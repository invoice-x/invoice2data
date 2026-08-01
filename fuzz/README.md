# Fuzz targets

Continuous fuzzing via [OSS-Fuzz](https://google.github.io/oss-fuzz/). This
directory ships the [Atheris](https://github.com/google/atheris)-based
harnesses invoice2data exposes to OSS-Fuzz's build system.

## What each harness covers

| Harness | Target |
|---------|--------|
| `fuzz_parse_number.py` | `InvoiceTemplate.parse_number` -- locale / separator edge cases |
| `fuzz_parse_date.py` | `InvoiceTemplate.parse_date` -- format + language matrix |
| `fuzz_ordered_load.py` | `ordered_load` (stream loader) on both JSON + YAML payloads |
| `fuzz_regex_compile.py` | `regex.compile` on user-supplied template patterns (ReDoS guard) |

Same crash class the in-repo property tests (`tests/test_property.py`,
`hypothesis`) exercise -- OSS-Fuzz runs them continuously on Google's
infrastructure, catches the long-tail cases the ~500 hypothesis examples
per CI run miss, and lands corpus regressions as GitHub issues via the
OSS-Fuzz issue-tracker integration.

## Running locally

```bash
uv sync --group dev --extra ai --extra dateparser
pip install atheris

# 30-second smoke run
python fuzz/fuzz_parse_number.py -atheris_runs=100000

# Longer campaign with a corpus dir
mkdir -p /tmp/i2d-corpus
python fuzz/fuzz_ordered_load.py /tmp/i2d-corpus -runs=-1
```

## OSS-Fuzz project files

Templates for the PR that lands in
[`google/oss-fuzz/projects/invoice2data/`](https://github.com/google/oss-fuzz/tree/master/projects)
live under [`oss-fuzz/`](./oss-fuzz/). Copy them into a fork of
google/oss-fuzz, adjust the emails/URLs, and open the intake PR -- the OSS-Fuzz
team usually reviews within a week.

## Contract each harness enforces

Every harness catches the *typed* failure modes
(`invoice2data.exceptions.InvoiceProcessingError` and `ValueError`) so
they don't count as findings. Any other exception is a real bug: the
library's contract with callers is that parser inputs either return
sensible failure values or raise a typed error class.
