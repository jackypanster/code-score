"""Temporary directory management and cleanup for metrics collection."""

import logging
import os
import shutil
import tempfile
from pathlib import Path


class RepositoryCleanup:
    """Manages cleanup of temporary files and directories."""

    def __init__(self):
        """Initialize cleanup manager."""
        self.cleanup_paths: list[Path] = []
        self.logger = logging.getLogger('code_score.cleanup')

    def register_for_cleanup(self, path: Path) -> None:
        """Register a path for cleanup."""
        if path not in self.cleanup_paths:
            self.cleanup_paths.append(path)
            self.logger.debug(f"Registered for cleanup: {path}")

    def cleanup_temporary_files(self) -> None:
        """Clean up all registered temporary files and directories."""
        errors = []

        for path in self.cleanup_paths:
            try:
                self.cleanup_path(path)
            except Exception as e:
                error_msg = f"Failed to cleanup {path}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)

        # Clear the cleanup list
        self.cleanup_paths.clear()

        if errors:
            self.logger.warning(f"Cleanup completed with {len(errors)} error(s)")
        else:
            self.logger.debug("Cleanup completed successfully")

    def cleanup_path(self, path: Path) -> None:
        """Clean up a specific path."""
        if not path.exists():
            self.logger.debug(f"Path already cleaned up: {path}")
            return

        try:
            if path.is_file():
                path.unlink()
                self.logger.debug(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                self.logger.debug(f"Removed directory: {path}")
        except PermissionError as e:
            self.logger.warning(f"Permission denied cleaning up {path}: {e}")
            # Try to change permissions and retry
            try:
                if path.is_dir():
                    for root, dirs, files in os.walk(path):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0o755)
                        for f in files:
                            os.chmod(os.path.join(root, f), 0o644)
                    shutil.rmtree(path)
                else:
                    os.chmod(path, 0o644)
                    path.unlink()
                self.logger.debug(f"Removed after permission fix: {path}")
            except Exception as retry_error:
                raise Exception(f"Failed to cleanup after permission fix: {retry_error}")
        except Exception as e:
            raise Exception(f"Unexpected cleanup error: {e}")

    def cleanup_cloned_repository(self, repository_path: str | None) -> None:
        """Clean up a cloned repository directory."""
        if not repository_path:
            return

        repo_path = Path(repository_path)

        # Get the parent temp directory (should be one level up)
        if repo_path.name == "repo" and repo_path.parent.name.startswith("code-score-"):
            temp_dir = repo_path.parent
            self.cleanup_path(temp_dir)
        else:
            # Clean up the repository directory itself
            self.cleanup_path(repo_path)

    def create_temp_directory(self, prefix: str = "code-score-") -> Path:
        """Create a temporary directory and register it for cleanup."""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.register_for_cleanup(temp_dir)
        self.logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir

    def get_cleanup_status(self) -> dict:
        """Get status of cleanup operations."""
        return {
            "registered_paths": len(self.cleanup_paths),
            "paths": [str(p) for p in self.cleanup_paths]
        }

    def force_cleanup_all(self) -> None:
        """Force cleanup of all known temporary directories."""
        # Look for any remaining code-score temporary directories
        temp_root = Path(tempfile.gettempdir())

        try:
            for item in temp_root.iterdir():
                if item.is_dir() and item.name.startswith("code-score-"):
                    try:
                        self.cleanup_path(item)
                        self.logger.info(f"Force cleaned orphaned temp dir: {item}")
                    except Exception as e:
                        self.logger.warning(f"Failed to force cleanup {item}: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to scan for orphaned temp dirs: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup_temporary_files()


# Global cleanup instance for module-level operations
_global_cleanup = RepositoryCleanup()


def get_cleanup_manager() -> RepositoryCleanup:
    """Get the global cleanup manager instance."""
    return _global_cleanup


def register_for_cleanup(path: Path) -> None:
    """Register a path for cleanup using the global manager."""
    _global_cleanup.register_for_cleanup(path)


def cleanup_all() -> None:
    """Clean up all registered paths using the global manager."""
    _global_cleanup.cleanup_temporary_files()


def create_temp_directory(prefix: str = "code-score-") -> Path:
    """Create a temporary directory using the global manager."""
    return _global_cleanup.create_temp_directory(prefix)
