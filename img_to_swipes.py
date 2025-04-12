import logging
import sys
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Iterator

import cairosvg
from com.dtmilano.android.viewclient import ViewClient
from culebratester_client.models import Point
from PIL import Image
from tqdm import tqdm

IMG = Path("img/fry.svg")
START_X = 160
START_Y = 880
MAX_WIDTH = 760
MAX_HEIGHT = 520

DRAW_DEBUG_FRAME = False
DUMP_BMP = True
FRAME_SEGMENT_STEPS = 70
DRAW_SWIPE_SIZE = 100

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.INFO)


def load_black_pixels(svg_path: Path) -> Iterator[tuple[int, int]]:
    png_data = cairosvg.svg2png(url=svg_path.as_posix(), output_width=MAX_WIDTH, output_height=MAX_HEIGHT)
    img = Image.open(BytesIO(png_data)).convert("LA")
    for y in range(img.height):
        for x in range(img.width):
            pixel = img.getpixel((x, y))
            assert isinstance(pixel, tuple)
            luminosity, alpha = pixel
            if alpha > 0 and luminosity < 255:
                yield (x, y)


def save_black_pixels(black_pixels: set[tuple[int, int]], bmp_path: Path) -> None:
    top = min(y for _, y in black_pixels)
    bottom = max(y for _, y in black_pixels)
    left = min(x for x, _ in black_pixels)
    right = max(x for x, _ in black_pixels)
    width = right - left + 1
    height = bottom - top + 1
    img = Image.new("RGB", (width, height), color="white")
    for x, y in black_pixels:
        img.putpixel((x - left, y - top), (0, 0, 0))
    img.save(bmp_path)


def horisontal_align_left(pixels: set[tuple[int, int]]) -> Iterator[tuple[int, int]]:
    left = min(x for x, _ in pixels)
    for x, y in pixels:
        yield (x - left, y)


def get_neighbors(pos: tuple[int, int]) -> Iterator[tuple[int, int]]:
    yield (pos[0] - 1, pos[1])
    yield (pos[0] + 1, pos[1])
    yield (pos[0], pos[1] - 1)
    yield (pos[0], pos[1] + 1)
    yield (pos[0] - 1, pos[1] - 1)
    yield (pos[0] - 1, pos[1] + 1)
    yield (pos[0] + 1, pos[1] - 1)
    yield (pos[0] + 1, pos[1] + 1)


def find_connected_pixels(
    all_pixels: set[tuple[int, int]], high_priority_pixels: set[tuple[int, int]], sequence_length: int
) -> Iterator[tuple[int, int]]:
    sequence_pixels = Counter()
    last_pixel = next(iter(high_priority_pixels))
    sequence_pixels[last_pixel] += 1
    sequence_length -= 1
    yield last_pixel

    for _ in range(sequence_length):
        best_neighbor = None
        best_neighbor_rank = 0
        for neighbor in get_neighbors(last_pixel):
            if neighbor not in all_pixels:
                continue

            neighbor_rank = 0
            if neighbor in sequence_pixels:
                neighbor_rank = sequence_pixels[neighbor] + 1
            elif neighbor in high_priority_pixels:
                neighbor_rank = 0
            else:
                neighbor_rank = 1

            if best_neighbor is None or neighbor_rank < best_neighbor_rank:
                best_neighbor = neighbor
                best_neighbor_rank = neighbor_rank

        if best_neighbor is not None:
            last_pixel = best_neighbor

        sequence_pixels[last_pixel] += 1
        yield last_pixel


def find_content_frame(black_pixels: set[tuple[int, int]]) -> Iterator[tuple[int, int]]:
    top = min(y for _, y in black_pixels)
    bottom = max(y for _, y in black_pixels)
    left = min(x for x, _ in black_pixels)
    right = max(x for x, _ in black_pixels)

    yield (left, top)
    yield (right, top)
    yield (right, bottom)
    yield (left, bottom)
    yield (left, top)


def swipe(view_client: ViewClient, pixels: Iterator[tuple[int, int]], segment_steps: int) -> None:
    segments = [Point(x + START_X, y + START_Y) for x, y in pixels]
    view_client.uiAutomatorHelper.ui_device.swipe(segments=segments, segment_steps=segment_steps)


def main() -> None:
    workdir = Path(__file__).parent
    svg_path = workdir / IMG
    black_pixels = set(load_black_pixels(svg_path))
    LOGGER.info(f"Loaded {len(black_pixels)} black pixels from {svg_path}")

    if DUMP_BMP:
        bmp_path = workdir / "img_to_swipes.bmp"
        save_black_pixels(black_pixels, bmp_path)
        LOGGER.info(f"Saved black pixels to {bmp_path}")

    black_pixels = set(horisontal_align_left(black_pixels))

    view_client = ViewClient(*ViewClient.connectToDeviceOrExit(), useuiautomatorhelper=True)

    if DRAW_DEBUG_FRAME:
        content_frame = find_content_frame(black_pixels)
        swipe(view_client, content_frame, FRAME_SEGMENT_STEPS)

        target_frame = [
            (0, 0),
            (MAX_WIDTH, 0),
            (MAX_WIDTH, MAX_HEIGHT),
            (0, MAX_HEIGHT),
            (0, 0),
        ]
        swipe(view_client, target_frame, FRAME_SEGMENT_STEPS)

    unprocessed_pixels = set(black_pixels)
    pbar = tqdm(total=len(unprocessed_pixels), desc="Drawing")
    while unprocessed_pixels:  # pylint: disable=while-used
        connected_pixels = list(find_connected_pixels(black_pixels, unprocessed_pixels, DRAW_SWIPE_SIZE))
        swipe(view_client, connected_pixels, 2)

        old_unprocessed_pixels_len = len(unprocessed_pixels)
        unprocessed_pixels.difference_update(connected_pixels)
        new_unprocessed_pixels_len = len(unprocessed_pixels)
        pbar.update(old_unprocessed_pixels_len - new_unprocessed_pixels_len)
    pbar.close()


if __name__ == "__main__":
    main()
