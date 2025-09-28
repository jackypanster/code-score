"""Git operations for repository cloning and management."""

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .models.repository import Repository


class GitOperationError(Exception):
    """Base exception for git operations."""
    pass


class InvalidRepositoryError(GitOperationError):
    """Repository URL is invalid or inaccessible."""
    pass


class NetworkTimeoutError(GitOperationError):
    """Network operation timed out."""
    pass


class GitOperations:
    """Handles Git repository operations using command-line git."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize git operations with timeout."""
        self.timeout_seconds = timeout_seconds

    def clone_repository(self, url: str, commit_sha: str | None = None) -> Repository:
        """Clone repository to temporary directory and optionally checkout specific commit."""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="code-score-")
            local_path = str(Path(temp_dir) / "repo")

            # Clone repository
            clone_cmd = ["git", "clone", "--depth", "1", url, local_path]
            if commit_sha:
                # For specific commit, we need full clone
                clone_cmd = ["git", "clone", url, local_path]

            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            if result.returncode != 0:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if "fatal: repository" in result.stderr.lower():
                    raise InvalidRepositoryError(f"Invalid repository URL: {url}")
                else:
                    raise GitOperationError(f"Git clone failed: {result.stderr}")

            # Checkout specific commit if provided
            if commit_sha:
                self.checkout_commit(local_path, commit_sha)

            # Get actual commit SHA
            actual_commit = self._get_current_commit(local_path)

            # Calculate repository size
            size_mb = self._calculate_repo_size(local_path)

            # Create repository object
            repository = Repository(
                url=url,
                commit_sha=actual_commit,
                local_path=local_path,
                clone_timestamp=datetime.utcnow(),
                size_mb=size_mb
            )

            return repository

        except subprocess.TimeoutExpired:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise NetworkTimeoutError(f"Git clone timed out after {self.timeout_seconds} seconds")

        except Exception as e:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if isinstance(e, (GitOperationError, InvalidRepositoryError, NetworkTimeoutError)):
                raise
            raise GitOperationError(f"Unexpected error during clone: {str(e)}")

    def checkout_commit(self, local_path: str, commit_sha: str) -> None:
        """Checkout specific commit in cloned repository."""
        try:
            result = subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise GitOperationError(f"Failed to checkout commit {commit_sha}: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise GitOperationError(f"Checkout timed out for commit {commit_sha}")

    def get_repository_info(self, local_path: str) -> dict[str, Any]:
        """Get repository information from local clone."""
        try:
            # Get current commit SHA
            commit_sha = self._get_current_commit(local_path)

            # Get repository URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            url = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get commit timestamp
            result = subprocess.run(
                ["git", "show", "-s", "--format=%ci", commit_sha],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            commit_timestamp = result.stdout.strip() if result.returncode == 0 else None

            return {
                "commit_sha": commit_sha,
                "url": url,
                "commit_timestamp": commit_timestamp,
                "local_path": local_path
            }

        except Exception as e:
            raise GitOperationError(f"Failed to get repository info: {str(e)}")

    def cleanup_repository(self, repository: Repository) -> None:
        """Clean up cloned repository and temporary files."""
        if repository.local_path and Path(repository.local_path).exists():
            # Get parent temp directory
            temp_dir = Path(repository.local_path).parent
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                # Log warning but don't fail - cleanup is best effort
                pass

    def _get_current_commit(self, local_path: str) -> str:
        """Get current commit SHA from repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise GitOperationError("Failed to get current commit SHA")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise GitOperationError("Timeout getting current commit SHA")

    def _calculate_repo_size(self, local_path: str) -> float:
        """Calculate repository size in megabytes."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(local_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        # Skip files that can't be accessed
                        continue

            return round(total_size / (1024 * 1024), 1)  # Convert to MB

        except Exception:
            return 0.0  # Return 0 if size calculation fails
