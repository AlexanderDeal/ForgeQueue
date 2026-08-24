from pathlib import Path
from PIL import Image

from app.image_processor import create_thumbnail


def test_create_thumbnail(tmp_path: Path) -> None:
	source = tmp_path / "source.png"
	output = tmp_path / "thumbnail.png"

	Image.new("RGB", (800, 400), color="blue").save(source)

	create_thumbnail(source, output, (200, 200))

	assert output.exists()
	with Image.open(output) as thumbnail:
		assert thumbnail.size == (200, 100)
