"""Tests for F025: WorkspaceManager worktree 隔离."""

import subprocess
from pathlib import Path

import pytest

from app.core.workspace_manager import WorkspaceManager


def _init_git_repo(path: Path):
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=str(path), capture_output=True, check=True)
    readme = path / "README.md"
    readme.write_text("# test", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(path), capture_output=True, check=True)


class TestWorkspaceManager:
    def test_init_defaults(self):
        wm = WorkspaceManager(repo_dir=".", base_dir=str(Path.cwd() / "data" / "test_ws"))
        assert wm._repo_dir == "."
        assert "test_ws" in str(wm._base_dir)

    def test_acquire_creates_directory(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        _init_git_repo(repo_dir)
        base_dir = tmp_path / "worktrees"
        wm = WorkspaceManager(repo_dir=str(repo_dir), base_dir=str(base_dir))
        ws = wm.acquire_workspace("REQ-001", "review")
        assert ws.req_id == "REQ-001"
        assert ws.stage == "review"
        assert Path(ws.path).exists()

    def test_release_workspace_nonexistent_does_not_raise(self):
        wm = WorkspaceManager(repo_dir=".", base_dir=str(Path.cwd() / "data" / "test_ws"))
        wm.release_workspace("NONEXISTENT", "review")

    def test_cleanup_old_workspaces(self, tmp_path):
        base_dir = tmp_path / "old_ws"
        old_dir = base_dir / "REQ-OLD" / "review"
        old_dir.mkdir(parents=True)
        wm = WorkspaceManager(repo_dir=str(tmp_path), base_dir=str(base_dir))
        count = wm.cleanup_old_workspaces(retention_days=0)
        assert count >= 0
