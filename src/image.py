from __future__ import annotations

from io import BytesIO
from itertools import cycle
from pathlib import Path
from typing import Iterable

from PIL.Image import Image as PilImage
from PIL.Image import open as pil_open
from PIL.Image import new as pil_new
from PIL.Image import Resampling as PilResampling
import pymupdf
from reportlab.graphics import renderPDF
from svglib import svglib

from src.geometry import Point, Polygon, Rect, Size, bounding_rect, points_to_polygons, polygons_to_points


class Image:
    def __init__(self, strokes: Iterable[Polygon]) -> None:
        self._content_bounding_rect: Rect | None = None
        self._pixels: list[Point] | None = None
        self._strokes: list[Polygon] = list(strokes)

    @staticmethod
    def from_pixels(pixels: Iterable[Point], max_stroke_length: int) -> Image:
        unique_pixels = set(pixels)

        if len(unique_pixels) <= 1:
            return Image([Polygon(list(unique_pixels))])

        return Image(points_to_polygons(unique_pixels, max_stroke_length))

    @staticmethod
    def from_strokes(strokes: Iterable[Polygon]) -> Image:
        return Image(strokes)

    @staticmethod
    def from_pil_image(image: PilImage, max_stroke_length: int, max_luminosity: int) -> Image:
        black_pixels = []
        gray_image = image.convert("LA")
        for y in range(gray_image.height):
            for x in range(gray_image.width):
                pixel = gray_image.getpixel((x, y))
                assert isinstance(pixel, tuple)
                luminosity, alpha = pixel
                if alpha > 0 and luminosity < max_luminosity:
                    black_pixels.append(Point(x, y))

        return Image.from_pixels(black_pixels, max_stroke_length)

    @staticmethod
    def from_svg(
        svg_path: Path, max_width: int, max_height: int, max_stroke_length: int, max_luminosity: int
    ) -> Image:
        drawing = svglib.svg2rlg(path=svg_path.as_posix())
        pdf = renderPDF.drawToString(drawing)
        doc = pymupdf.Document(stream=pdf)
        page = doc.load_page(0)

        scale_factor = max_width / page.rect.width
        if int(page.rect.height * scale_factor) > max_height:
            scale_factor = max_height / page.rect.height

        matrix = pymupdf.Matrix(scale_factor, scale_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=True)
        png_data = pix.tobytes("png")
        with pil_open(BytesIO(png_data)) as pil_image:
            return Image.from_pil_image(pil_image, max_stroke_length, max_luminosity)

    @staticmethod
    def from_file(
        path: Path, max_width: int, max_height: int, max_stroke_length: int, max_luminosity: int
    ) -> Image:
        if path.suffix.lower() == ".svg":
            return Image._from_svg_file(path, max_width, max_height, max_stroke_length, max_luminosity)

        return Image._from_any_file(path, max_width, max_height, max_stroke_length, max_luminosity)

    @property
    def pixels(self) -> list[Point]:
        if self._pixels is None:
            self._pixels = list(polygons_to_points(self._strokes))

        return self._pixels

    @property
    def strokes(self) -> list[Polygon]:
        return self._strokes

    @property
    def size(self) -> Size:
        return Size(self.content_bounding_rect.right + 1, self.content_bounding_rect.bottom + 1)

    @property
    def content_bounding_rect(self) -> Rect:
        if self._content_bounding_rect is None:
            self._content_bounding_rect = bounding_rect(self.pixels)

        return self._content_bounding_rect

    def to_pil_image(self, palette: Iterable[tuple[int, int, int]] | None = None) -> PilImage:
        if palette is None:
            palette = [(0, 0, 0)]

        pil_image = pil_new("RGB", (self.size.width, self.size.height), color="white")
        cycled_palette = cycle(palette)
        for stroke in self.strokes:
            palette_color = next(cycled_palette)
            for pixel in stroke.points:
                pil_image.putpixel((pixel.x, pixel.y), palette_color)

        return pil_image

    @staticmethod
    def _from_any_file(
        path: Path, max_width: int, max_height: int, max_stroke_length: int, max_luminosity: int
    ) -> Image:
        with pil_open(path) as pil_image:
            if pil_image.width != max_width and pil_image.height != max_height:
                scale_factor = min(max_width / pil_image.width, max_height / pil_image.height)
                new_size = (int(pil_image.width * scale_factor), int(pil_image.height * scale_factor))
                pil_image.resize(new_size, resample=PilResampling.LANCZOS)

            return Image.from_pil_image(pil_image, max_stroke_length, max_luminosity)

    @staticmethod
    def _from_svg_file(
        path: Path, max_width: int, max_height: int, max_stroke_length: int, max_luminosity: int
    ) -> Image:
        drawing = svglib.svg2rlg(path.as_posix())
        pdf = renderPDF.drawToString(drawing)
        doc = pymupdf.Document(stream=pdf)
        page = doc.load_page(0)

        scale_factor = min(max_width / page.rect.width, max_height / page.rect.height)
        matrix = pymupdf.Matrix(scale_factor, scale_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=True)
        png_data = pix.tobytes("png")
        with pil_open(BytesIO(png_data)) as pil_image:
            return Image.from_pil_image(pil_image, max_stroke_length, max_luminosity)
