import importlib
import sys
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any

import toml
from nodejs import node
from src.geometry import Point, Rect

from src.target_platforms.target_platform import ITargetPlatform


class HostPlatform(Enum):
    windows = auto()
    linux = auto()
    darwin = auto()


class Config:
    def __init__(self) -> None:
        self._root_dir: Path = Path(sys.argv[0]).parent

        self._config_path = self._root_dir / "config.toml"
        config_dict = toml.load(self.config_path)

        self._host_platform: HostPlatform = self._find_host_platform()
        self._target_platform: ITargetPlatform = self._find_target_platform(config_dict)
        self._artifacts_dir: Path = self.root_dir / "artifacts"
        self._node_path: Path = Path(node.path)
        self._npm_path: Path = self._node_path.parent / "npm.cmd"
        self._image_path: Path = self._find_image_path(config_dict)
        self._draw_canvas_rect: bool = self._find_draw_canvas_rect(config_dict)
        self._draw_image_rect: bool = self._find_draw_image_rect(config_dict)
        self._draw_content_rect: bool = self._find_draw_content_rect(config_dict)
        self._luminosity_threshold: int = self._find_luminosity_threshold(config_dict)
        self._canvas_rect: Rect = self._find_canvas_rect(config_dict)
        self._swipe_length: int = self._find_swipe_length(config_dict)
        self._swipe_duration: int = self._find_swipe_duration(config_dict)

        self._artifacts_dir.mkdir(exist_ok=True)

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def swipe_duration(self) -> int:
        return self._swipe_duration

    @property
    def swipe_length(self) -> int:
        return self._swipe_length

    @property
    def canvas_rect(self) -> Rect:
        return self._canvas_rect

    @property
    def luminosity_threshold(self) -> int:
        return self._luminosity_threshold

    @property
    def node_path(self) -> Path:
        return self._node_path

    @property
    def npm_path(self) -> Path:
        return self._npm_path

    @property
    def target_platform(self) -> ITargetPlatform:
        return self._target_platform

    @property
    def host_platform(self) -> HostPlatform:
        return self._host_platform

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    @property
    def image_path(self) -> Path:
        return self._image_path

    @property
    def artifacts_dir(self) -> Path:
        return self._artifacts_dir

    @property
    def draw_canvas_rect(self) -> bool:
        return self._draw_canvas_rect

    @property
    def draw_image_rect(self) -> bool:
        return self._draw_image_rect

    @property
    def draw_content_rect(self) -> bool:
        return self._draw_content_rect

    def _find_host_platform(self) -> HostPlatform:
        if sys.platform.startswith("linux"):
            return HostPlatform.linux

        if sys.platform == "darwin":
            return HostPlatform.darwin

        if sys.platform in {"win32", "cygwin", "msys"}:
            return HostPlatform.windows

        raise ValueError(f"Unsupported platform: {sys.platform}")

    def _find_target_platform(self, config_dict: dict[str, Any]) -> ITargetPlatform:
        if "target_platform" not in config_dict:
            raise ValueError("target_platform not specified in config.toml")

        target_platform_name = config_dict["target_platform"]
        if not isinstance(target_platform_name, str):
            raise TypeError("target_platform must be a string")

        platform_module = importlib.import_module(f"src.target_platforms.{target_platform_name}.target_platform")

        target_platform = platform_module.TargetPlatform()
        assert isinstance(target_platform, ITargetPlatform)

        return target_platform

    def _find_image_path(self, config_dict: dict[str, Any]) -> Path:
        if "image_path" not in config_dict:
            raise ValueError("image_path not specified in config.toml")

        path = config_dict["image_path"]
        if not isinstance(path, str):
            raise TypeError("image_path must be a string")

        path = Path(path)
        if not path.is_absolute():
            path = self.root_dir / path

        return path

    def _find_draw_canvas_rect(self, config_dict: dict[str, Any]) -> bool:
        draw_canvas_rect = config_dict.get("draw_canvas_rect", False)
        if not isinstance(draw_canvas_rect, bool):
            raise TypeError("draw_canvas_rect must be a boolean")

        return draw_canvas_rect

    def _find_draw_image_rect(self, config_dict: dict[str, Any]) -> bool:
        draw_image_rect = config_dict.get("draw_image_rect", False)
        if not isinstance(draw_image_rect, bool):
            raise TypeError("draw_image_rect must be a boolean")

        return draw_image_rect

    def _find_draw_content_rect(self, config_dict: dict[str, Any]) -> bool:
        draw_content_rect = config_dict.get("draw_content_rect", False)
        if not isinstance(draw_content_rect, bool):
            raise TypeError("draw_content_rect must be a boolean")

        return draw_content_rect

    def _find_luminosity_threshold(self, config_dict: dict[str, Any]) -> int:
        luminosity_threshold = config_dict.get("luminosity_threshold", 200)
        if not isinstance(luminosity_threshold, int):
            raise TypeError("luminosity_threshold must be an integer")

        return luminosity_threshold

    def _find_canvas_rect(self, config_dict: dict[str, Any]) -> Rect:
        if "canvas_x" not in config_dict:
            raise ValueError("canvas_x not specified in config.toml")
        x = config_dict["canvas_x"]

        if "canvas_y" not in config_dict:
            raise ValueError("canvas_y not specified in config.toml")
        y = config_dict["canvas_y"]

        if "canvas_width" not in config_dict:
            raise ValueError("canvas_width not specified in config.toml")
        width = config_dict["canvas_width"]

        if "canvas_height" not in config_dict:
            raise ValueError("canvas_height not specified in config.toml")
        height = config_dict["canvas_height"]

        return Rect(Point(x, y), Point(x + width, y + height))

    def _find_swipe_length(self, config_dict: dict[str, Any]) -> int:
        swipe_length = config_dict.get("swipe_length", 50)
        if not isinstance(swipe_length, int):
            raise TypeError("swipe_length must be an integer")

        return swipe_length

    def _find_swipe_duration(self, config_dict: dict[str, Any]) -> int:
        swipe_duration = config_dict.get("swipe_duration", 20)
        if not isinstance(swipe_duration, int):
            raise TypeError("swipe_duration must be an integer")

        return swipe_duration


@lru_cache
def current_config() -> Config:
    return Config()
