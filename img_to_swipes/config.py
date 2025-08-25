import importlib
import sys
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

import toml
from nodejs import node
from img_to_swipes.geometry import Point, Rect

from img_to_swipes.target_platforms.target_platform import ITargetPlatform


class HostPlatform(Enum):
    windows = auto()
    linux = auto()
    darwin = auto()


T = TypeVar("T")


@lru_cache
def _config_dict() -> dict[str, Any]:
    return toml.load(config_path())


@lru_cache
def _config_key(category: str, key: str, key_type: type[T], default: T | None) -> T:
    category_dict = _config_dict().get(category)
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


@lru_cache
def root_dir() -> Path:
    return Path(sys.argv[0]).parent.absolute()


@lru_cache
def config_path() -> Path:
    return root_dir() / "config.toml"


@lru_cache
def host_platform() -> HostPlatform:
    if sys.platform.startswith("linux"):
        return HostPlatform.linux

    if sys.platform == "darwin":
        return HostPlatform.darwin

    if sys.platform in {"win32", "cygwin", "msys"}:
        return HostPlatform.windows

    raise ValueError(f"Unsupported platform: {sys.platform}")


@lru_cache
def platform_tools_path() -> Path:
    return root_dir() / "platform_tools" / host_platform().name


@lru_cache
def nodejs_path() -> Path:
    return Path(node.path)


@lru_cache
def target_platform() -> ITargetPlatform:
    platform_name = _config_key("target_platform", "name", str, None)
    platform_module = importlib.import_module(f"img_to_swipes.target_platforms.{platform_name}.target_platform")
    platform = platform_module.TargetPlatform()
    assert isinstance(platform, ITargetPlatform)

    return platform


@lru_cache
def artifacts_dir() -> Path:
    path = root_dir() / "artifacts"
    path.mkdir(exist_ok=True)

    return path


@lru_cache
def image_path() -> Path:
    path_str = _config_key("image", "path", str, None)
    path = Path(path_str)
    if not path.is_absolute():
        path = root_dir() / path

    return path


@lru_cache
def draw_canvas_rect() -> bool:
    return _config_key("debug", "draw_canvas_rect", bool, False)


@lru_cache
def draw_image_rect() -> bool:
    return _config_key("debug", "draw_image_rect", bool, False)


@lru_cache
def draw_content_rect() -> bool:
    return _config_key("debug", "draw_content_rect", bool, False)


@lru_cache
def max_luminosity() -> int:
    value = _config_key("image", "max_luminosity", int, 200)
    if not (0 <= value <= 255):
        raise ValueError("Max luminosity must be between 0 and 255")

    return value


@lru_cache
def canvas_rect() -> Rect:
    x = _config_key("canvas", "x", int, None)
    y = _config_key("canvas", "y", int, None)

    width = _config_key("canvas", "width", int, None)
    if width <= 0:
        raise ValueError("Canvas width must be greater than 0")

    height = _config_key("canvas", "height", int, None)
    if height <= 0:
        raise ValueError("Canvas height must be greater than 0")

    return Rect(Point(x, y), Point(x + width, y + height))


@lru_cache
def swipe_length() -> int:
    value = _config_key("swipe", "length", int, 200)
    if value <= 0:
        raise ValueError("Swipe length must be a positive integer")

    return value


@lru_cache
def swipe_duration() -> int:
    value = _config_key("swipe", "duration", int, 1)
    if value <= 0:
        raise ValueError("Swipe duration must be a positive integer")

    return value


@lru_cache
def swipe_radius() -> int:
    value = _config_key("swipe", "radius", int, 2)
    if value <= 0:
        raise ValueError("Swipe radius must be a positive integer")

    return value
