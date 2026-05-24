"""--move/--copy sanitizes illegal filename characters (issue #544)."""

from pathlib import Path

from invoice2data.__main__ import _process_and_move_copy
from invoice2data.__main__ import _sanitize_filename_part


def test_sanitize_filename_part_replaces_illegal_chars() -> None:
    assert _sanitize_filename_part("123/001/2023") == "123_001_2023"
    assert _sanitize_filename_part('a<b>c:d"e/f\\g|h?i*j') == "a_b_c_d_e_f_g_h_i_j"
    assert _sanitize_filename_part("plain-name 2024") == "plain-name 2024"


def test_copy_with_illegal_chars_in_field(tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4")
    dest = tmp_path / "out"
    dest.mkdir()

    res = {
        "date": "2023-12-26",
        "invoice_number": "123/001/2023",  # the illegal "/" from the issue
        "desc": "Acme",
    }
    _process_and_move_copy(
        str(src), res, str(dest), None, "{date} {invoice_number} {desc}.pdf"
    )

    files = list(dest.iterdir())
    assert len(files) == 1
    assert files[0].name == "2023-12-26 123_001_2023 Acme.pdf"
    assert src.exists()  # copy leaves the original
