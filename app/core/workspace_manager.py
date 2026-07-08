"""F025: WorkspaceManager — git worktree 隔离."""

import subprocess
from pathlib import Path

from app.core.adapters.base import Workspace
from app.core.config import get_settings


class WorkspaceManager:
    def __init__(self, repo_dir: str | None = None, base_dir: str | None = None):
        settings = get_settings()
        self._repo_dir = repo_dir or settings.GIT_REPO_DIR or "."
        self._base_dir = Path(base_dir or settings.WORKTREE_BASE_DIR)

    def acquire_workspace(self, req_id: str, stage: str, base_ref: str | None = None) -> Workspace:
        ws_path = self._base_dir / req_id / stage
        ws_path.parent.mkdir(parents=True, exist_ok=True)

        if not ws_path.exists():
            ref = base_ref or "HEAD"
            subprocess.run(
                ["git", "worktree", "add", str(ws_path), ref],
                cwd=self._repo_dir, check=True, capture_output=True, text=True,
            )

        return Workspace(
            path=str(ws_path),
            req_id=req_id,
            stage=stage,
            base_ref=base_ref,
        )

    def release_workspace(self, req_id: str, stage: str) -> None:
        ws_path = self._base_dir / req_id / stage
        if ws_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", str(ws_path)],
                cwd=self._repo_dir, capture_output=True, text=True,
            )

    def cleanup_old_workspaces(self, retention_days: int = 7) -> int:
        import time
        now = time.time()
        cutoff = now - retention_days * 86400
        removed = 0
        for ws_dir in self._base_dir.glob("*/*"):
            if ws_dir.is_dir():
                mtime = ws_dir.stat().st_mtime
                if mtime < cutoff:
                    self.release_workspace(ws_dir.parent.name, ws_dir.name)
                    removed += 1
        return removed
