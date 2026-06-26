from pathlib import Path
import importlib.util
import pytest


def _load_body_class_module():
    path = Path(__file__).resolve().parents[2] / "md2" / "scripts" / "html_body_classes.py"
    spec = importlib.util.spec_from_file_location("html_body_classes", str(path))
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def test_adds_body_classes_to_plain_body():
    mod = _load_body_class_module()
    out = mod.add_body_classes("<html><body><p>x</p></body></html>", ["letter", "no-toc"])
    assert '<body class="letter no-toc">' in out


def test_preserves_existing_classes_without_duplicates():
    mod = _load_body_class_module()
    out = mod.add_body_classes(
        '<html><body id="doc" class="existing letter"><p>x</p></body></html>',
        ["letter", "no-toc"],
    )
    assert 'class="existing letter no-toc"' in out
    assert 'id="doc"' in out


def test_fails_when_body_tag_is_missing():
    mod = _load_body_class_module()
    with pytest.raises(mod.BodyClassError, match="No <body> tag found"):
        mod.add_body_classes("<html><p>x</p></html>", ["no-toc"])
