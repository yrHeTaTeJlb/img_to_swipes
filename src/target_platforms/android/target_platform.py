import os
import subprocess
from pathlib import Path
from time import sleep
from typing import TextIO

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import MAIN_SCRIPT_PATH, AppiumService
from selenium.common.exceptions import WebDriverException

from src import config
from src.log import logger
from src.nodejs_utils import install_appium, install_uiautomator, modules_root
from src.target_platforms.target_platform import ITargetPlatform


class TargetPlatform(ITargetPlatform):
    def __init__(self) -> None:
        self._appium_service: AppiumService = AppiumService()
        self._appium_service_log: TextIO | None = None

    @property
    def name(self) -> str:
        return "Android"

    def install_dependencies(self) -> None:
        install_appium()
        install_uiautomator()

    def start_service(self) -> None:
        if self._appium_service.is_running:
            return

        if not self._appium_service_log:
            self._appium_service_log = open(config.artifacts_dir() / "appium.log", "w", encoding='utf-8')

        env = os.environ.copy()
        env["ANDROID_HOME"] = (config.platform_tools_path() / "android").as_posix()
        env["PATH"] = os.pathsep.join([env.get("PATH", ""), config.nodejs_path().parent.as_posix()])

        main_script = modules_root() / MAIN_SCRIPT_PATH

        logger.info("Starting Appium service for Android...")
        self._appium_service.start(
            node=config.nodejs_path(),
            npm="npm",
            env=env,
            stdout=self._appium_service_log,
            stderr=self._appium_service_log,
            timeout_ms=120000,
            main_script=main_script,
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
        attempt_count = 5
        attempt_delay = 10
        for attempt in range(1, attempt_count + 1):
            logger.info(f"Creating Appium driver for Android (attempt {attempt}/{attempt_count})...")
            try:
                driver = webdriver.Remote(options=UiAutomator2Options())
                logger.info("Appium driver for Android created successfully")
                return driver
            except WebDriverException as e:
                logger.warning(self._make_friendly_error_message(e))
                if attempt < attempt_count:
                    logger.info(f"Killing adb server and retrying in {attempt_delay} seconds...")
                    sleep(attempt_delay)
                    self._kill_adb()
                else:
                    logger.error(
                        "Exceeded maximum number of attempts to create Appium driver for Android. "
                        f"Disconnect your device, enable USB debugging, execute '{self._adb} kill-server', "
                        "and then reconnect the device."
                    )
                    raise

        raise RuntimeError("Failed to create Appium driver for Android")

    @property
    def _adb(self) -> Path:
        return config.platform_tools_path() / "android" / "adb"

    def _kill_adb(self) -> None:
        subprocess.run([self._adb, "kill-server"], check=False)

    def _make_friendly_error_message(self, exception: WebDriverException) -> str:
        error_message = exception.msg or ""

        if "device unauthorized" in error_message:
            return "Device unauthorized. Check for a confirmation dialog on your device"
        if "Could not find a connected Android device" in error_message:
            return "Device not found. Make sure your device is connected and USB debugging is enabled"

        return f"Failed to create Appium driver for Android: {error_message}"
