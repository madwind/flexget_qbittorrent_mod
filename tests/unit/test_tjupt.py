from __future__ import annotations

from PIL import Image

from ptsites.trackers.tjupt import compareHash, toHash


def test_to_hash_uses_grayscale_average_threshold() -> None:
    image = Image.new('L', (10, 10))
    image.putdata([0] * 50 + [255] * 50)

    assert toHash(image) == '0' * 50 + '1' * 50


def test_compare_hash_returns_matching_pixel_ratio() -> None:
    assert compareHash('0' * 50 + '1' * 50, '0' * 75 + '1' * 25) == 0.75
