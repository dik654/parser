"""
Batch processing utilities for handling multiple documents.
"""

import asyncio
import json
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from src.document import Document
from src.pipeline.pipeline import Pipeline, PipelineConfig, PipelineResult

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    # Parallelization
    parallel: bool = False
    max_workers: int = 4
    use_processes: bool = False  # Use processes instead of threads

    # Progress
    show_progress: bool = True
    progress_callback: Optional[Callable[[int, int, str], None]] = None

    # Output
    output_format: str = "json"  # json, jsonl
    output_dir: Optional[str] = None
    save_failed: bool = True

    # Filtering
    extensions: Optional[List[str]] = None
    recursive: bool = True
    glob_pattern: str = "*"


@dataclass
class BatchResult:
    """Result of batch processing."""

    total: int
    successful: int
    failed: int
    results: List[PipelineResult]
    failed_files: List[str] = field(default_factory=list)
    processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.successful / self.total

    def summary(self) -> str:
        """Generate summary string."""
        return (
            f"Processed {self.total} files: "
            f"{self.successful} successful, {self.failed} failed "
            f"({self.success_rate:.1%} success rate) "
            f"in {self.processing_time:.2f}s"
        )


class BatchProcessor:
    """
    Batch processor for handling multiple documents.

    Supports parallel processing, progress tracking, and various output formats.
    """

    def __init__(
        self,
        pipeline: Optional[Pipeline] = None,
        config: Optional[BatchConfig] = None,
    ):
        """
        Initialize batch processor.

        Args:
            pipeline: Pipeline to use for processing
            config: Batch processing configuration
        """
        self.pipeline = pipeline or Pipeline()
        self.config = config or BatchConfig()

    def process_directory(
        self,
        directory: Union[str, Path],
        **kwargs: Any,
    ) -> BatchResult:
        """
        Process all matching files in a directory.

        Args:
            directory: Directory path to process
            **kwargs: Additional options passed to pipeline

        Returns:
            BatchResult: Batch processing result
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Collect files
        files = list(self._collect_files(directory))

        return self.process_files(files, **kwargs)

    def process_files(
        self,
        files: List[Union[str, Path]],
        **kwargs: Any,
    ) -> BatchResult:
        """
        Process a list of files.

        Args:
            files: List of file paths
            **kwargs: Additional options passed to pipeline

        Returns:
            BatchResult: Batch processing result
        """
        import time

        start_time = time.time()
        files = [Path(f) for f in files]
        total = len(files)

        if total == 0:
            return BatchResult(
                total=0,
                successful=0,
                failed=0,
                results=[],
            )

        # Setup progress bar
        progress_iter = self._get_progress_iterator(files)

        # Process files
        if self.config.parallel and total > 1:
            results = self._process_parallel(progress_iter, **kwargs)
        else:
            results = self._process_sequential(progress_iter, **kwargs)

        processing_time = time.time() - start_time

        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        failed_files = [r.source_path for r in results if not r.success and r.source_path]

        # Save results if output directory specified
        if self.config.output_dir:
            self._save_results(results)

        return BatchResult(
            total=total,
            successful=successful,
            failed=failed,
            results=results,
            failed_files=failed_files,
            processing_time=processing_time,
        )

    def process_glob(
        self,
        pattern: str,
        base_dir: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> BatchResult:
        """
        Process files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.pdf")
            base_dir: Base directory for pattern (default: current dir)
            **kwargs: Additional options passed to pipeline

        Returns:
            BatchResult: Batch processing result
        """
        base_dir = Path(base_dir) if base_dir else Path.cwd()
        files = list(base_dir.glob(pattern))
        return self.process_files(files, **kwargs)

    def _collect_files(self, directory: Path) -> Iterator[Path]:
        """Collect files from directory based on config."""
        if self.config.recursive:
            pattern = f"**/{self.config.glob_pattern}"
        else:
            pattern = self.config.glob_pattern

        for path in directory.glob(pattern):
            if path.is_file():
                # Filter by extension if specified
                if self.config.extensions:
                    if path.suffix.lower().lstrip(".") in self.config.extensions:
                        yield path
                else:
                    yield path

    def _get_progress_iterator(self, files: List[Path]):
        """Get iterator with optional progress bar."""
        if self.config.show_progress:
            try:
                from tqdm import tqdm
                return tqdm(files, desc="Processing", unit="file")
            except ImportError:
                pass
        return files

    def _process_sequential(
        self,
        files: Iterator[Path],
        **kwargs: Any,
    ) -> List[PipelineResult]:
        """Process files sequentially."""
        results = []
        files_list = list(files)
        total = len(files_list)

        for idx, file_path in enumerate(files_list):
            if self.config.progress_callback:
                self.config.progress_callback(idx + 1, total, str(file_path))

            result = self.pipeline.process(file_path, **kwargs)
            results.append(result)

        return results

    def _process_parallel(
        self,
        files: Iterator[Path],
        **kwargs: Any,
    ) -> List[PipelineResult]:
        """Process files in parallel."""
        files_list = list(files)

        # Choose executor type
        if self.config.use_processes:
            executor_class = ProcessPoolExecutor
        else:
            executor_class = ThreadPoolExecutor

        results = []
        with executor_class(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._process_single, f, kwargs): f
                for f in files_list
            }

            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = futures[future]
                    results.append(PipelineResult(
                        document=None,
                        success=False,
                        error=str(e),
                        source_path=str(file_path),
                    ))

        return results

    def _process_single(
        self,
        file_path: Path,
        kwargs: Dict[str, Any],
    ) -> PipelineResult:
        """Process a single file (for parallel execution)."""
        return self.pipeline.process(file_path, **kwargs)

    def _save_results(self, results: List[PipelineResult]) -> None:
        """Save processing results to output directory."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.config.output_format == "jsonl":
            self._save_jsonl(results, output_dir)
        else:
            self._save_json(results, output_dir)

    def _save_json(self, results: List[PipelineResult], output_dir: Path) -> None:
        """Save results as individual JSON files."""
        for result in results:
            if result.success and result.document:
                doc = result.document
                output_path = output_dir / f"{doc.id}.json"
                doc.save_json(output_path)
            elif self.config.save_failed and result.source_path:
                # Save error info for failed files
                error_path = output_dir / f"error_{Path(result.source_path).stem}.json"
                error_data = {
                    "source": result.source_path,
                    "error": result.error,
                    "processing_time": result.processing_time,
                }
                error_path.write_text(json.dumps(error_data, indent=2))

    def _save_jsonl(self, results: List[PipelineResult], output_dir: Path) -> None:
        """Save results as JSONL file."""
        output_path = output_dir / "results.jsonl"

        with output_path.open("w") as f:
            for result in results:
                if result.success and result.document:
                    line = result.document.to_json(indent=None)
                    f.write(line + "\n")
                elif self.config.save_failed and result.source_path:
                    error_data = {
                        "source": result.source_path,
                        "error": result.error,
                        "success": False,
                    }
                    f.write(json.dumps(error_data) + "\n")


async def process_async(
    pipeline: Pipeline,
    files: List[Union[str, Path]],
    max_concurrent: int = 10,
    **kwargs: Any,
) -> List[PipelineResult]:
    """
    Process files asynchronously.

    Args:
        pipeline: Pipeline to use
        files: List of file paths
        max_concurrent: Maximum concurrent tasks
        **kwargs: Additional options

    Returns:
        List[PipelineResult]: Processing results
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(file_path: Union[str, Path]) -> PipelineResult:
        async with semaphore:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: pipeline.process(file_path, **kwargs)
            )

    tasks = [process_one(f) for f in files]
    return await asyncio.gather(*tasks)
