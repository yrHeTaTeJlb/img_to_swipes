from __future__ import annotations

import json
import os
from functools import lru_cache

from nodejs import npm

from src.config import current_config
from src.log import logger


@lru_cache
def find_installed_npm_packages() -> set[str]:
    logger.info("Querying installed npm packages...")

    try:
        process = npm.run(["list", "--json"], capture_output=True, text=True, check=True)
    except Exception as e:
        raise RuntimeError("Failed to query installed npm packages") from e

    output = json.loads(process.stdout)
    packages = list(output.get("dependencies", []))
    logger.info(f"Found {len(packages)} installed npm packages")

    return set(packages)


def install_appium() -> None:
    logger.info("Installing Appium...")
    if "appium" in find_installed_npm_packages():
        logger.info("Appium is already installed")
        return

    config = current_config()
    log_path = config.artifacts_dir / "install_appium.log"
    with open(log_path, "w", encoding='utf-8') as log_file:
        try:
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join([env.get("PATH", ""), config.node_path.parent.as_posix()])
            npm.run(["install", "appium@2"], stdout=log_file, stderr=log_file, check=True, env=env)
        except Exception as e:
            raise RuntimeError(f"Failed to install Appium. See {log_path} for details") from e

    logger.info("Appium installed successfully")


def install_appium_driver(driver_name: str) -> None:
    logger.info(f"Installing Appium driver '{driver_name}'...")
    if driver_name in find_installed_npm_packages():
        logger.info("Appium is already installed")
        return

    config = current_config()
    log_path = config.artifacts_dir / "install_appium_driver.log"
    with open(log_path, "w", encoding='utf-8') as log_file:
        try:
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join([env.get("PATH", ""), config.node_path.parent.as_posix()])
            npm.run(["install", driver_name], stdout=log_file, stderr=log_file, check=True, env=env)
        except Exception as e:
            raise RuntimeError(f"Failed to install Appium driver '{driver_name}'. See {log_path} for details") from e

    logger.info(f"Appium driver '{driver_name}' installed successfully")


