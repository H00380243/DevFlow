"""Tests for GitHandler / GitCommitOrchestrator — F018 Git 提交."""

from unittest.mock import MagicMock, patch

import pytest


class TestCommitHappyPath:
    def test_commit_produces_result(self):
        from app.core.git_handler import GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123def456"
        git_handler.push.return_value = None
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        result = orchestrator.execute("REQ-20260709-001", files, push_enabled=True)
        assert result["branch_name"] == "feature/REQ-20260709-001"
        assert result["commit_id"] == "abc123def456"
        assert result["commit_message"].startswith("feat(")

    def test_file_count_in_message(self):
        from app.core.git_handler import GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123"
        git_handler.push.return_value = None
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}, {"path": "b.py", "content": "y = 2"}]
        result = orchestrator.execute("REQ-20260709-001", files, push_enabled=True)
        assert "2" in result["commit_message"]

    def test_many_files_truncated(self):
        from app.core.git_handler import GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123"
        git_handler.push.return_value = None
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": f"f{i}.py", "content": str(i)} for i in range(10)]
        result = orchestrator.execute("REQ-20260709-001", files, push_enabled=True)
        assert "5 more" in result["commit_message"] or "10" in result["commit_message"]


class TestCommitErrors:
    def test_push_retry_3x_fails(self):
        from app.core.git_handler import GitCommitFailedError, GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123"
        git_handler.push.side_effect = Exception("network error")
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        with pytest.raises(GitCommitFailedError):
            orchestrator.execute("REQ-20260709-001", files, push_enabled=True)

    def test_auth_error(self):
        from app.core.git_handler import CredentialExpiredError, GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123"
        git_handler.push.side_effect = Exception("authentication failed")
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        with pytest.raises(CredentialExpiredError):
            orchestrator.execute("REQ-20260709-001", files, push_enabled=True)

    def test_create_branch_error(self):
        from app.core.git_handler import GitCommitFailedError, GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.side_effect = Exception("cannot create branch")
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        with pytest.raises(GitCommitFailedError):
            orchestrator.execute("REQ-20260709-001", files, push_enabled=False)

    def test_push_retry_success(self):
        from app.core.git_handler import GitCommitOrchestrator

        git_handler = MagicMock()
        git_handler.create_branch.return_value = "feature/REQ-20260709-001"
        git_handler.commit.return_value = "abc123"
        call_count = 0
        def flaky_push(branch):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("transient error")
        git_handler.push.side_effect = flaky_push
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        result = orchestrator.execute("REQ-20260709-001", files, push_enabled=True)
        assert call_count == 3

    def test_empty_req_id(self):
        from app.core.git_handler import GitCommitOrchestrator

        git_handler = MagicMock()
        orchestrator = GitCommitOrchestrator(git_handler=git_handler)
        files = [{"path": "a.py", "content": "x = 1"}]
        with pytest.raises(ValueError):
            orchestrator.execute("", files, push_enabled=False)


class TestBuildCommitMessage:
    def test_format(self):
        from app.core.git_handler import GitCommitOrchestrator

        orchestrator = GitCommitOrchestrator(git_handler=MagicMock())
        files = [{"path": "a.py", "content": "x = 1"}]
        msg = orchestrator._build_commit_message("REQ-20260709-001", files)
        assert msg.startswith("feat(REQ-20260709-001):")

    def test_push_disabled_skips_push(self):
        from app.core.git_handler import GitCommitOrchestrator

        mock_git = MagicMock()
        mock_git.create_branch.return_value = "feature/REQ-20260709-002"
        mock_git.commit.return_value = "a1b2c3d"
        orch = GitCommitOrchestrator(git_handler=mock_git)
        result = orch.execute("REQ-20260709-002", [{"path": "a.py", "content": "x"}], push_enabled=False)
        mock_git.push.assert_not_called()
        assert result["branch_name"] == "feature/REQ-20260709-002"
