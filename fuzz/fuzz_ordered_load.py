"""OSS-Fuzz harness for `invoice2data.extract.loader.ordered_load`.

`ordered_load` accepts an untrusted string (from a DB column or API payload)
and returns `list[InvoiceTemplate]` -- empty list on parse error. Every
crash class here maps to a real ingest bug: the two initial hypothesis
findings (int/None returning from `json.loads` / `yaml.safe_load` -> loader
iterating a non-list) are already patched; OSS-Fuzz keeps looking for the
long-tail cases.
"""

import sys

import atheris


with atheris.instrument_imports():
    import yaml  # type: ignore[import-untyped]

    from invoice2data.extract.loader import ordered_load


def TestOneInput(data: bytes) -> None:  # noqa: N802
    fdp = atheris.FuzzedDataProvider(data)
    # First byte picks JSON vs YAML, rest is the payload.
    kind = fdp.ConsumeIntInRange(0, 1)
    payload = fdp.ConsumeUnicodeNoSurrogates(1024)
    loader = yaml.safe_load if kind else None  # `None` -> default json.loads
    if loader is None:
        result = ordered_load(payload)
    else:
        result = ordered_load(payload, loader=loader)
    # Contract: always a list, never propagates the parser's exception.
    assert isinstance(result, list), (
        f"ordered_load returned {type(result).__name__}, expected list"
    )


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
