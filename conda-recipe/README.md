# conda-forge recipe

This directory holds the conda recipe used to publish invoice2data to
[conda-forge](https://conda-forge.org/) (issue #626). conda-forge packages live
in their own *feedstock* repo, created by submitting this recipe to
[conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes).

## Why `noarch: python`

invoice2data's optional mypyc compilation is gated behind
`INVOICE2DATA_COMPILE_MYPYC=1` (off by default), so a plain `pip install` is
pure-Python. That means the conda package can be a single `noarch: python` build
— no per-platform compiler, no wheel matrix. (PyPI still ships the compiled
wheels for speed; the conda package trades that micro-optimisation for a much
simpler feedstock. A compiled feedstock can be added later if there's demand.)

## Submitting (after the PyPI release)

1. Release `invoice2data` to PyPI (the normal `master` release flow builds the
   sdist + wheels).
2. Get the sdist hash:
   ```bash
   pip download invoice2data==<version> --no-binary :all: --no-deps -d /tmp/i2d
   sha256sum /tmp/i2d/invoice2data-<version>.tar.gz
   ```
3. Update `version` and `sha256` in `meta.yaml`.
4. Copy `meta.yaml` into `staged-recipes/recipes/invoice2data/meta.yaml`, open a
   PR there, and address the lint bot. Once merged, conda-forge creates the
   `invoice2data-feedstock` and the package builds automatically.
5. Future releases are then maintained in that feedstock (a bot opens version-bump
   PRs); keep this copy in sync as the source of truth.

Validate locally before submitting:

```bash
conda install -n base conda-build conda-verify
conda build conda-recipe/
```
