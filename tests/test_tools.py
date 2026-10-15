import pytest

from mcp_file_server.sandbox import Sandbox, SandboxError
from mcp_file_server.tools import FileTools, ToolError


@pytest.fixture
def ft(tmp_path):
    return FileTools(Sandbox(tmp_path / "ws"))


def test_write_and_read(ft):
    ft.write_file("a/note.txt", "hello")
    assert "hello" in ft.read_file("a/note.txt")


def test_write_no_overwrite(ft):
    ft.write_file("n.txt", "1")
    with pytest.raises(ToolError):
        ft.write_file("n.txt", "2", overwrite=False)


def test_read_in_chunks(ft):
    ft.write_file("big.txt", "abcdefghij")
    out = ft.read_file("big.txt", offset=0, limit=4)
    assert "abcd" in out and "offset=4" in out


def test_read_missing_file(ft):
    with pytest.raises(ToolError):
        ft.read_file("nope.txt")


def test_append(ft):
    ft.write_file("log.txt", "one\n")
    ft.append_file("log.txt", "two\n")
    assert "one\ntwo" in ft.read_file("log.txt")


def test_str_replace_ok(ft):
    ft.write_file("f.txt", "alpha beta")
    ft.str_replace("f.txt", "beta", "gamma")
    assert "alpha gamma" in ft.read_file("f.txt")


def test_str_replace_not_unique(ft):
    ft.write_file("f.txt", "x x")
    with pytest.raises(ToolError):
        ft.str_replace("f.txt", "x", "y")


def test_str_replace_missing(ft):
    ft.write_file("f.txt", "abc")
    with pytest.raises(ToolError):
        ft.str_replace("f.txt", "zzz", "y")


def test_delete_requires_confirm(ft):
    ft.write_file("d.txt", "x")
    with pytest.raises(ToolError):
        ft.delete_file("d.txt")
    assert "d.txt" in ft.list_files()


def test_delete_with_confirm(ft):
    ft.write_file("d.txt", "x")
    ft.delete_file("d.txt", confirm=True)
    assert ft.list_files() == "(empty)"


def test_delete_root_refused(ft):
    with pytest.raises(ToolError):
        ft.delete_file(".", confirm=True)


def test_delete_nonempty_dir_refused(ft):
    ft.write_file("dir/x.txt", "x")
    with pytest.raises(ToolError):
        ft.delete_file("dir", confirm=True)


def test_make_dir_and_list(ft):
    ft.make_dir("one/two")
    assert "one/two/" in ft.list_files(recursive=True)


def test_move(ft):
    ft.write_file("a.txt", "x")
    ft.move_file("a.txt", "sub/b.txt")
    assert "sub/b.txt" in ft.list_files(recursive=True)
    assert "a.txt (" not in ft.list_files(recursive=True)


def test_move_onto_existing_refused(ft):
    ft.write_file("a.txt", "1")
    ft.write_file("b.txt", "2")
    with pytest.raises(ToolError):
        ft.move_file("a.txt", "b.txt")


def test_search(ft):
    ft.write_file("a.txt", "Hello World\nbye")
    ft.write_file("b/c.txt", "say hello")
    out = ft.search_text("hello")
    assert "a.txt:1" in out and "b/c.txt:1" in out


def test_search_no_match(ft):
    assert ft.search_text("zzz") == "No matches."


def test_file_info(ft):
    ft.write_file("a.txt", "abc")
    assert "size: 3 bytes" in ft.file_info("a.txt")


# ---- Security: EVERY tool must reject escape attempts ----
CALLS = {
    "list_files": lambda ft, p: ft.list_files(p),
    "read_file": lambda ft, p: ft.read_file(p),
    "write_file": lambda ft, p: ft.write_file(p, "x"),
    "append_file": lambda ft, p: ft.append_file(p, "x"),
    "str_replace": lambda ft, p: ft.str_replace(p, "a", "b"),
    "delete_file": lambda ft, p: ft.delete_file(p, confirm=True),
    "make_dir": lambda ft, p: ft.make_dir(p),
    "move_src": lambda ft, p: ft.move_file(p, "ok.txt"),
    "move_dst": lambda ft, p: ft.move_file("ok.txt", p),
    "search_text": lambda ft, p: ft.search_text("x", p),
    "file_info": lambda ft, p: ft.file_info(p),
}


@pytest.mark.parametrize("bad", ["../x", "/etc/passwd", "C:\\Windows", "a/../../x", ".git/config"])
@pytest.mark.parametrize("name", list(CALLS))
def test_every_tool_rejects_escapes(ft, name, bad):
    with pytest.raises(SandboxError):
        CALLS[name](ft, bad)

        