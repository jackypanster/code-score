"""Error handling and logging for metrics collection pipeline."""

import logging
import sys
from typing import List, Dict, Any
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricsError(Exception):
    """Base exception for metrics collection errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.context = context or {}


class RepositoryError(MetricsError):
    """Repository-related errors."""
    pass


class ToolExecutionError(MetricsError):
    """Tool execution errors."""
    pass


class OutputGenerationError(MetricsError):
    """Output generation errors."""
    pass


class ErrorHandler:
    """Handles errors and logging throughout the metrics collection pipeline."""

    def __init__(self, verbose: bool = False):
        """Initialize error handler with logging configuration."""
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Configure logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = logging.DEBUG if self.verbose else logging.INFO

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Setup stderr handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        # Configure logger
        logger = logging.getLogger('code_score')
        logger.setLevel(log_level)
        logger.addHandler(handler)

        # Prevent duplicate logs
        logger.propagate = False

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle an error with appropriate logging and tracking."""
        logger = logging.getLogger('code_score')

        if isinstance(error, MetricsError):
            severity = error.severity
            message = error.message
            error_context = error.context
        else:
            severity = ErrorSeverity.ERROR
            message = str(error)
            error_context = {}

        # Create full error message
        full_message = f"{context}: {message}" if context else message

        # Log error
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(full_message)
            self.errors.append(full_message)
        elif severity == ErrorSeverity.ERROR:
            logger.error(full_message)
            self.errors.append(full_message)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(full_message)
            self.warnings.append(full_message)
        else:
            logger.info(full_message)

        # Log context if available and verbose
        if error_context and self.verbose:
            logger.debug(f"Error context: {error_context}")

    def handle_tool_failure(self, tool_name: str, error: Exception) -> None:
        """Handle tool execution failure with graceful degradation."""
        warning_msg = f"Tool '{tool_name}' failed: {str(error)}"

        tool_error = ToolExecutionError(
            message=warning_msg,
            severity=ErrorSeverity.WARNING,
            context={"tool": tool_name, "error_type": type(error).__name__}
        )

        self.handle_error(tool_error, "Tool execution")

    def handle_repository_failure(self, repo_url: str, error: Exception) -> None:
        """Handle repository operation failure (critical)."""
        error_msg = f"Repository operation failed for '{repo_url}': {str(error)}"

        repo_error = RepositoryError(
            message=error_msg,
            severity=ErrorSeverity.CRITICAL,
            context={"repository_url": repo_url, "error_type": type(error).__name__}
        )

        self.handle_error(repo_error, "Repository operation")

    def handle_output_failure(self, output_path: str, error: Exception) -> None:
        """Handle output generation failure (critical)."""
        error_msg = f"Output generation failed for '{output_path}': {str(error)}"

        output_error = OutputGenerationError(
            message=error_msg,
            severity=ErrorSeverity.CRITICAL,
            context={"output_path": output_path, "error_type": type(error).__name__}
        )

        self.handle_error(output_error, "Output generation")

    def has_critical_errors(self) -> bool:
        """Check if any critical errors occurred."""
        return len(self.errors) > 0

    def get_errors(self) -> List[str]:
        """Get list of all errors."""
        return self.errors.copy()

    def get_warnings(self) -> List[str]:
        """Get list of all warnings."""
        return self.warnings.copy()

    def clear(self) -> None:
        """Clear all stored errors and warnings."""
        self.errors.clear()
        self.warnings.clear()

    def should_continue(self) -> bool:
        """Determine if execution should continue based on error state."""
        # Following constitutional KISS principle: fail fast on critical errors
        return not self.has_critical_errors()

    def log_summary(self) -> None:
        """Log a summary of errors and warnings."""
        logger = logging.getLogger('code_score')

        if self.errors:
            logger.error(f"Execution completed with {len(self.errors)} error(s)")
            if self.verbose:
                for error in self.errors:
                    logger.error(f"  - {error}")

        if self.warnings:
            logger.warning(f"Execution completed with {len(self.warnings)} warning(s)")
            if self.verbose:
                for warning in self.warnings:
                    logger.warning(f"  - {warning}")

        if not self.errors and not self.warnings:
            logger.info("Execution completed successfully with no errors or warnings")


def get_error_handler(verbose: bool = False) -> ErrorHandler:
    """Get a configured error handler instance."""
    return ErrorHandler(verbose=verbose)