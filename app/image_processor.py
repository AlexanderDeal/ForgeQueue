from pathlib import Path

from PIL import Image


def create_thumbnail(
    input_path: Path,
    output_path: Path,
    max_size: tuple[int, int],
) -> None:
    with Image.open(input_path) as image:
        image.thumbnail(max_size)
        image.save(output_path)