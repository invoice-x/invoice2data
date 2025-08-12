"""Nox sessions."""

import os
import shlex
import shutil
import sys
from pathlib import Path
from textwrap import dedent

import nox


nox.options.default_venv_backend = "uv"

package = "invoice2data"
python_versions = ["3.12", "3.11", "3.10", "3.9", "3.8"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = (
    "pre-commit",
    "safety",
    "mypy",
    "tests",
    "typeguard",
    "xdoctest",
    "docs-build",
)


def activate_virtualenv_in_precommit_hooks(session: nox.Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    assert session.bin is not None  # nosec

    # Only patch hooks containing a reference to this session's bindir. Support
    # quoting rules for Python and bash, but strip the outermost quotes so we
    # can detect paths within the bindir, like <bindir>/python.
    bindirs = [
        bindir[1:-1] if bindir[0] in "'\"" else bindir
        for bindir in (repr(session.bin), shlex.quote(session.bin))
    ]

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    headers = {
        # pre-commit < 2.16.0
        "python": f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """,
        # pre-commit >= 2.16.0
        "bash": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
        # pre-commit >= 2.17.0 on Windows forces sh shebang
        "/bin/sh": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
    }

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        if not hook.read_bytes().startswith(b"#!"):
            continue

        text = hook.read_text()

        if not any(
            (Path("A") == Path("a") and bindir.lower() in text.lower())
            or bindir in text
            for bindir in bindirs
        ):
            continue

        lines = text.splitlines()

        for executable, header in headers.items():
            if executable in lines[0].lower():
                lines.insert(1, dedent(header))
                hook.write_text("\n".join(lines))
                break


@nox.session(name="pre-commit", python=python_versions[0])
def precommit(session: nox.Session) -> None:
    """Lint using pre-commit."""
    args = session.posargs or [
        "run",
        "--all-files",
        "--hook-stage=manual",
        "--show-diff-on-failure",
    ]
    session.run_install(
        "uv",
        "sync",
        "--group",
        "dev",
        "--group",
        "lint",
        # external=True,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@nox.session(python=python_versions[0])
def safety(session: nox.Session) -> None:
    """Scan dependencies for insecure packages."""
    session.run("uv", "venv", external=True)  # Create the uv environment
    session.run("uv", "venv", "activate", external=True)  # Activate the uv environment
    session.run("uv", "export", "-o", "requirements.txt", external=True)
    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        "--group",
        "safety",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        external=True,
    )
    session.run(
        "safety",
        "check",
        "--full-report",
        "--file=requirements.txt",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        external=True,
    )


@nox.session(python=python_versions)
def mypy(session: nox.Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or ["src", "tests", "docs/conf.py"]
    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        "--group",
        "mypy",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        external=True,
    )
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        # "--group",
        # "lint",
        "--extra",
        "googlevision",
        "--extra",
        "ocr",
        "--extra",
        "ocrmypdf",
        "--extra",
        "pdfminer-six",
        "--extra",
        "pdfplumber",
        "--extra",
        "pyyaml",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run(
        "python",
        "-c",
        '"import google.cloud.vision; import google.cloud.storage"',
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.env["PYTHONPATH"] = "src"

    try:
        session.run(
            "coverage",
            "run",
            "--parallel",
            "-m",
            "pytest",
            env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        )
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@nox.session(python=python_versions[0])
def coverage(session: nox.Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]
    session.run(
        "uv",
        "pip",
        "install",
        "coverage[toml]",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        # external=True,
    )
    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@nox.session(python=python_versions[0])
def typeguard(session: nox.Session) -> None:
    """Runtime type checking using Typeguard."""
    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        "--extra",
        "pdfminer-six",
        "--group",
        "typeguard",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        # external=True,
    )
    session.run(
        "pytest",
        f"--typeguard-packages={package}",
        "-k",
        "not test_gvision",
        *session.posargs,
    )


@nox.session(python=python_versions)
def xdoctest(session: nox.Session) -> None:
    """Run examples with xdoctest."""
    if session.posargs:
        args = [package, *session.posargs]
    else:
        args = [f"--modname={package}", "--command=all"]
        if "FORCE_COLOR" in os.environ:
            args.append("--colored=1")

    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        "--group",
        "xdoctest",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        # external=True,
    )
    session.run("python", "-m", "xdoctest", *args)


@nox.session(name="docs-build", python=python_versions[0])
def docs_build(session: nox.Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    if not session.posargs and "FORCE_COLOR" in os.environ:
        args.insert(0, "--color")

    session.run(
        "uv",
        "sync",
        "--group",
        "docs",
        "--group",
        "dev",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        # external=True,
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@nox.session(python=python_versions[0])
def docs(session: nox.Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build"]
    session.run(
        "uv",
        "sync",
        "--group",
        "dev",
        "--group",
        "docs",
        # external=True,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
