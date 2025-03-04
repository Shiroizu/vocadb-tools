from pathlib import Path


def save_file(filepath: str, content: str | list, append=False) -> None:
    """Safely writes content to a file, creating necessary directories."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w"
    if append:
        mode = "a"

    with path.open(mode, encoding="utf-8") as f:
        if isinstance(content, list):
            content = list(map(str, content))
            f.write("\n".join(content))
        else:
            f.write(str(content))
        if append:
            f.write("\n")

def clear_file(filepath: str):
    """Clear file if it exists."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        _ = input(f"Clearing file '{filepath}'. Press enter to continue.'")

    with path.open("w", encoding="utf-8") as f:
        f.write("")
