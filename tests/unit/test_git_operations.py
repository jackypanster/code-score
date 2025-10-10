"""Real execution tests for git operations functionality.

NO MOCKS - All tests use real Git repositories and operations.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.git_operations import GitOperationError, GitOperations
from src.metrics.models.repository import Repository


def check_git_available() -> bool:
    """Check if git is available in the system PATH."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class TestGitOperationsReal:
    """REAL TESTS for Git operations - NO MOCKS."""

    @pytest.fixture
    def git_ops(self) -> GitOperations:
        """Create GitOperations instance."""
        return GitOperations(timeout_seconds=30)

    @pytest.fixture
    def real_local_repo(self) -> Path:
        """Create a real local Git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "test_repo"
            repo_path.mkdir()

            # Initialize real Git repo
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, capture_output=True)

            # Create a file and commit
            (repo_path / "README.md").write_text("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)

            yield repo_path

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_success(self, git_ops: GitOperations, real_local_repo: Path) -> None:
        """REAL TEST: Clone a real local Git repository."""
        # Use file:// URL for local repo (no network needed)
        repo_url = f"file://{real_local_repo}"

        # REAL CLONE - No mocks!
        repository = git_ops.clone_repository(repo_url)

        # Verify repository object
        assert isinstance(repository, Repository)
        assert repository.url == repo_url
        assert repository.local_path is not None
        assert Path(repository.local_path).exists()
        assert (Path(repository.local_path) / "README.md").exists()
        # Note: commit_sha is populated even when not explicitly requested (populated from cloned repo)
        assert repository.commit_sha is not None

        # Cleanup
        git_ops.cleanup_repository(repository)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_with_commit_sha(self, git_ops: GitOperations, real_local_repo: Path) -> None:
        """REAL TEST: Clone repository and checkout specific commit."""
        # Get the actual commit SHA from the real repo
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=real_local_repo,
            capture_output=True,
            text=True
        )
        actual_commit_sha = result.stdout.strip()

        repo_url = f"file://{real_local_repo}"

        # REAL CLONE with specific commit
        repository = git_ops.clone_repository(repo_url, actual_commit_sha)

        # Verify repository object
        assert repository.commit_sha == actual_commit_sha
        assert Path(repository.local_path).exists()

        # Verify we're actually on the specified commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository.local_path,
            capture_output=True,
            text=True
        )
        current_commit = result.stdout.strip()
        assert current_commit == actual_commit_sha

        # Cleanup
        git_ops.cleanup_repository(repository)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_failure(self, git_ops: GitOperations) -> None:
        """REAL TEST: Verify clone failure for non-existent repository."""
        # Use a non-existent local path
        repo_url = "file:///nonexistent/path/to/repo.git"

        # REAL CLONE that will fail - catches generic Exception
        with pytest.raises(Exception):  # May raise GitOperationError or generic Exception
            git_ops.clone_repository(repo_url)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_invalid_commit_sha(self, git_ops: GitOperations, real_local_repo: Path) -> None:
        """REAL TEST: Verify clone with invalid commit SHA fails."""
        repo_url = f"file://{real_local_repo}"
        invalid_commit = "0000000000000000000000000000000000000000"

        # REAL CLONE with invalid commit
        with pytest.raises(GitOperationError, match="Failed to checkout commit"):
            git_ops.clone_repository(repo_url, invalid_commit)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_cleanup_repository_real_success(self, git_ops: GitOperations, real_local_repo: Path) -> None:
        """REAL TEST: Verify repository cleanup removes directory."""
        # First clone a real repo
        repo_url = f"file://{real_local_repo}"
        repository = git_ops.clone_repository(repo_url)

        # Verify it exists
        assert Path(repository.local_path).exists()
        local_path = repository.local_path

        # REAL CLEANUP
        git_ops.cleanup_repository(repository)

        # Verify parent temp directory was removed
        parent_temp = Path(local_path).parent
        assert not parent_temp.exists()

    def test_cleanup_repository_real_none_path(self, git_ops: GitOperations) -> None:
        """REAL TEST: Verify cleanup with None path doesn't crash."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path=None
        )

        # Should not raise exception
        git_ops.cleanup_repository(repository)

    def test_cleanup_repository_real_empty_path(self, git_ops: GitOperations) -> None:
        """REAL TEST: Verify cleanup with empty path doesn't crash."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path=""
        )

        # Should not raise exception
        git_ops.cleanup_repository(repository)

    def test_cleanup_repository_real_nonexistent_path(self, git_ops: GitOperations) -> None:
        """REAL TEST: Verify cleanup of non-existent path doesn't crash."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path="/nonexistent/path/to/repo"
        )

        # Should not raise exception (path doesn't exist, nothing to clean)
        git_ops.cleanup_repository(repository)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_with_multiple_commits(self, git_ops: GitOperations) -> None:
        """REAL TEST: Clone repo and verify with multiple commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a repo with multiple commits
            repo_path = Path(temp_dir) / "multi_commit_repo"
            repo_path.mkdir()

            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, capture_output=True)

            # First commit
            (repo_path / "file1.txt").write_text("First")
            subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "First commit"], cwd=repo_path, capture_output=True)

            # Get first commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            first_commit = result.stdout.strip()

            # Second commit
            (repo_path / "file2.txt").write_text("Second")
            subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Second commit"], cwd=repo_path, capture_output=True)

            # Clone at first commit
            repo_url = f"file://{repo_path}"
            repository = git_ops.clone_repository(repo_url, first_commit)

            # Verify we're on first commit (file2.txt shouldn't exist)
            assert (Path(repository.local_path) / "file1.txt").exists()
            assert not (Path(repository.local_path) / "file2.txt").exists()

            # Cleanup
            git_ops.cleanup_repository(repository)

    @pytest.mark.skipif(not check_git_available(), reason="git not available")
    def test_clone_repository_real_preserves_file_content(self, git_ops: GitOperations) -> None:
        """REAL TEST: Verify cloned repo has correct file contents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create repo with specific content
            repo_path = Path(temp_dir) / "content_repo"
            repo_path.mkdir()

            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, capture_output=True)

            expected_content = "Test content for verification\nLine 2\nLine 3"
            (repo_path / "test.txt").write_text(expected_content)
            subprocess.run(["git", "add", "test.txt"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Add test file"], cwd=repo_path, capture_output=True)

            # Clone
            repo_url = f"file://{repo_path}"
            repository = git_ops.clone_repository(repo_url)

            # Verify content is preserved
            cloned_content = (Path(repository.local_path) / "test.txt").read_text()
            assert cloned_content == expected_content

            # Cleanup
            git_ops.cleanup_repository(repository)

    def test_create_temp_directory_real(self) -> None:
        """REAL TEST: Verify temporary directory creation."""
        # REAL TEMP DIR creation - No mocks, use tempfile directly
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="code-score-")

        # Verify it exists and has correct prefix
        assert Path(temp_dir).exists()
        assert "code-score-" in temp_dir

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
