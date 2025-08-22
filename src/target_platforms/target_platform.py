from abc import ABC, abstractmethod

from appium import webdriver


class ITargetPlatform(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def install_dependencies(self) -> None:
        ...

    @abstractmethod
    def start_service(self) -> None:
        ...

    @abstractmethod
    def stop_service(self) -> None:
        ...

    @abstractmethod
    def make_driver(self) -> webdriver.Remote:
        ...
