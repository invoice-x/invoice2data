# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [MIT license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

[mit license]: https://opensource.org/licenses/MIT
[source code]: https://github.com/invoice-x/invoice2data
[documentation]: https://invoice2data.readthedocs.io/
[issue tracker]: https://github.com/invoice-x/invoice2data/issues

## How to report a bug

Report bugs on the [Issue Tracker].

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

## How to request a feature

Request features on the [Issue Tracker].

## How to set up your development environment

You need Python 3.9+ and the following tools:

- [uv]
- [Nox]

Install the package with development requirements:

```console
$ uv install
```

You can now run an interactive Python session,
or the command-line interface:

```console
$ uv run python
$ uv run invoice2data
```

[uv]: https://docs.astral.sh/uv/
[nox]: https://nox.thea.codes/

## How to test the project

Run the full test suite:

```console
$ nox
```

List the available Nox sessions:

```console
$ nox --list-sessions
```

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

```console
$ nox --session=tests
```

Unit tests are located in the _tests_ directory,
and are written using the [pytest] testing framework.

[pytest]: https://pytest.readthedocs.io/

## How to submit changes

Open a [pull request] to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
$ nox --session=pre-commit -- install
```

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.

[pull request]: https://github.com/invoice-x/invoice2data/pulls


## Writing Documentation


Writing documentation, function docstrings, examples and tutorials is a great way to start contributing to open-source software! The documentation is present inside the ``docs/`` directory of the source code repository.

The documentation is written in [markdown], with [Sphinx] used to generate these lovely HTML files that you're currently reading (unless you're reading this on GitHub). You can edit the documentation using any text editor and then generate the HTML output by running `make html` in the ``docs/`` directory.

The function docstrings are written in google style. Make sure you check out how its format guidelines before you start writing one.

[markdown]: https://en.wikipedia.org/wiki/markdown
[Sphinx]: http://www.sphinx-doc.org/en/master/



## How to make a release

```{note}
*You need to be a project maintainer to make a release.*
```
Before making a release, go through the following checklist:

- All pull requests for the release have been merged.
- The default branch passes all checks.

Releases are made by publishing a GitHub Release.
A draft release is being maintained based on merged pull requests.
To publish the release, follow these steps:

1. Click **Edit** next to the draft release.
2. Enter a tag with the new version.
3. Enter the release title, also the new version.
4. Edit the release description, if required.
5. Click **Publish Release**.

After publishing the release, the following automated steps are triggered:

- The Git tag is applied to the repository.
- `Read the Docs` builds a new stable version of the documentation.

<!-- github-only -->

[code of conduct]: CODE_OF_CONDUCT.md
