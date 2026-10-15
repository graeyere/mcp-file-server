"""Path safety. Every tool must call Sandbox.resolve() before touching a file."""
from pathlib import Path, PurePosixPath, PureWindowsPath


class SandboxError(Exception):
    """Raised when a path is not allowed."""


class Sandbox:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, user_path) -> Path:
        """Return a safe absolute path inside the root, or raise SandboxError."""
        if not isinstance(user_path, str):
            raise SandboxError("Path must be a string.")
        if "\x00" in user_path:
            raise SandboxError("Path contains an invalid character.")

        p = user_path.strip()
        if p in ("", "."):
            return self.root

        if ":" in p:
            raise SandboxError(f"Path '{user_path}' is not allowed (':' is forbidden).")
        if PureWindowsPath(p).anchor or PurePosixPath(p).anchor:
            raise SandboxError(f"Absolute paths are not allowed: '{user_path}'.")

        parts = [x.lower() for x in p.replace("\\", "/").split("/")]
        if ".." in parts:
            raise SandboxError(f"'..' is not allowed in paths: '{user_path}'.")
        if ".git" in parts:
            raise SandboxError("Access to .git is not allowed.")

        # resolve() follows symlinks, so a link pointing outside ends up outside.
        candidate = (self.root / p).resolve()
        if candidate != self.root and not candidate.is_relative_to(self.root):
            raise SandboxError(f"Path '{user_path}' is outside the workspace.")
        return candidate

    def relative(self, path: Path) -> str:
        """Show a path relative to the root (never leak the full disk path)."""
        rel = Path(path).resolve().relative_to(self.root).as_posix()
        return "." if rel == "" else rel


    