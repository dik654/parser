"""
File utilities for document processing.
"""

import mimetypes
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Iterator, List, Optional, Tuple, Union

from src.document import DocumentType


def detect_file_type(
    source: Union[str, Path, bytes, BinaryIO],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect file type using magic bytes and extension.

    Args:
        source: File path, raw bytes, or file object

    Returns:
        Tuple of (mime_type, extension)
    """
    # Try python-magic first
    try:
        import magic

        if isinstance(source, bytes):
            mime = magic.from_buffer(source, mime=True)
        elif isinstance(source, (str, Path)):
            mime = magic.from_file(str(source), mime=True)
        else:
            # BinaryIO
            pos = source.tell()
            data = source.read(2048)
            source.seek(pos)
            mime = magic.from_buffer(data, mime=True)

        ext = mimetypes.guess_extension(mime)
        return mime, ext

    except ImportError:
        pass

    # Fallback to extension-based detection
    if isinstance(source, (str, Path)):
        path = Path(source)
        ext = path.suffix.lower()
        mime, _ = mimetypes.guess_type(str(path))
        return mime, ext

    return None, None


def detect_encoding(
    source: Union[str, Path, bytes, BinaryIO],
    sample_size: int = 65536,
) -> Optional[str]:
    """
    Detect text encoding.

    Args:
        source: File path, raw bytes, or file object
        sample_size: Number of bytes to sample for detection

    Returns:
        Detected encoding name
    """
    try:
        import chardet
    except ImportError:
        return "utf-8"  # Default fallback

    # Get sample bytes
    if isinstance(source, bytes):
        sample = source[:sample_size]
    elif isinstance(source, (str, Path)):
        with open(source, "rb") as f:
            sample = f.read(sample_size)
    else:
        pos = source.tell()
        sample = source.read(sample_size)
        source.seek(pos)

    result = chardet.detect(sample)
    return result.get("encoding", "utf-8")


def get_document_type(source: Union[str, Path]) -> DocumentType:
    """
    Get document type from file path.

    Args:
        source: File path

    Returns:
        DocumentType enum value
    """
    path = Path(source)
    ext = path.suffix.lower().lstrip(".")
    return DocumentType.from_extension(ext)


def is_supported_file(
    source: Union[str, Path],
    supported_types: Optional[List[str]] = None,
) -> bool:
    """
    Check if file type is supported.

    Args:
        source: File path
        supported_types: List of supported extensions (without dot)

    Returns:
        True if supported
    """
    path = Path(source)
    ext = path.suffix.lower().lstrip(".")

    if supported_types:
        return ext in supported_types

    # Default supported types
    default_types = ["pdf", "docx", "pptx", "xlsx", "html", "htm", "md", "hwpx", "hwp",
                     "png", "jpg", "jpeg", "gif", "bmp", "tiff", "txt"]
    return ext in default_types


class TempFileManager:
    """Manager for temporary files and directories."""

    def __init__(self, prefix: str = "docparser_"):
        """
        Initialize temp file manager.

        Args:
            prefix: Prefix for temp files/directories
        """
        self.prefix = prefix
        self._temp_files: List[Path] = []
        self._temp_dirs: List[Path] = []

    def create_temp_file(
        self,
        suffix: str = "",
        content: Optional[bytes] = None,
    ) -> Path:
        """
        Create a temporary file.

        Args:
            suffix: File extension (e.g., ".pdf")
            content: Optional content to write

        Returns:
            Path to temp file
        """
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=self.prefix)
        path = Path(path)

        if content:
            path.write_bytes(content)

        os.close(fd)
        self._temp_files.append(path)
        return path

    def create_temp_dir(self) -> Path:
        """
        Create a temporary directory.

        Returns:
            Path to temp directory
        """
        path = Path(tempfile.mkdtemp(prefix=self.prefix))
        self._temp_dirs.append(path)
        return path

    def cleanup(self) -> None:
        """Clean up all temporary files and directories."""
        for path in self._temp_files:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass

        for path in self._temp_dirs:
            try:
                if path.exists():
                    shutil.rmtree(path)
            except Exception:
                pass

        self._temp_files.clear()
        self._temp_dirs.clear()

    def __enter__(self) -> "TempFileManager":
        return self

    def __exit__(self, *args) -> None:
        self.cleanup()


def extract_archive(
    archive_path: Union[str, Path],
    extract_to: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """
    Extract files from archive.

    Args:
        archive_path: Path to archive file
        extract_to: Extraction directory (temp if None)

    Returns:
        List of extracted file paths
    """
    archive_path = Path(archive_path)
    suffix = archive_path.suffix.lower()

    if extract_to:
        extract_dir = Path(extract_to)
        extract_dir.mkdir(parents=True, exist_ok=True)
    else:
        extract_dir = Path(tempfile.mkdtemp(prefix="docparser_extract_"))

    extracted_files = []

    if suffix == ".zip" or suffix == ".hwpx":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
            for name in zf.namelist():
                path = extract_dir / name
                if path.is_file():
                    extracted_files.append(path)

    elif suffix in [".tar", ".gz", ".tgz", ".bz2"]:
        import tarfile

        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(extract_dir)
            for member in tf.getmembers():
                if member.isfile():
                    extracted_files.append(extract_dir / member.name)

    return extracted_files


def iter_directory(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
) -> Iterator[Path]:
    """
    Iterate over files in directory.

    Args:
        directory: Directory path
        pattern: Glob pattern
        recursive: Whether to search recursively
        extensions: Filter by extensions (without dot)

    Yields:
        File paths
    """
    directory = Path(directory)

    if recursive:
        glob_pattern = f"**/{pattern}"
    else:
        glob_pattern = pattern

    for path in directory.glob(glob_pattern):
        if path.is_file():
            if extensions:
                ext = path.suffix.lower().lstrip(".")
                if ext in extensions:
                    yield path
            else:
                yield path


def get_file_size(source: Union[str, Path]) -> int:
    """Get file size in bytes."""
    return Path(source).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Format file size as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
