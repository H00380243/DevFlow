"""Smoke Verification — F016 冲烟验证.

对 LLM 生成的 Python 代码执行语法/导入/启动三项独立检查。
纯计算模块，无外部依赖。
"""

import ast
import importlib.util

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    syntax_ok: bool = False
    imports_ok: bool = False
    startup_ok: bool = False
    errors: list[str] = Field(default_factory=list)


class SmokeVerifier:
    def verify(self, files: list[dict]) -> VerificationResult:
        if not files:
            return VerificationResult(
                syntax_ok=False, imports_ok=False, startup_ok=False,
                errors=["No files to verify"],
            )
        syntax_ok, syntax_errs = self.check_syntax(files)
        imports_ok, import_errs = self.check_imports(files)
        startup_ok, startup_errs = self.check_startup(files)
        return VerificationResult(
            syntax_ok=syntax_ok,
            imports_ok=imports_ok,
            startup_ok=startup_ok,
            errors=syntax_errs + import_errs + startup_errs,
        )

    def check_syntax(self, files: list[dict]) -> tuple[bool, list[str]]:
        errors = []
        for f in files:
            try:
                ast.parse(f["content"])
            except SyntaxError as e:
                errors.append(f"Syntax error in {f['path']}: {e.msg}")
        return (len(errors) == 0), errors

    def check_imports(self, files: list[dict]) -> tuple[bool, list[str]]:
        project_modules: set[str] = set()
        for f in files:
            mod = f["path"].replace("/", ".").replace("\\", ".")
            if mod.endswith(".py"):
                mod = mod[:-3]
            project_modules.add(mod)

        errors = []
        for f in files:
            try:
                tree = ast.parse(f["content"])
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if not self._module_available(top, project_modules):
                            errors.append(
                                f"Module '{top}' not found (imported by {f['path']})"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        top = node.module.split(".")[0]
                        if not self._module_available(top, project_modules):
                            errors.append(
                                f"Module '{top}' not found (imported by {f['path']})"
                            )
        return (len(errors) == 0), errors

    def check_startup(self, files: list[dict]) -> tuple[bool, list[str]]:
        valid = []
        for f in files:
            try:
                ast.parse(f["content"])
                valid.append(f)
            except SyntaxError:
                pass
        if not valid:
            return False, ["No valid files to execute"]
        namespace: dict = {}
        try:
            for f in sorted(valid, key=lambda x: x["path"]):
                exec(f["content"], namespace)
            return True, []
        except Exception as e:
            return False, [f"Startup error: {type(e).__name__}: {e}"]

    @staticmethod
    def _module_available(name: str, project_modules: set[str]) -> bool:
        if name in project_modules:
            return True
        for pm in project_modules:
            if pm == name or pm.endswith("." + name) or pm.startswith(name + "."):
                return True
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            return False
