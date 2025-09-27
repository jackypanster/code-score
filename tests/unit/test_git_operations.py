"""Unit tests for git operations functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import subprocess

from src.metrics.git_operations import GitOperations, GitOperationError
from src.metrics.models.repository import Repository


class TestGitOperations:
    """Test git operations functionality."""

    @pytest.fixture
    def git_ops(self) -> GitOperations:
        """Create GitOperations instance."""
        return GitOperations(timeout_seconds=30)

    @pytest.fixture
    def mock_successful_clone(self) -> MagicMock:
        """Mock successful git clone."""
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = ""
        mock.stderr = ""
        return mock

    @pytest.fixture
    def mock_failed_clone(self) -> MagicMock:
        """Mock failed git clone."""
        mock = MagicMock()
        mock.returncode = 128
        mock.stdout = ""
        mock.stderr = "fatal: repository not found"
        return mock

    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_run: MagicMock, mock_mkdtemp: MagicMock, git_ops: GitOperations, mock_successful_clone: MagicMock) -> None:
        """Test successful repository cloning."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"
        mock_run.return_value = mock_successful_clone

        repo_url = "https://github.com/test/repo.git"
        repository = git_ops.clone_repository(repo_url)

        # Verify repository object
        assert isinstance(repository, Repository)
        assert repository.url == repo_url
        assert repository.local_path == "/tmp/code-score-12345/repo"
        assert repository.commit_sha is None  # No specific commit requested

        # Verify git clone was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "clone" in args
        assert repo_url in args

    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_clone_repository_with_commit_sha(self, mock_run: MagicMock, mock_mkdtemp: MagicMock, git_ops: GitOperations, mock_successful_clone: MagicMock) -> None:
        """Test repository cloning with specific commit SHA."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"
        mock_run.return_value = mock_successful_clone

        repo_url = "https://github.com/test/repo.git"
        commit_sha = "a1b2c3d4e5f6789012345678901234567890abcd"

        repository = git_ops.clone_repository(repo_url, commit_sha)

        # Verify repository object
        assert repository.commit_sha == commit_sha

        # Verify git commands were called (clone + checkout)
        assert mock_run.call_count == 2

        # First call should be clone
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "git" in first_call_args
        assert "clone" in first_call_args

        # Second call should be checkout
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "git" in second_call_args
        assert "checkout" in second_call_args
        assert commit_sha in second_call_args

    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_run: MagicMock, mock_mkdtemp: MagicMock, git_ops: GitOperations, mock_failed_clone: MagicMock) -> None:
        """Test repository cloning failure."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"
        mock_run.return_value = mock_failed_clone

        repo_url = "https://github.com/nonexistent/repo.git"

        with pytest.raises(GitOperationError, match="Failed to clone repository"):
            git_ops.clone_repository(repo_url)

    @patch('subprocess.run')
    def test_clone_repository_timeout(self, mock_run: MagicMock, git_ops: GitOperations) -> None:
        """Test repository cloning timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

        repo_url = "https://github.com/test/repo.git"

        with pytest.raises(GitOperationError, match="Git operation timed out"):
            git_ops.clone_repository(repo_url)

    @patch('subprocess.run')
    def test_clone_repository_command_not_found(self, mock_run: MagicMock, git_ops: GitOperations) -> None:
        """Test repository cloning when git command is not found."""
        mock_run.side_effect = FileNotFoundError("git: command not found")

        repo_url = "https://github.com/test/repo.git"

        with pytest.raises(GitOperationError, match="Git command not found"):
            git_ops.clone_repository(repo_url)

    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_clone_repository_invalid_commit_sha(self, mock_run: MagicMock, mock_mkdtemp: MagicMock, git_ops: GitOperations) -> None:
        """Test repository cloning with invalid commit SHA."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"

        # First call (clone) succeeds, second call (checkout) fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # Successful clone
            MagicMock(returncode=1, stdout="", stderr="fatal: reference is not a tree")  # Failed checkout
        ]

        repo_url = "https://github.com/test/repo.git"
        invalid_commit = "invalid123"

        with pytest.raises(GitOperationError, match="Failed to checkout commit"):
            git_ops.clone_repository(repo_url, invalid_commit)

    @patch('shutil.rmtree')
    def test_cleanup_repository_success(self, mock_rmtree: MagicMock, git_ops: GitOperations) -> None:
        """Test successful repository cleanup."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path="/tmp/code-score-12345/repo"
        )

        git_ops.cleanup_repository(repository)

        # Should call rmtree on the parent temp directory
        mock_rmtree.assert_called_once_with("/tmp/code-score-12345")

    @patch('shutil.rmtree')
    def test_cleanup_repository_permission_error(self, mock_rmtree: MagicMock, git_ops: GitOperations) -> None:
        """Test repository cleanup with permission error."""
        mock_rmtree.side_effect = PermissionError("Permission denied")

        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path="/tmp/code-score-12345/repo"
        )

        # Should not raise exception, just log warning
        git_ops.cleanup_repository(repository)

    def test_cleanup_repository_none_path(self, git_ops: GitOperations) -> None:
        """Test repository cleanup with None local_path."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path=None
        )

        # Should not raise exception
        git_ops.cleanup_repository(repository)

    def test_cleanup_repository_empty_path(self, git_ops: GitOperations) -> None:
        """Test repository cleanup with empty local_path."""
        repository = Repository(
            url="https://github.com/test/repo.git",
            local_path=""
        )

        # Should not raise exception
        git_ops.cleanup_repository(repository)

    @patch('tempfile.mkdtemp')
    def test_create_temp_directory(self, mock_mkdtemp: MagicMock, git_ops: GitOperations) -> None:
        """Test temporary directory creation."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"

        temp_dir = git_ops.create_temp_directory()

        assert temp_dir == "/tmp/code-score-12345"
        mock_mkdtemp.assert_called_once_with(prefix="code-score-")

    @patch('tempfile.mkdtemp')
    def test_create_temp_directory_custom_prefix(self, mock_mkdtemp: MagicMock, git_ops: GitOperations) -> None:
        """Test temporary directory creation with custom prefix."""
        mock_mkdtemp.return_value = "/tmp/custom-12345"

        temp_dir = git_ops.create_temp_directory(prefix="custom-")

        assert temp_dir == "/tmp/custom-12345"
        mock_mkdtemp.assert_called_once_with(prefix="custom-")

    def test_validate_commit_sha_valid(self, git_ops: GitOperations) -> None:
        """Test validation of valid commit SHA."""
        valid_shas = [
            "a1b2c3d4e5f6789012345678901234567890abcd",
            "1234567890abcdef1234567890abcdef12345678",
            "0000000000000000000000000000000000000000"
        ]

        for sha in valid_shas:
            # Should not raise exception
            git_ops.validate_commit_sha(sha)

    def test_validate_commit_sha_invalid(self, git_ops: GitOperations) -> None:
        """Test validation of invalid commit SHA."""
        invalid_shas = [
            "short",
            "1234567890abcdef1234567890abcdef1234567g",  # Contains invalid character
            "1234567890abcdef1234567890abcdef123456789",  # Too long
            "1234567890abcdef1234567890abcdef1234567",   # Too short
            "",
            None
        ]

        for sha in invalid_shas:
            with pytest.raises(GitOperationError, match="Invalid commit SHA format"):
                git_ops.validate_commit_sha(sha)

    def test_extract_repo_name_from_url(self, git_ops: GitOperations) -> None:
        """Test repository name extraction from URL."""
        test_cases = [
            ("https://github.com/user/repo.git", "repo"),
            ("https://github.com/user/my-project.git", "my-project"),
            ("git@github.com:user/repo.git", "repo"),
            ("https://gitlab.com/user/project.git", "project"),
            ("https://github.com/user/repo", "repo"),  # No .git suffix
        ]

        for url, expected_name in test_cases:
            assert git_ops.extract_repo_name(url) == expected_name

    def test_extract_repo_name_invalid_url(self, git_ops: GitOperations) -> None:
        """Test repository name extraction from invalid URL."""
        invalid_urls = [
            "invalid-url",
            "https://github.com/",
            "",
            "just-text"
        ]

        for url in invalid_urls:
            # Should return fallback name
            result = git_ops.extract_repo_name(url)
            assert result == "unknown-repo"

    @patch('subprocess.run')
    def test_get_repository_info_success(self, mock_run: MagicMock, git_ops: GitOperations) -> None:
        """Test getting repository information."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="a1b2c3d4e5f6789012345678901234567890abcd\n", stderr=""),  # Current commit
            MagicMock(returncode=0, stdout="main\n", stderr=""),  # Current branch
            MagicMock(returncode=0, stdout="https://github.com/user/repo.git\n", stderr="")  # Remote URL
        ]

        repo_path = "/tmp/repo"
        info = git_ops.get_repository_info(repo_path)

        assert info["current_commit"] == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert info["current_branch"] == "main"
        assert info["remote_url"] == "https://github.com/user/repo.git"

        # Verify git commands were called
        assert mock_run.call_count == 3

    @patch('subprocess.run')
    def test_get_repository_info_failure(self, mock_run: MagicMock, git_ops: GitOperations) -> None:
        """Test getting repository information when git commands fail."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git", "fatal: not a git repository")

        repo_path = "/tmp/not-a-repo"

        with pytest.raises(GitOperationError, match="Failed to get repository information"):
            git_ops.get_repository_info(repo_path)

    def test_git_operations_timeout_setting(self) -> None:
        """Test GitOperations timeout configuration."""
        git_ops_default = GitOperations()
        assert git_ops_default.timeout_seconds == 300  # Default timeout

        git_ops_custom = GitOperations(timeout_seconds=60)
        assert git_ops_custom.timeout_seconds == 60

    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_clone_repository_sets_size_mb(self, mock_run: MagicMock, mock_mkdtemp: MagicMock, git_ops: GitOperations, mock_successful_clone: MagicMock) -> None:
        """Test that clone_repository sets the repository size."""
        mock_mkdtemp.return_value = "/tmp/code-score-12345"
        mock_run.return_value = mock_successful_clone

        with patch('src.metrics.git_operations.GitOperations.calculate_repository_size') as mock_calc_size:
            mock_calc_size.return_value = 25.7

            repo_url = "https://github.com/test/repo.git"
            repository = git_ops.clone_repository(repo_url)

            assert repository.size_mb == 25.7
            mock_calc_size.assert_called_once_with("/tmp/code-score-12345/repo")

    @patch('os.path.getsize')
    @patch('os.walk')
    def test_calculate_repository_size(self, mock_walk: MagicMock, mock_getsize: MagicMock, git_ops: GitOperations) -> None:
        """Test repository size calculation."""
        # Mock os.walk to return sample file structure
        mock_walk.return_value = [
            ("/repo", ["src"], ["README.md", "main.py"]),
            ("/repo/src", [], ["module.py", "utils.py"])
        ]

        # Mock file sizes (in bytes)
        mock_getsize.side_effect = [1024, 2048, 1536, 512]  # Total: 5120 bytes = 5 KB

        size_mb = git_ops.calculate_repository_size("/repo")

        # 5120 bytes = 0.00488... MB
        assert abs(size_mb - 0.00488) < 0.001

    @patch('os.walk')
    def test_calculate_repository_size_permission_error(self, mock_walk: MagicMock, git_ops: GitOperations) -> None:
        """Test repository size calculation with permission error."""
        mock_walk.side_effect = PermissionError("Permission denied")

        size_mb = git_ops.calculate_repository_size("/restricted/repo")

        # Should return 0.0 on error
        assert size_mb == 0.0

    @patch('os.path.getsize')
    @patch('os.walk')
    def test_calculate_repository_size_file_not_found(self, mock_walk: MagicMock, mock_getsize: MagicMock, git_ops: GitOperations) -> None:
        """Test repository size calculation when file is deleted during calculation."""
        mock_walk.return_value = [("/repo", [], ["file.txt"])]
        mock_getsize.side_effect = FileNotFoundError("File not found")

        size_mb = git_ops.calculate_repository_size("/repo")

        # Should return 0.0 when files can't be accessed
        assert size_mb == 0.0