"""Git Handler — F018 Git 提交与密钥检测.

Provides SecretDetector (regex-based secret scanning), GitHandler (branch/commit/push),
and GitCommitOrchestrator (workflow orchestration).
"""

import re
import time
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SecretDetectedError(Exception):
    """Raised when one or more secrets are detected in source files."""

    def __init__(self, matches: list[dict]):
        self.matches = matches
        super().__init__(f"Secret detected in {len(matches)} location(s)")


class GitCommitFailedError(Exception):
    """Raised when Git commit/push operation fails after retries."""


class CredentialExpiredError(Exception):
    """Raised when Git push fails due to authentication/credential issues."""


# ---------------------------------------------------------------------------
# Secret Detection
# ---------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, str]] = [
    ("AWS Access Key", r"AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"),
    ("Generic API Key", r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    ("Generic Password", r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ("Bearer Token", r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    ("Private Key", r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    ("GitHub Token", r"ghp_[A-Za-z0-9]{36}"),
    ("Slack Token", r"xox[bpsar]-[0-9a-zA-Z\-]{10,}"),
]


class SecretDetector:
    """Regex-based secret scanner for source code files."""

    def detect(self, files: list[dict]) -> list[dict]:
        if not files:
            return []
        matches: list[dict] = []
        for f in files:
            path = f.get("path", "")
            content = f.get("content")
            if content is None or not isinstance(content, str):
                continue
            if not content:
                continue
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                for name, pattern in SECRET_PATTERNS:
                    if re.search(pattern, line):
                        matches.append({
                            "file_path": path,
                            "line_number": line_num,
                            "pattern_name": name,
                            "matched_text": line.strip()[:80],
                        })
        if matches:
            raise SecretDetectedError(matches)
        return []


# ---------------------------------------------------------------------------
# Git Operations
# ---------------------------------------------------------------------------

class GitHandler:
    """Low-level Git operations (create branch, commit, push).

    All operations are mockable — in production these wrap gitpython/CLI calls.
    """

    def create_branch(self, req_id: str) -> str:
        branch_name = f"feature/{req_id}"
        # In production: subprocess.run(["git", "checkout", "-b", branch_name])
        return branch_name

    def commit(self, branch: str, files: list[dict], message: str) -> str:
        # In production: subprocess.run(["git", "add", ...]) + subprocess.run(["git", "commit", ...])
        # Return a simulated commit SHA
        return "a1b2c3d4e5f6"

    def push(self, branch: str) -> None:
        # In production: subprocess.run(["git", "push", "origin", branch])
        pass


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class GitCommitOrchestrator:
    """Orchestrates the full Git commit workflow: secret scan → branch → commit → push."""

    MAX_PUSH_RETRIES = 3

    def __init__(self, git_handler: GitHandler | None = None):
        self._git = git_handler or GitHandler()
        self._detector = SecretDetector()

    def execute(self, req_id: str, files: list[dict], push_enabled: bool = True) -> dict:
        if not req_id:
            raise ValueError("req_id cannot be empty")

        # Step 1: Secret detection
        self._detector.detect(files)

        # Step 2: Create branch
        try:
            branch_name = self._git.create_branch(req_id)
        except Exception as e:
            raise GitCommitFailedError(f"Branch creation failed: {e}") from e

        # Step 3: Commit
        message = self._build_commit_message(req_id, files)
        try:
            commit_id = self._git.commit(branch_name, files, message)
        except Exception as e:
            raise GitCommitFailedError(f"Commit failed: {e}") from e

        # Step 4: Push with retry
        if push_enabled:
            self._retry_push(branch_name)

        return {
            "branch_name": branch_name,
            "commit_id": commit_id,
            "commit_message": message,
        }

    def _retry_push(self, branch: str) -> None:
        last_error: Exception | None = None
        for attempt in range(self.MAX_PUSH_RETRIES):
            try:
                self._git.push(branch)
                return
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                if "auth" in msg or "credential" in msg or "permission" in msg:
                    raise CredentialExpiredError(f"Authentication failed: {e}") from e
                if attempt < self.MAX_PUSH_RETRIES - 1:
                    time.sleep(2 ** attempt)
        raise GitCommitFailedError(
            f"Push failed after {self.MAX_PUSH_RETRIES} retries: {last_error}"
        )

    def _build_commit_message(self, req_id: str, files: list[dict]) -> str:
        count = len(files)
        if count <= 5:
            file_list = ", ".join(f["path"] for f in files)
        else:
            shown = ", ".join(f["path"] for f in files[:5])
            file_list = f"{shown} and {count - 5} more"
        return (
            f"feat({req_id}): auto-generated implementation\n\n"
            f"Files: {count} files changed ({file_list})"
        )
