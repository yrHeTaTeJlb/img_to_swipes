import importlib
import sys
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

import toml
from nodejs import node
from src.geometry import Point, Rect

from src.target_platforms.target_platform import ITargetPlatform


class HostPlatform(Enum):
    windows = auto()
    linux = auto()
    darwin = auto()


T = TypeVar("T")


class Config:
    def __init__(self) -> None:
        self._root_dir: Path = Path(sys.argv[0]).parent.absolute()
        self._config_path = self._find_config_path()
        self._host_platform: HostPlatform = self._find_host_platform()
        self._platform_tools_path: Path = self._find_platform_tools_path()
        self._node_path: Path = self._find_node_path()
        self._npm_path: Path = self._find_npm_path()

        config_dict = toml.load(self.config_path)
        self._target_platform: ITargetPlatform = self._find_target_platform(config_dict)
        self._artifacts_dir: Path = self._find_artifacts_dir(config_dict)
        self._image_path: Path = self._find_image_path(config_dict)
        self._draw_canvas_rect: bool = self._find_draw_canvas_rect(config_dict)
        self._draw_image_rect: bool = self._find_draw_image_rect(config_dict)
        self._draw_content_rect: bool = self._find_draw_content_rect(config_dict)
        self._max_luminosity: int = self._find_max_luminosity(config_dict)
        self._canvas_rect: Rect = self._find_canvas_rect(config_dict)
        self._swipe_length: int = self._find_swipe_length(config_dict)
        self._swipe_duration: int = self._find_swipe_duration(config_dict)

        self._artifacts_dir.mkdir(exist_ok=True)

    @property
    def platform_tools_path(self) -> Path:
        return self._platform_tools_path

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
    def max_luminosity(self) -> int:
        return self._max_luminosity

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

    @staticmethod
    def _find_key(config_dict: dict[str, Any], category: str, key: str, key_type: type[T], default: T | None) -> T:
        category_dict = config_dict.get(category)
        if category_dict is None:
            if default is not None:
                return default
            raise ValueError(f"Category {category} not specified in config.toml")

        if not isinstance(category_dict, dict):
            raise TypeError(f"\"{category}\" must be a category")

        key_value = category_dict.get(key)
        if key_value is None:
            if default is not None:
                return default
            raise ValueError(f"Key {key} not specified in {category} category of config.toml")

        if not isinstance(key_value, key_type):
            raise TypeError(f"Key {key} in {category} category must be of type {key_type.__name__}")

        return key_value

    def _find_config_path(self) -> Path:
        return self._root_dir / "config.toml"

    def _find_node_path(self) -> Path:
        return Path(node.path)

    def _find_artifacts_dir(self, config_dict: dict[str, Any]) -> Path:
        path_str = self._find_key(config_dict, "artifacts", "path", str, None)
        path = Path(path_str)
        if not path.is_absolute():
            path = self.root_dir / path

        return path

    def _find_npm_path(self) -> Path:
        if self.host_platform == HostPlatform.linux:
            return self.platform_tools_path / "nodejs" / "npm.sh"

        if self.host_platform == HostPlatform.darwin:
            return self.platform_tools_path / "nodejs" / "npm.sh"

        if self.host_platform == HostPlatform.windows:
            return self.platform_tools_path / "nodejs" / "npm.cmd"

        raise ValueError(f"Unsupported host platform: {self.host_platform.name}")

    def _find_host_platform(self) -> HostPlatform:
        if sys.platform.startswith("linux"):
            return HostPlatform.linux

        if sys.platform == "darwin":
            return HostPlatform.darwin

        if sys.platform in {"win32", "cygwin", "msys"}:
            return HostPlatform.windows

        raise ValueError(f"Unsupported platform: {sys.platform}")

    def _find_platform_tools_path(self) -> Path:
        return self.root_dir / "platform_tools" / self.host_platform.name

    def _find_target_platform(self, config_dict: dict[str, Any]) -> ITargetPlatform:
        target_platform_name = self._find_key(config_dict, "target_platform", "name", str, None)
        platform_module = importlib.import_module(f"src.target_platforms.{target_platform_name}.target_platform")
        target_platform = platform_module.TargetPlatform()
        assert isinstance(target_platform, ITargetPlatform)

        return target_platform

    def _find_image_path(self, config_dict: dict[str, Any]) -> Path:
        path_str = self._find_key(config_dict, "image", "path", str, None)
        path = Path(path_str)
        if not path.is_absolute():
            path = self.root_dir / path

        return path

    def _find_draw_canvas_rect(self, config_dict: dict[str, Any]) -> bool:
        return self._find_key(config_dict, "debug", "draw_canvas_rect", bool, False)

    def _find_draw_image_rect(self, config_dict: dict[str, Any]) -> bool:
        return self._find_key(config_dict, "debug", "draw_image_rect", bool, False)

    def _find_draw_content_rect(self, config_dict: dict[str, Any]) -> bool:
        return self._find_key(config_dict, "debug", "draw_content_rect", bool, False)

    def _find_max_luminosity(self, config_dict: dict[str, Any]) -> int:
        return self._find_key(config_dict, "image", "max_luminosity", int, 200)

    def _find_canvas_rect(self, config_dict: dict[str, Any]) -> Rect:
        x = self._find_key(config_dict, "canvas", "x", int, None)
        y = self._find_key(config_dict, "canvas", "y", int, None)
        width = self._find_key(config_dict, "canvas", "width", int, None)
        height = self._find_key(config_dict, "canvas", "height", int, None)

        return Rect(Point(x, y), Point(x + width, y + height))

    def _find_swipe_length(self, config_dict: dict[str, Any]) -> int:
        return self._find_key(config_dict, "swipe", "swipe_length", int, 200)

    def _find_swipe_duration(self, config_dict: dict[str, Any]) -> int:
        return self._find_key(config_dict, "swipe", "swipe_duration", int, 1)


@lru_cache
def current_config() -> Config:
    return Config()
