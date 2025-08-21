from __future__ import annotations

import colorsys
from math import ceil
from typing import Iterator

from tqdm import tqdm

from src.config import current_config
from src.geometry import Point, Rect
from src.image import Image
from src.log import logger
from src.swiper import Swiper


def log_config() -> None:
    config = current_config()

    logger.info(f"Config file: {config.config_path}:")
    logger.info(f"Host platform: {config.host_platform.name}")
    logger.info(f"Root dir: {config.root_dir}")
    logger.info(f"Artifacts dir: {config.artifacts_dir}")
    logger.info(f"Node path: {config.node_path}")
    logger.info(f"Npm path: {config.npm_path}")
    logger.info(f"Image path: {config.image_path}")
    logger.info(f"Draw canvas bounding rect: {config.draw_canvas_rect}")
    logger.info(f"Draw image bounding rect: {config.draw_image_rect}")
    logger.info(f"Draw content bounding rect: {config.draw_content_rect}")
    logger.info(f"Maximum luminosity: {config.max_luminosity}")
    logger.info(f"Canvas rect: {config.canvas_rect}")
    logger.info(f"Swipe length: {config.swipe_length}")
    logger.info(f"Swipe duration(ms): {config.swipe_duration}")


def load_image() -> Image:
    config = current_config()

    logger.info(f"Loading image {config.image_path}...")
    image = Image.from_file(
        config.image_path,
        config.canvas_rect.size.width,
        config.canvas_rect.size.height,
        config.swipe_length,
        config.max_luminosity,
    )
    logger.info(f"Loaded {len(image.pixels)} black pixels({len(image.strokes)} strokes) from {config.image_path}")
    return image


def save_pixels(image: Image) -> None:
    config = current_config()

    black_pixels_path = config.artifacts_dir / "pixels.bmp"
    image.to_pil_image().save(black_pixels_path)
    logger.info(f"Saved black pixels to {black_pixels_path}")


def save_strokes(image: Image) -> None:
    config = current_config()

    palette_size = 50
    palette = []
    hue_step = 1 / palette_size
    for i in range(palette_size):
        red, green, blue = colorsys.hsv_to_rgb(i * hue_step, 1, 1)
        palette.append((int(red * 255), int(green * 255), int(blue * 255)))

    strokes_path = config.artifacts_dir / "strokes.bmp"
    image.to_pil_image(palette).save(strokes_path)
    logger.info(f"Saved strokes to {strokes_path}")


def make_image_queue(image: Image) -> Iterator[Image]:
    config = current_config()

    rect_lerp_step_count = ceil(config.swipe_length / 4)
    if config.draw_content_rect:
        yield Image.from_strokes([image.content_bounding_rect.to_polygon().lerp(rect_lerp_step_count)])

    if config.draw_image_rect:
        image_rect = Rect(Point(0, 0), Point(image.size.width, image.size.height))
        yield Image.from_strokes([image_rect.to_polygon().lerp(rect_lerp_step_count)])

    if config.draw_canvas_rect:
        canvas_rect = Rect(Point(0, 0), Point(config.canvas_rect.size.width, config.canvas_rect.size.height))
        yield Image.from_strokes([canvas_rect.to_polygon().lerp(rect_lerp_step_count)])

    yield image


def draw_images(images: list[Image]) -> None:
    config = current_config()

    swiper = Swiper(config.swipe_duration)
    total_stroke_count = sum(len(image.strokes) for image in images)
    with tqdm(total=total_stroke_count, smoothing=1) as pbar:
        for image in images:
            for stroke in image.strokes:
                canvas_stroke = stroke.offset(config.canvas_rect.left, config.canvas_rect.top)
                swiper.swipe(canvas_stroke)
                pbar.update()


def main() -> None:
    log_config()

    image = load_image()
    save_pixels(image)
    save_strokes(image)

    images = list(make_image_queue(image))
    draw_images(images)
