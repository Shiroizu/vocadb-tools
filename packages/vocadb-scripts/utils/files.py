from pathlib import Path


def save_file(filepath: str, content: str | list) -> None:
    """Safely writes content to a file, creating necessary directories."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        if isinstance(content, list):
            content = list(map(str, content))
            f.write("\n".join(content))
        else:
            f.write(str(content))
