from __future__ import annotations

import colorsys
from itertools import cycle
from logging import INFO, FileHandler
from math import ceil
from typing import Iterator

from PIL.Image import new as pil_new
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from tqdm import tqdm
from wakepy import keep

from src import config
from src.geometry import Point, Polygon, Rect, points_to_polygons, polygons_bounding_rect
from src.image import Image
from src.log import logger
from src.swiper import Swiper


def log_config() -> None:
    logger.info(f"Root dir: {config.root_dir()}")
    logger.info(f"Config file: {config.config_path()}:")
    logger.info(f"Host platform: {config.host_platform().name}")
    logger.info(f"Platform tools dir: {config.platform_tools_path()}")
    logger.info(f"NodeJS path: {config.nodejs_path()}")
    logger.info(f"Target platform: {config.target_platform().name}")
    logger.info(f"Artifacts dir: {config.artifacts_dir()}")
    logger.info(f"Image path: {config.image_path()}")
    logger.info(f"Draw canvas bounding rect: {config.draw_canvas_rect()}")
    logger.info(f"Draw image bounding rect: {config.draw_image_rect()}")
    logger.info(f"Draw content bounding rect: {config.draw_content_rect()}")
    logger.info(f"Maximum luminosity: {config.max_luminosity()}")
    logger.info(f"Canvas rect: {config.canvas_rect()}")
    logger.info(f"Swipe length: {config.swipe_length()}")
    logger.info(f"Swipe duration(ms): {config.swipe_duration()}")


def load_image() -> Image:
    logger.info(f"Loading image {config.image_path()}...")
    image = Image.from_file(
        config.image_path(),
        config.canvas_rect().size.width,
        config.canvas_rect().size.height,
        config.max_luminosity(),
    )
    logger.info(f"Loaded {len(image.pixels)} black pixels from {config.image_path()}")
    return image


def save_image(image: Image) -> None:
    black_pixels_path = config.artifacts_dir() / "pixels.bmp"
    image.to_pil_image().save(black_pixels_path)
    logger.info(f"Saved black pixels to {black_pixels_path}")


def make_palette(size: int) -> Iterator[tuple[int, int, int]]:
    palette = []
    hue_step = 1 / size
    for i in range(size):
        red, green, blue = colorsys.hsv_to_rgb(i * hue_step, 1, 1)
        palette.append((int(red * 255), int(green * 255), int(blue * 255)))

    return cycle(palette)


def save_swipe_image(swipes: list[Polygon]) -> None:
    palette = make_palette(50)

    bounding_rect = polygons_bounding_rect(swipes)
    pil_image = pil_new("RGB", (bounding_rect.size.width, bounding_rect.size.height), color="white")

    for swipe in swipes:
        image_swipe = swipe.offset(-bounding_rect.left, -bounding_rect.top)
        color = next(palette)
        for pixel in image_swipe.points:
            pil_image.putpixel((pixel.x, pixel.y), color)

    swipes_path = config.artifacts_dir() / "swipes.bmp"
    pil_image.save(swipes_path)
    logger.info(f"Saved swipes to {swipes_path}")


def make_swipe_queue(image: Image) -> Iterator[Polygon]:
    rect_lerp_step_count = ceil(config.swipe_length() / 4)

    if config.draw_canvas_rect():
        canvas_size = config.canvas_rect().size
        canvas_rect = Rect(Point(0, 0), Point(canvas_size.width, canvas_size.height))
        yield canvas_rect.to_polygon().lerp(rect_lerp_step_count)

    if config.draw_image_rect():
        image_rect = Rect(Point(0, 0), Point(image.size.width, image.size.height))
        yield image_rect.to_polygon().lerp(rect_lerp_step_count)

    if config.draw_content_rect():
        yield image.content_bounding_rect.to_polygon().lerp(rect_lerp_step_count)

    unique_pixels = set(image.pixels)
    processed_pixels: set[Point] = set()
    with tqdm(total=len(unique_pixels), smoothing=1, colour="green", desc="Preparing swipes") as pbar:
        for polygon in points_to_polygons(unique_pixels, config.swipe_length()):
            old_count = len(processed_pixels)
            processed_pixels.update(polygon.points)
            new_count = len(processed_pixels)
            pbar.update(new_count - old_count)
            yield polygon


def perform_swipes(swipes: list[Polygon]) -> None:
    swiper = Swiper(config.swipe_duration())
    dx = config.canvas_rect().left
    dy = config.canvas_rect().top
    for swipe in tqdm(swipes, smoothing=1, colour="green", desc="Performing swipes"):
        swiper.swipe(swipe.offset(dx, dy))


def configure_logging() -> None:
    logger.setLevel(INFO)
    logger.addHandler(RichHandler(show_time=False, show_path=False, highlighter=NullHighlighter()))
    logger.addHandler(FileHandler(config.artifacts_dir() / "img_to_swipes.log", mode="w", encoding="utf-8"))


def main() -> None:
    try:
        with keep.running():
            configure_logging()

            log_config()

            image = load_image()
            save_image(image)

            swipes = list(make_swipe_queue(image))
            save_swipe_image(swipes)

            perform_swipes(swipes)
    except Exception as e:
        logger.exception(e)
        raise
