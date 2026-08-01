"""OSS-Fuzz harness for the `regex` engine on user-supplied template patterns.

Templates ship arbitrary regex patterns via the ``regex`` / ``lines`` /
``tables`` field parsers. The `regex` library rejects some pathological
patterns outright (`regex.error`); anything else is either a compile-time
crash we should surface, or a runtime hang the fuzzer will detect via the
libFuzzer timeout.
"""

import sys

import atheris


with atheris.instrument_imports():
    import regex  # type: ignore[import-untyped]


def TestOneInput(data: bytes) -> None:  # noqa: N802
    fdp = atheris.FuzzedDataProvider(data)
    pattern = fdp.ConsumeUnicodeNoSurrogates(128)
    try:
        compiled = regex.compile(pattern)
    except (regex.error, ValueError, RecursionError):
        return  # documented failure modes for hostile patterns

    # Also exercise the matching path on a bounded body -- ReDoS shows up
    # here, not at compile time. libFuzzer's `-timeout` flag catches hangs.
    body = fdp.ConsumeUnicodeNoSurrogates(256)
    try:
        compiled.search(body)
    except (regex.error, ValueError):
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
