from pathlib import Path
import importlib.util
import pytest


def _load_letter_module():
    path = Path(__file__).resolve().parents[2] / "md2" / "scripts" / "letter_preprocess.py"
    spec = importlib.util.spec_from_file_location("letter_preprocess", str(path))
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def test_required_tags_generate_header_and_remove_source_tags():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
Ralf Schneider
Verschaffeltstraße 14
</sender>

<receiver>
Netze BW GmbH
Schelmenwasenstraße 15
</receiver>

# Betreff

Text
"""
    )

    assert '<div class="md2-letter-header">' in out
    assert 'Ralf Schneider - Verschaffeltstraße 14' in out
    assert 'Netze BW GmbH<br>Schelmenwasenstraße 15' in out
    assert "<sender>" not in out
    assert "<receiver>" not in out
    assert "# Betreff" in out


def test_optional_tags_and_senderline_render_when_present():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A
B
</sender>
<receiver>
C
</receiver>
<senderline>
Custom Sender
</senderline>
<date>
26.06.2026
</date>
<email>
a@example.test
</email>
<phone>
123
</phone>
<reference>
ABC
</reference>
Body
"""
    )

    assert "Custom Sender" in out
    assert "E-Mail" in out
    assert "Telefon" in out
    assert "Referenz" in out
    assert "Datum" in out
    assert "26.06.2026" in out


def test_optional_tags_absent_are_not_rendered():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A
</sender>
<receiver>
B
</receiver>
Body
"""
    )

    assert '<dl class="md2-letter-meta">' not in out
    assert "E-Mail" not in out
    assert "Telefon" not in out
    assert "Referenz" not in out
    assert "Datum" not in out


def test_empty_senderline_uses_derived_senderline():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A
B
</sender>
<receiver>
C
</receiver>
<senderline>

</senderline>
Body
"""
    )

    assert 'class="md2-letter-sender-line">A - B</div>' in out


def test_html_escapes_letter_tag_content():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A & <B>
</sender>
<receiver>
C > D
</receiver>
Body
"""
    )

    assert "A &amp; &lt;B&gt;" in out
    assert "C &gt; D" in out


def test_reciver_typo_fails_as_unknown_tag():
    mod = _load_letter_module()
    with pytest.raises(mod.LetterPreprocessError, match="Unknown letter tag <reciver>"):
        mod.preprocess_letter_markdown(
            """<sender>
A
</sender>
<reciver>
B
</reciver>
Body
"""
        )


def test_unknown_metadata_tag_fails_loudly():
    mod = _load_letter_module()
    with pytest.raises(mod.LetterPreprocessError, match="Unknown letter tag <fax>"):
        mod.preprocess_letter_markdown(
            """<sender>
A
</sender>
<fax>
123
</fax>
<receiver>
B
</receiver>
Body
"""
        )


def test_missing_required_tags_fail_loudly():
    mod = _load_letter_module()
    with pytest.raises(mod.LetterPreprocessError, match="Missing required letter tag"):
        mod.preprocess_letter_markdown("# Body")

    with pytest.raises(mod.LetterPreprocessError, match="<receiver>"):
        mod.preprocess_letter_markdown(
            """<sender>
A
</sender>
Body
"""
        )


def test_duplicate_unclosed_nested_and_empty_tags_fail_loudly():
    mod = _load_letter_module()
    invalid_docs = [
        """<sender>
A
</sender>
<sender>
B
</sender>
<receiver>
C
</receiver>
""",
        """<sender>
A
</sender>
<receiver>
C
""",
        """<sender>
<receiver>
C
</receiver>
</sender>
""",
        """<sender>

</sender>
<receiver>
C
</receiver>
""",
        """<sender>
A
</sender>
<receiver>
B
</receiver>
<date>
1
</date>
<date>
2
</date>
""",
    ]
    for source in invalid_docs:
        with pytest.raises(mod.LetterPreprocessError):
            mod.preprocess_letter_markdown(source)


def test_tag_like_text_inside_fenced_code_is_body_content():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A
</sender>
<receiver>
B
</receiver>

```
<sender>
not metadata
</sender>
```
"""
    )

    assert "not metadata" in out
    assert out.count('<div class="md2-letter-header">') == 1


def test_remaining_markdown_body_order_is_preserved():
    mod = _load_letter_module()
    out = mod.preprocess_letter_markdown(
        """<sender>
A
</sender>
<receiver>
B
</receiver>
First paragraph

## Section

Second paragraph
"""
    )

    assert out.index("First paragraph") < out.index("## Section") < out.index("Second paragraph")
