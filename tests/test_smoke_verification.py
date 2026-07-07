"""Tests for SmokeVerifier — F016 冲烟验证."""

import pytest


class TestVerifyAllPassHappy:
    """T001: FUNC/happy — all checks pass on valid Python file."""

    def test_all_checks_pass(self):
        from app.core.smoke_verification import SmokeVerifier, VerificationResult

        verifier = SmokeVerifier()
        files = [{"path": "main.py", "content": "def foo():\n    pass\n"}]

        result = verifier.verify(files)

        assert isinstance(result, VerificationResult)
        assert result.syntax_ok is True
        assert result.imports_ok is True
        assert result.startup_ok is True
        assert result.errors == []


class TestVerifySyntaxError:
    """T002: FUNC/error — syntax error detected."""

    def test_syntax_error(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "bad.py", "content": "def foo(\n"}]

        result = verifier.verify(files)

        assert result.syntax_ok is False
        assert any("Syntax error" in e for e in result.errors)


class TestVerifyImportError:
    """T003: FUNC/error — missing module flagged."""

    def test_import_error(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "main.py", "content": "import nonexistent_xyz_module\n"}]

        result = verifier.verify(files)

        assert result.imports_ok is False
        assert any("not found" in e for e in result.errors)


class TestVerifyStartupError:
    """T004: FUNC/error — startup error caught."""

    def test_startup_error(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "crash.py", "content": "raise RuntimeError(\"boom\")\n"}]

        result = verifier.verify(files)

        assert result.startup_ok is False
        assert any("RuntimeError" in e for e in result.errors)


class TestVerifyEmptyFiles:
    """T005: BNDRY/edge — empty files list."""

    def test_empty_files(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = []

        result = verifier.verify(files)

        assert result.syntax_ok is False
        assert result.imports_ok is False
        assert result.startup_ok is False
        assert any("No files" in e for e in result.errors)


class TestVerifyEmptyContent:
    """T006: BNDRY/edge — empty content is valid Python."""

    def test_empty_content(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "empty.py", "content": ""}]

        result = verifier.verify(files)

        assert result.syntax_ok is True
        assert result.imports_ok is True
        assert result.startup_ok is True


class TestVerifyStdlibImportPasses:
    """T007: BNDRY/edge — stdlib imports pass."""

    def test_stdlib_import_pass(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "main.py", "content": "import os\nimport sys\nimport json\n"}]

        result = verifier.verify(files)

        assert result.imports_ok is True


class TestVerifyFromImport:
    """T008: BNDRY/edge — from X import Y handled correctly."""

    def test_from_import(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "main.py", "content": "from pathlib import Path\n"}]

        result = verifier.verify(files)

        assert result.imports_ok is True


class TestVerifyProjectCrossRef:
    """T009: FUNC/happy — project module cross-reference passes."""

    def test_project_cross_ref(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "src/utils.py", "content": "def helper():\n    pass\n"},
            {"path": "src/main.py", "content": "import src.utils\n"},
        ]

        result = verifier.verify(files)

        assert result.imports_ok is True


class TestVerifyMultipleSyntaxErrors:
    """T010: BNDRY/edge — 2 files both with syntax errors."""

    def test_multiple_syntax_errors(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "a.py", "content": "def foo(\n"},
            {"path": "b.py", "content": "x =\n"},
        ]

        result = verifier.verify(files)

        assert result.syntax_ok is False
        assert len([e for e in result.errors if "Syntax error" in e]) >= 2


class TestVerifyStartupNoValidFiles:
    """T011: BNDRY/edge — all files have syntax errors, startup fails."""

    def test_startup_no_valid_files(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "bad.py", "content": "def foo(\n"}]

        result = verifier.verify(files)

        assert result.startup_ok is False
        assert any("No valid files" in e for e in result.errors)


class TestVerifyStartupCrossFileRef:
    """T012: FUNC/happy — cross-file variable reference in exec."""

    def test_startup_cross_file_ref(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "lib.py", "content": "VALUE = 42\n"},
            {"path": "main.py", "content": "result = VALUE + 1\n"},
        ]

        result = verifier.verify(files)

        assert result.startup_ok is True


class TestVerifyCombinedSyntaxAndImport:
    """T013: BNDRY/edge — syntax error in one file, import check still runs on others."""

    def test_combined_syntax_and_import(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "good.py", "content": "import json\n"},
            {"path": "bad_syntax.py", "content": "def broken(\n"},
            {"path": "needs_bad.py", "content": "from bad_syntax import x\n"},
        ]

        result = verifier.verify(files)

        assert result.syntax_ok is False
        assert result.imports_ok is True


class TestVerifyRelativeImport:
    """T014: BNDRY/edge — relative from-import is skipped."""

    def test_relative_import(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "pkg/__init__.py", "content": ""},
            {"path": "pkg/mod.py", "content": "from . import something\n"},
        ]

        result = verifier.verify(files)

        assert result.syntax_ok is True
        assert result.imports_ok is True


class TestVerifySingleFileNoImports:
    """T015: BNDRY/edge — single file with no imports passes."""

    def test_single_file_no_imports(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [{"path": "main.py", "content": "x = 1\n"}]

        result = verifier.verify(files)

        assert result.syntax_ok is True
        assert result.imports_ok is True
        assert result.startup_ok is True


class TestVerifyMixedImportPassFail:
    """T016: FUNC/error — one import passes, one fails."""

    def test_mixed_import_pass_fail(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        files = [
            {"path": "a.py", "content": "import os\n"},
            {"path": "b.py", "content": "import nonexistent_xyz_module\n"},
        ]

        result = verifier.verify(files)

        assert result.imports_ok is False
        assert any("nonexistent_xyz_module" in e for e in result.errors)


class TestVerifyIndentationError:
    """T017: BNDRY/edge — IndentationError is caught."""

    def test_indentation_error(self):
        from app.core.smoke_verification import SmokeVerifier

        verifier = SmokeVerifier()
        content = "def foo():\n  x = 1\n    y = 2\n"
        files = [{"path": "bad.py", "content": content}]

        result = verifier.verify(files)

        assert result.syntax_ok is False
        assert any("Syntax error" in e or "IndentationError" in e for e in result.errors)
