from pathlib import Path
import importlib.util


def _load_preprocess_module():
    # tests live under src/tests/... so parents[2] points to src/
    path = Path(__file__).resolve().parents[2] / "md2" / "scripts" / "preprocess_md.py"
    spec = importlib.util.spec_from_file_location("preprocess_md", str(path))
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def test_inserts_blank_line_before_dash_list():
    mod = _load_preprocess_module()
    src = ["**huhu**", "- a", "- b"]
    out = mod.preprocess_lines(src)
    assert out == ["**huhu**", "", "- a", "- b"]


def test_inserts_blank_line_before_star_list():
    mod = _load_preprocess_module()
    src = ["**title**", "* a", "* b"]
    out = mod.preprocess_lines(src)
    assert out == ["**title**", "", "* a", "* b"]


def test_idempotent_on_repeated_runs():
    mod = _load_preprocess_module()
    src = ["**x**", "", "- a", "- b"]
    once = mod.preprocess_lines(src)
    twice = mod.preprocess_lines(once)
    assert once == twice


def test_does_not_modify_inside_fences():
    mod = _load_preprocess_module()
    src = [
        "```",
        "**huhu**",
        "- a",
        "```",
        "**ok**",
        "- a",
    ]
    out = mod.preprocess_lines(src)
    # First list is inside fences -> unchanged; second list gets a blank line before it
    assert out == [
        "```",
        "**huhu**",
        "- a",
        "```",
        "**ok**",
        "",
        "- a",
    ]
