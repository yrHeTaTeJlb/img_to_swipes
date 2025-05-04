from itertools import starmap
from typing import Iterable

from com.dtmilano.android.viewclient import ViewClient
from culebratester_client.models import Point


class Swiper:
    def __init__(self) -> None:
        self._view_client: ViewClient = ViewClient(*ViewClient.connectToDeviceOrExit(), useuiautomatorhelper=True)

    def swipe(self, points: Iterable[tuple[int, int]]) -> None:
        segments = list(starmap(Point, points))
        self._view_client.uiAutomatorHelper.ui_device.swipe(segments=segments, segment_steps=2)
