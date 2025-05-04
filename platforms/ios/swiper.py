from typing import Iterable

from appium import webdriver
from appium.options.ios import XCUITestOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput


class Swiper:
    def __init__(self) -> None:
        driver = webdriver.Remote(options=XCUITestOptions())

        self.actions = ActionChains(driver, duration=15)
        touch_input = PointerInput(interaction.POINTER_TOUCH, 'touch')
        self.actions.w3c_actions = ActionBuilder(driver, mouse=touch_input, duration=15)

    def swipe(self, points: Iterable[tuple[int, int]]) -> None:
        start = next(iter(points), None)
        if start is None:
            return

        self.actions.w3c_actions.pointer_action.move_to_location(start[0], start[1])
        self.actions.w3c_actions.pointer_action.pointer_down()
        for x, y in points:
            self.actions.w3c_actions.pointer_action.move_to_location(x, y)
        self.actions.w3c_actions.pointer_action.release()
        self.actions.perform()
