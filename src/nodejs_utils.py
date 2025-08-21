from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache

from nodejs import npm

from src.config import current_config
from src.log import logger


@dataclass(frozen=True)
class Package:
    name: str
    version: str

    def __str__(self) -> str:
        return f"{self.name}@{self.version}"


@lru_cache
def find_installed_npm_packages() -> set[Package]:
    logger.info("Querying installed npm packages...")

    try:
        process = npm.run(["list", "--json"], capture_output=True, text=True, check=True)
    except Exception as e:
        raise RuntimeError("Failed to query installed npm packages") from e

    packages = set()
    output = json.loads(process.stdout)
    dependencies = output.get("dependencies", {})
    for package, info in dependencies.items():
        version = info.get("version", "unknown")
        packages.add(Package(package, version))

    logger.info(f"Found {len(packages)} installed npm packages")

    return set(packages)


def install_package(package_name: str, package_version: str) -> None:
    package = Package(package_name, package_version)
    if package in find_installed_npm_packages():
        logger.info(f"'{package}' is already installed")
        return

    logger.info(f"Installing '{package}'...")

    config = current_config()
    log_path = config.artifacts_dir / f"install_{package}.log"
    with open(log_path, "w", encoding='utf-8') as log_file:
        try:
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join([env.get("PATH", ""), config.node_path.parent.as_posix()])
            npm.run(["install", str(package)], stdout=log_file, stderr=log_file, check=True, env=env)
        except Exception as e:
            raise RuntimeError(f"Failed to install '{package}'. See {log_path} for details") from e

    logger.info("Appium installed successfully")


def install_appium() -> None:
    install_package("appium", "2.19.0")


def install_uiautomator() -> None:
    install_package("appium-uiautomator2-driver", "4.2.9")
