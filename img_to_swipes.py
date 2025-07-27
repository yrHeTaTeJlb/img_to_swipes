import importlib
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Iterator

import cv2
import numpy as np
import pymupdf
from PIL import Image
from reportlab.graphics import renderPDF
from svglib import svglib
from tqdm import tqdm

IMG = Path("img/pepe.svg")
START_X = 115
START_Y = 790
MAX_WIDTH = 560
MAX_HEIGHT = 520
DEBUG = False
PLATFORM = "android"

FRAME_SEGMENT_STEPS = 70
DRAW_SWIPE_SIZE = 100
LUMINOSITY_THRESHOLD = 200

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.INFO)

Swiper = importlib.import_module(f"platforms.{PLATFORM}.swiper").Swiper
SWIPER = Swiper()


@dataclass
class Borders:
    top: int
    bottom: int
    left: int
    right: int

    def __init__(self, points: Iterable[tuple[int, int]]) -> None:
        self.top = min(y for _, y in points)
        self.bottom = max(y for _, y in points)
        self.left = min(x for x, _ in points)
        self.right = max(x for x, _ in points)

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1


def make_scale_matrix(rect: pymupdf.Rect, max_width: int, max_height: int) -> pymupdf.Matrix:
    scale_factor = max_width / rect.width
    if int(rect.height * scale_factor) > max_height:
        scale_factor = max_height / rect.height

    return pymupdf.Matrix(scale_factor, scale_factor)


def svg2png(svg_path: Path, output_width: int, output_height: int) -> bytes:
    drawing = svglib.svg2rlg(path=svg_path.as_posix())
    pdf = renderPDF.drawToString(drawing)
    doc = pymupdf.Document(stream=pdf)
    page = doc.load_page(0)
    matrix = make_scale_matrix(page.rect, output_width, output_height)
    pix = page.get_pixmap(matrix=matrix, alpha=True)
    return pix.tobytes("png")


def load_black_pixels(svg_path: Path) -> Iterator[tuple[int, int]]:
    png_data = svg2png(svg_path, output_width=MAX_WIDTH, output_height=MAX_HEIGHT)
    img = Image.open(BytesIO(png_data)).convert("LA")
    for y in range(img.height):
        for x in range(img.width):
            pixel = img.getpixel((x, y))
            assert isinstance(pixel, tuple)
            luminosity, alpha = pixel
            if alpha > 0 and luminosity < LUMINOSITY_THRESHOLD:
                yield (x, y)


def save_black_pixels(black_pixels: Iterable[tuple[int, int]], bmp_path: Path) -> None:
    borders = Borders(black_pixels)

    img = Image.new("RGB", (borders.width, borders.height), color="white")
    for x, y in black_pixels:
        img.putpixel((x - borders.left, y - borders.top), (0, 0, 0))
    img.save(bmp_path)


def find_contours(black_pixels: set[tuple[int, int]], sequence_length: int) -> Iterator[list[tuple[int, int]]]:
    borders = Borders(black_pixels)

    mask = np.zeros((borders.height, borders.width), dtype=np.uint8)
    for x, y in black_pixels:
        mask[y - borders.top, x - borders.left] = 255

    contours_raw, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for contour_np in contours_raw:
        relative_points = contour_np.squeeze(axis=1).tolist()
        absolute_points = [(point[0] + borders.left, point[1] + borders.top) for point in relative_points]
        contour_points = [tuple(point) for point in absolute_points]

        num_contour_points = len(contour_points)
        if num_contour_points == 0:
            continue

        num_chunks = max(1, round(num_contour_points / sequence_length))
        contour_points_np = np.array(contour_points, dtype=object)
        for chunk_np in np.array_split(contour_points_np, num_chunks):
            yield [tuple(point) for point in chunk_np.tolist()]


def save_contours(contours: list[list[tuple[int, int]]], bmp_path: Path) -> None:
    borders = Borders(point for contour in contours for point in contour)

    contour_img = np.full((borders.height, borders.width, 3), 255, dtype=np.uint8)

    contours_np = []
    for contour in contours:
        adjusted_contour = [(p[0] - borders.left, p[1] - borders.top) for p in contour]
        contours_np.append(np.array(adjusted_contour, dtype=np.int32).reshape((-1, 1, 2)))

    cv2.drawContours(contour_img, contours_np, -1, (0, 0, 0), thickness=1)
    cv2.imwrite(bmp_path.as_posix(), contour_img)


def horisontal_align_left(pixels: Iterable[tuple[int, int]]) -> Iterator[tuple[int, int]]:
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


def find_content_frame(black_pixels: Iterable[tuple[int, int]]) -> Iterator[tuple[int, int]]:
    borders = Borders(black_pixels)

    horizontal_step = max(1, borders.width // FRAME_SEGMENT_STEPS)
    vertical_step = max(1, borders.height // FRAME_SEGMENT_STEPS)

    for x in range(borders.left, borders.right + 1, horizontal_step):
        yield (x, borders.top)
    yield (borders.right, borders.top)

    for y in range(borders.top, borders.bottom + 1, vertical_step):
        yield (borders.right, y)
    yield (borders.right, borders.bottom)

    for x in range(borders.right, borders.left - 1, -horizontal_step):
        yield (x, borders.bottom)
    yield (borders.left, borders.bottom)

    for y in range(borders.bottom, borders.top - 1, -vertical_step):
        yield (borders.left, y)
    yield (borders.left, borders.top)


def swipe(pixels: Iterator[tuple[int, int]]) -> None:
    SWIPER.swipe((x + START_X, y + START_Y) for x, y in pixels)


def main() -> None:
    workdir = Path(__file__).parent
    svg_path = IMG
    if not svg_path.absolute():
        svg_path = workdir / IMG
    black_pixels = set(horisontal_align_left(list(load_black_pixels(svg_path))))
    contours = list(find_contours(black_pixels, DRAW_SWIPE_SIZE))
    LOGGER.info(f"Loaded {len(black_pixels)} black pixels from {svg_path}")

    if DEBUG:
        black_pixels_path = workdir / "debug" / "black_pixels.bmp"
        save_black_pixels(black_pixels, black_pixels_path)
        LOGGER.info(f"Saved black pixels to {black_pixels_path}")

        contours_path = workdir / "debug" / "contours.bmp"
        contour_pixels = [pixel for contour in contours for pixel in contour]
        save_black_pixels(contour_pixels, contours_path)
        LOGGER.info(f"Saved contours to {contours_path}")

    if DEBUG:
        swipe(find_content_frame(black_pixels))
        swipe(find_content_frame([(0, 0), (MAX_WIDTH, 0), (0, MAX_HEIGHT)]))

    unprocessed_pixels = set(black_pixels)
    pbar = tqdm(total=len(unprocessed_pixels), desc="Drawing")

    for contour in contours:
        swipe(contour)

        old_unprocessed_pixels_len = len(unprocessed_pixels)
        unprocessed_pixels.difference_update(contour)
        new_unprocessed_pixels_len = len(unprocessed_pixels)
        pbar.update(old_unprocessed_pixels_len - new_unprocessed_pixels_len)

    while unprocessed_pixels:  # pylint: disable=while-used
        connected_pixels = list(find_connected_pixels(black_pixels, unprocessed_pixels, DRAW_SWIPE_SIZE))
        swipe(connected_pixels)

        old_unprocessed_pixels_len = len(unprocessed_pixels)
        unprocessed_pixels.difference_update(connected_pixels)
        new_unprocessed_pixels_len = len(unprocessed_pixels)
        pbar.update(old_unprocessed_pixels_len - new_unprocessed_pixels_len)
    pbar.close()


if __name__ == "__main__":
    main()
