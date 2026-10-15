import os

import pytest

from mcp_file_server.sandbox import Sandbox, SandboxError


@pytest.fixture
def sb(tmp_path):
    return Sandbox(tmp_path / "ws")


def test_valid_paths(sb):
    assert sb.resolve("") == sb.root
    assert sb.resolve(".") == sb.root
    assert sb.resolve("notes.txt") == sb.root / "notes.txt"
    assert sb.resolve("a/b/c.txt") == sb.root / "a" / "b" / "c.txt"


@pytest.mark.parametrize(
    "bad",
    [
        "..",
        "../x",
        "a/../../x",
        "a\\..\\..\\x",
        "/etc/passwd",
        "\\Windows\\win.ini",
        "C:\\Windows\\win.ini",
        "C:/Windows",
        "\\\\server\\share\\f",
        "//server/share",
        "file.txt:stream",
        "x\x00y",
        ".git/config",
        "a/.GIT/config",
    ],
)
def test_forbidden_paths_are_rejected(sb, bad):
    with pytest.raises(SandboxError):
        sb.resolve(bad)


def test_non_string_rejected(sb):
    with pytest.raises(SandboxError):
        sb.resolve(None)


def test_symlink_escape_rejected(sb, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    try:
        os.symlink(outside, sb.root / "link", target_is_directory=True)
    except OSError:
        pytest.skip("Windows needs Developer Mode/admin to create symlinks")
    with pytest.raises(SandboxError):
        sb.resolve("link/secret.txt")


def test_relative_helper(sb):
    assert sb.relative(sb.root) == "."
    assert sb.relative(sb.root / "a" / "b.txt") == "a/b.txt"

    