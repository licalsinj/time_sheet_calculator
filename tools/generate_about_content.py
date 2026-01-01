"""
generate_about_content.py

Generates a Python module from src/ABOUT.md so the About content can be
embedded into the executable at build time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def read_about_markdown(path: Path) -> str:
    """
    Reads markdown content from the provided path.

    Args:
        path: Path to the ABOUT.md file.

    Returns:
        Markdown content as a string.

    Raises:
        FileNotFoundError: If the file is missing.
        OSError: If the file cannot be read.
    """
    return path.read_text(encoding="utf-8")


def write_python_module(target: Path, content: str) -> None:
    """
    Writes a Python module containing the markdown content.

    Args:
        target: Path to the output Python module.
        content: Markdown content to embed.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.
    """
    header = (
        '"""\n'
        "about_content.py\n"
        "\n"
        "Auto-generated file. Do not edit directly.\n"
        '"""\n\n'
    )
    target.write_text(f"{header}ABOUT_MARKDOWN = {content!r}\n", encoding="utf-8")


def main() -> None:
    """
    Script entry point for generating the about_content module.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    root_dir = Path(__file__).resolve().parents[1]
    about_candidates = [
        root_dir / "src" / "ABOUT.md",
        root_dir / "src" / "about.md",
    ]
    about_path: Optional[Path] = None
    for candidate in about_candidates:
        if candidate.exists():
            about_path = candidate
            break

    if about_path is None:
        raise FileNotFoundError("ABOUT.md (or about.md) was not found in src/")
    output_path = root_dir / "src" / "about_content.py"

    markdown = read_about_markdown(about_path)
    write_python_module(output_path, markdown)


if __name__ == "__main__":
    main()
