import os
from pathlib import Path
from typing import TextIO

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import AppiumService

from src.config import current_config
from src.log import logger
from src.target_platforms.target_platform import ITargetPlatform
from src.nodejs_utils import install_appium, install_appium_driver


class TargetPlatform(ITargetPlatform):
    def __init__(self) -> None:
        self._appium_service: AppiumService = AppiumService()
        self._appium_service_log: TextIO | None = None

    def install_dependencies(self) -> None:
        install_appium()
        install_appium_driver("appium-uiautomator2-driver@4")

    def start_service(self) -> None:
        if self._appium_service.is_running:
            return

        config = current_config()

        if not self._appium_service_log:
            self._appium_service_log = open(config.artifacts_dir / "appium.log", "w", encoding='utf-8')

        env = os.environ.copy()
        env["ANDROID_HOME"] = (config.platform_tools_path / "android").as_posix()
        env["PATH"] = os.pathsep.join([env.get("PATH", ""), config.node_path.parent.as_posix()])

        logger.info("Starting Appium service for Android...")
        self._appium_service.start(
            node=config.node_path,
            npm=config.npm_path,
            env=env,
            stdout=self._appium_service_log,
            stderr=self._appium_service_log,
            timeout_ms=120000,
        )
        logger.info("Appium service for Android started successfully")

    def stop_service(self) -> None:
        logger.info("Stopping Appium service for Android...")
        if self._appium_service_log:
            self._appium_service_log.close()
            self._appium_service_log = None

        if self._appium_service.is_running:
            self._appium_service.stop()
        logger.info("Appium service for Android stopped successfully")

    def make_driver(self) -> webdriver.Remote:
        return webdriver.Remote(options=UiAutomator2Options())
