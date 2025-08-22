from __future__ import annotations

import colorsys
from logging import INFO, FileHandler
from math import ceil
from wakepy import keep
from typing import Iterator

from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from tqdm import tqdm

from src import config
from src.geometry import Point, Polygon, Rect
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
        config.swipe_length(),
        config.max_luminosity(),
    )
    logger.info(f"Loaded {len(image.pixels)} black pixels({len(image.strokes)} strokes) from {config.image_path}")
    return image


def save_pixels(image: Image) -> None:
    black_pixels_path = config.artifacts_dir() / "pixels.bmp"
    image.to_pil_image().save(black_pixels_path)
    logger.info(f"Saved black pixels to {black_pixels_path}")


def save_strokes(image: Image) -> None:
    palette_size = 50
    palette = []
    hue_step = 1 / palette_size
    for i in range(palette_size):
        red, green, blue = colorsys.hsv_to_rgb(i * hue_step, 1, 1)
        palette.append((int(red * 255), int(green * 255), int(blue * 255)))

    strokes_path = config.artifacts_dir() / "strokes.bmp"
    image.to_pil_image(palette).save(strokes_path)
    logger.info(f"Saved strokes to {strokes_path}")


def make_image_queue(image: Image) -> Iterator[Image]:
    rect_lerp_step_count = ceil(config.swipe_length() / 4)

    if config.draw_canvas_rect():
        canvas_size = config.canvas_rect().size
        canvas_rect = Rect(Point(0, 0), Point(canvas_size.width, canvas_size.height))
        yield Image.from_strokes([canvas_rect.to_polygon().lerp(rect_lerp_step_count)])

    if config.draw_image_rect():
        image_rect = Rect(Point(0, 0), Point(image.size.width, image.size.height))
        yield Image.from_strokes([image_rect.to_polygon().lerp(rect_lerp_step_count)])

    if config.draw_content_rect():
        yield Image.from_strokes([image.content_bounding_rect.to_polygon().lerp(rect_lerp_step_count)])

    yield image


def draw_images(images: list[Image]) -> None:
    swiper = Swiper(config.swipe_duration())
    strokes: list[Polygon] = [stroke for image in images for stroke in image.strokes]
    dx = config.canvas_rect().left
    dy = config.canvas_rect().top
    for stroke in tqdm(strokes, smoothing=1, colour="green"):
        swiper.swipe(stroke.offset(dx, dy))


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
            save_pixels(image)
            save_strokes(image)

            images = list(make_image_queue(image))
            draw_images(images)
    except Exception as e:
        logger.exception(e)
        raise
