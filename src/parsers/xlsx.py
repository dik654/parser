"""
XLSX document parser using openpyxl and pandas.
"""

import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from src.document import Document, DocumentMetadata, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import register_parser


@register_parser("xlsx", extensions=["xlsx", "xls"])
class XLSXParser(BaseParser):
    """
    Parser for Microsoft Excel spreadsheets (.xlsx).

    Uses openpyxl for extraction and optionally pandas for data processing.
    """

    def __init__(
        self,
        extract_all_sheets: bool = True,
        sheet_names: Optional[List[str]] = None,
        include_formulas: bool = False,
        preserve_table_structure: bool = True,
        max_rows: Optional[int] = None,
        max_cols: Optional[int] = None,
    ):
        """
        Initialize XLSX parser.

        Args:
            extract_all_sheets: Whether to extract all sheets
            sheet_names: Specific sheet names to extract (if not all)
            include_formulas: Whether to include formulas (vs values only)
            preserve_table_structure: Whether to preserve table structure in text
            max_rows: Maximum rows to extract per sheet
            max_cols: Maximum columns to extract per sheet
        """
        self.extract_all_sheets = extract_all_sheets
        self.sheet_names = sheet_names
        self.include_formulas = include_formulas
        self.preserve_table_structure = preserve_table_structure
        self.max_rows = max_rows
        self.max_cols = max_cols

    @property
    def supported_extensions(self) -> List[str]:
        return [".xlsx", ".XLSX", ".xls", ".XLS"]

    def supports(self, source: Union[str, Path]) -> bool:
        return self._get_extension(source) in [".xlsx", ".xls"]

    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs: Any,
    ) -> Document:
        """
        Parse an XLSX document.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Additional options

        Returns:
            Document: Parsed document object
        """
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise ImportError(
                "openpyxl is required. Install with: pip install openpyxl"
            )

        import io

        # Load workbook
        if isinstance(source, bytes):
            wb = load_workbook(io.BytesIO(source), data_only=not self.include_formulas)
        elif isinstance(source, (str, Path)):
            wb = load_workbook(str(source), data_only=not self.include_formulas)
        else:
            wb = load_workbook(source, data_only=not self.include_formulas)

        # Determine sheets to process
        if self.sheet_names:
            sheets_to_process = [
                name for name in self.sheet_names if name in wb.sheetnames
            ]
        elif self.extract_all_sheets:
            sheets_to_process = wb.sheetnames
        else:
            sheets_to_process = [wb.active.title] if wb.active else []

        text_parts: List[str] = []
        tables: List[Dict[str, Any]] = []

        for sheet_name in sheets_to_process:
            sheet = wb[sheet_name]
            sheet_text, sheet_tables = self._process_sheet(sheet)

            text_parts.append(f"[Sheet: {sheet_name}]\n{sheet_text}")
            tables.extend(sheet_tables)

        content = "\n\n".join(text_parts)

        # Extract metadata
        props = wb.properties
        metadata = DocumentMetadata(
            title=props.title if props else None,
            author=props.creator if props else None,
            created_at=props.created if props else None,
            modified_at=props.modified if props else None,
            word_count=len(content.split()),
            char_count=len(content),
            source_path=str(source) if isinstance(source, (str, Path)) else None,
            custom={
                "sheet_count": len(wb.sheetnames),
                "sheet_names": wb.sheetnames,
                "subject": props.subject if props else None,
                "keywords": props.keywords if props else None,
            },
        )

        wb.close()

        return Document(
            id=str(uuid.uuid4()),
            content=content,
            doc_type=DocumentType.XLSX,
            metadata=metadata,
            tables=tables,
        )

    def _process_sheet(self, sheet) -> tuple:
        """Process a single worksheet."""
        text_lines: List[str] = []
        table_data: List[List[str]] = []

        max_row = min(sheet.max_row or 0, self.max_rows or float("inf"))
        max_col = min(sheet.max_column or 0, self.max_cols or float("inf"))

        for row_idx, row in enumerate(sheet.iter_rows(max_row=int(max_row)), 1):
            row_values: List[str] = []

            for col_idx, cell in enumerate(row):
                if col_idx >= max_col:
                    break

                value = cell.value
                if value is None:
                    value = ""
                else:
                    value = str(value)
                row_values.append(value)

            if any(v.strip() for v in row_values):
                table_data.append(row_values)

                if self.preserve_table_structure:
                    text_lines.append(" | ".join(row_values))
                else:
                    text_lines.append(" ".join(v for v in row_values if v.strip()))

        tables = []
        if table_data:
            tables.append({
                "sheet": sheet.title,
                "data": table_data,
                "row_count": len(table_data),
                "col_count": len(table_data[0]) if table_data else 0,
            })

        return "\n".join(text_lines), tables

    def to_dataframe(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        sheet_name: Optional[str] = None,
    ):
        """
        Parse XLSX to pandas DataFrame.

        Args:
            source: File path, file object, or raw bytes
            sheet_name: Specific sheet to read (reads first if None)

        Returns:
            pandas.DataFrame or dict of DataFrames
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")

        import io

        if isinstance(source, bytes):
            source = io.BytesIO(source)

        return pd.read_excel(
            source,
            sheet_name=sheet_name,
            engine="openpyxl",
        )
