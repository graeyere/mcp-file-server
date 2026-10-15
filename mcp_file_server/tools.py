"""Tool logic. Each method resolves paths through the Sandbox FIRST."""
import os
from datetime import datetime
from pathlib import Path

from .sandbox import Sandbox

MAX_READ_CHARS = 20000
MAX_FILE_BYTES = 2_000_000
MAX_WRITE_BYTES = 1_000_000


class ToolError(Exception):
    """A friendly error the agent can read and recover from."""


class FileTools:
    def __init__(self, sandbox: Sandbox):
        self.sb = sandbox

    def _rel(self, p: Path) -> str:
        return self.sb.relative(p)

    def _read_text(self, target: Path, shown: str) -> str:
        if not target.is_file():
            raise ToolError(f"File not found: '{shown}'.")
        if target.stat().st_size > MAX_FILE_BYTES:
            raise ToolError(f"'{shown}' is too large (limit {MAX_FILE_BYTES} bytes).")
        try:
            with open(target, "r", encoding="utf-8", newline="") as f:
                return f.read()
        except UnicodeDecodeError:
            raise ToolError(f"'{shown}' is not UTF-8 text.")

    def _write_text(self, target: Path, text: str, mode: str = "w") -> None:
        if len(text.encode("utf-8")) > MAX_WRITE_BYTES:
            raise ToolError(f"Content too large (limit {MAX_WRITE_BYTES} bytes).")
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, mode, encoding="utf-8", newline="") as f:
            f.write(text)

    def list_files(self, path: str = ".", recursive: bool = False, max_entries: int = 200) -> str:
        target = self.sb.resolve(path)
        if not target.is_dir():
            raise ToolError(f"'{path}' is not a directory.")
        found = []
        if recursive:
            for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
                dirnames[:] = sorted(d for d in dirnames if d.lower() != ".git")
                found += [Path(dirpath) / d for d in dirnames]
                found += [Path(dirpath) / n for n in sorted(filenames)]
        else:
            found = sorted(p for p in target.iterdir() if p.name.lower() != ".git")
        lines = []
        for p in found:
            if p.is_symlink():
                continue  # symlinks are hidden from listings
            rel = os.path.relpath(p, self.sb.root).replace("\\", "/")
            lines.append(rel + "/" if p.is_dir() else f"{rel} ({p.stat().st_size} bytes)")
        if not lines:
            return "(empty)"
        extra = len(lines) - max_entries
        out = "\n".join(lines[:max_entries])
        if extra > 0:
            out += f"\n... {extra} more entries not shown. Narrow the path."
        return out

    def read_file(self, path: str, offset: int = 0, limit: int = 20000) -> str:
        target = self.sb.resolve(path)
        if offset < 0 or limit < 1 or limit > MAX_READ_CHARS:
            raise ToolError(f"offset must be >= 0 and limit between 1 and {MAX_READ_CHARS}.")
        text = self._read_text(target, path)
        chunk = text[offset : offset + limit]
        end = offset + len(chunk)
        head = f"[{self._rel(target)} chars {offset}-{end} of {len(text)}]"
        if end < len(text):
            head += f" More available: call again with offset={end}."
        return head + "\n" + chunk

    def write_file(self, path: str, content: str, overwrite: bool = True) -> str:
        target = self.sb.resolve(path)
        if target == self.sb.root or target.is_dir():
            raise ToolError(f"'{path}' is a directory.")
        if target.exists() and not overwrite:
            raise ToolError(f"'{path}' already exists and overwrite is false.")
        self._write_text(target, content)
        return f"Wrote {len(content)} chars to {self._rel(target)}."

    def append_file(self, path: str, content: str) -> str:
        target = self.sb.resolve(path)
        if target == self.sb.root or target.is_dir():
            raise ToolError(f"'{path}' is a directory.")
        self._write_text(target, content, mode="a")
        return f"Appended {len(content)} chars to {self._rel(target)}."

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        target = self.sb.resolve(path)
        if not old_str:
            raise ToolError("old_str must not be empty.")
        text = self._read_text(target, path)
        count = text.count(old_str)
        if count == 0:
            raise ToolError(f"old_str not found in '{path}'. Read the file and copy the text exactly.")
        if count > 1:
            raise ToolError(f"old_str appears {count} times in '{path}'. Add surrounding text to make it unique.")
        self._write_text(target, text.replace(old_str, new_str, 1))
        return f"Replaced 1 occurrence in {self._rel(target)}."

    def delete_file(self, path: str, confirm: bool = False) -> str:
        target = self.sb.resolve(path)
        if target == self.sb.root:
            raise ToolError("Cannot delete the workspace root.")
        if not confirm:
            raise ToolError("Deletion not confirmed. Call again with confirm=true if you are sure.")
        if not target.exists():
            raise ToolError(f"Not found: '{path}'.")
        if target.is_dir():
            try:
                target.rmdir()
            except OSError:
                raise ToolError(f"Directory '{path}' is not empty. Delete its files first.")
        else:
            target.unlink()
        return f"Deleted {path}."

    def make_dir(self, path: str) -> str:
        target = self.sb.resolve(path)
        if target.exists() and not target.is_dir():
            raise ToolError(f"'{path}' exists and is a file.")
        target.mkdir(parents=True, exist_ok=True)
        return f"Directory ready: {self._rel(target)}."

    def move_file(self, src: str, dst: str) -> str:
        s = self.sb.resolve(src)
        d = self.sb.resolve(dst)
        if s == self.sb.root or d == self.sb.root:
            raise ToolError("Cannot move the workspace root.")
        if not s.exists():
            raise ToolError(f"Source not found: '{src}'.")
        if d.exists():
            raise ToolError(f"Destination already exists: '{dst}'.")
        d.parent.mkdir(parents=True, exist_ok=True)
        s.rename(d)
        return f"Moved {self._rel(s) if s.exists() else src} -> {self._rel(d)}."

    def search_text(self, query: str, path: str = ".", max_results: int = 50) -> str:
        start = self.sb.resolve(path)
        if not query:
            raise ToolError("query must not be empty.")
        if not start.is_dir():
            raise ToolError(f"'{path}' is not a directory.")
        q = query.lower()
        hits = []
        for dirpath, dirnames, filenames in os.walk(start, followlinks=False):
            dirnames[:] = [d for d in dirnames if d.lower() != ".git"]
            for name in sorted(filenames):
                p = Path(dirpath) / name
                if p.is_symlink() or p.stat().st_size > MAX_FILE_BYTES:
                    continue
                try:
                    with open(p, "r", encoding="utf-8", newline="") as f:
                        for n, line in enumerate(f, 1):
                            if q in line.lower():
                                rel = os.path.relpath(p, self.sb.root).replace("\\", "/")
                                hits.append(f"{rel}:{n}: {line.strip()[:200]}")
                                if len(hits) >= max_results:
                                    return "\n".join(hits) + f"\n... stopped at {max_results} results."
                except UnicodeDecodeError:
                    continue
        return "\n".join(hits) if hits else "No matches."

    def file_info(self, path: str) -> str:
        target = self.sb.resolve(path)
        if not target.exists():
            raise ToolError(f"Not found: '{path}'.")
        st = target.stat()
        kind = "directory" if target.is_dir() else "file"
        mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
        return f"path: {self._rel(target)}\ntype: {kind}\nsize: {st.st_size} bytes\nmodified: {mtime}"

