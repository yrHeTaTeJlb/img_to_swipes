import atexit
from functools import lru_cache
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from src.geometry import Polygon

from src.config import current_config


@lru_cache
def _install_target_platform_dependencies() -> None:
    config = current_config()
    config.target_platform.install_dependencies()


@lru_cache
def _start_target_platform_service() -> None:
    config = current_config()
    atexit.register(config.target_platform.stop_service)
    config.target_platform.start_service()


class Swiper:
    def __init__(self, duration: int) -> None:
        _install_target_platform_dependencies()
        _start_target_platform_service()

        config = current_config()
        driver = config.target_platform.make_driver()
        self._actions = ActionChains(driver, duration=duration)
        touch_input = PointerInput(interaction.POINTER_TOUCH, 'touch')
        self._actions.w3c_actions = ActionBuilder(driver, mouse=touch_input, duration=duration)

    def swipe(self, polygon: Polygon) -> None:
        if len(polygon.points) <= 1:
            return

        start = polygon.points[0]
        self._actions.w3c_actions.pointer_action.move_to_location(start.x, start.y)
        self._actions.w3c_actions.pointer_action.pointer_down()
        for point in polygon.points:
            self._actions.w3c_actions.pointer_action.move_to_location(point.x, point.y)
        self._actions.w3c_actions.pointer_action.release()
        self._actions.perform()
