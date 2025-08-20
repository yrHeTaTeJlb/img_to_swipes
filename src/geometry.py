from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import islice, repeat, starmap
from typing import Callable, Iterable, Iterator

import cv2
import numpy


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    @property
    def neighbors(self) -> Iterator[Point]:
        yield Point(self.x - 1, self.y)
        yield Point(self.x + 1, self.y)
        yield Point(self.x, self.y - 1)
        yield Point(self.x, self.y + 1)
        yield Point(self.x - 1, self.y - 1)
        yield Point(self.x - 1, self.y + 1)
        yield Point(self.x + 1, self.y - 1)
        yield Point(self.x + 1, self.y + 1)


@dataclass(frozen=True)
class Size:
    width: int
    height: int


@dataclass(frozen=True)
class Rect:
    top_left: Point
    bottom_right: Point

    @property
    def top(self) -> int:
        return self.top_left.y

    @property
    def bottom(self) -> int:
        return self.bottom_right.y

    @property
    def left(self) -> int:
        return self.top_left.x

    @property
    def right(self) -> int:
        return self.bottom_right.x

    @property
    def top_right(self) -> Point:
        return Point(self.right, self.top)

    @property
    def bottom_left(self) -> Point:
        return Point(self.left, self.bottom)

    @property
    def size(self) -> Size:
        return Size(self.right - self.left + 1, self.bottom - self.top + 1)

    def to_polygon(self) -> Polygon:
        return Polygon([self.top_left, self.top_right, self.bottom_right, self.bottom_left, self.top_left])


@dataclass(frozen=True)
class Polygon:
    points: list[Point]

    @property
    def bounding_rect(self) -> Rect:
        if not self.points:
            return Rect(Point(0, 0), Point(0, 0))

        min_x = min(point.x for point in self.points)
        min_y = min(point.y for point in self.points)
        max_x = max(point.x for point in self.points)
        max_y = max(point.y for point in self.points)

        return Rect(Point(min_x, min_y), Point(max_x, max_y))

    def offset(self, dx: int, dy: int) -> Polygon:
        return Polygon([Point(point.x + dx, point.y + dy) for point in self.points])

    def split(self, max_length: int) -> Iterator[Polygon]:
        if max_length <= 0:
            raise ValueError("Length must be greater than 0")

        for i in range(0, len(self.points), max_length):
            yield Polygon(self.points[i:i + max_length])

    def lerp(self, steps: int) -> Polygon:
        if steps < 0:
            raise ValueError("Steps must be non-negative")

        if len(self.points) <= 1 or steps == 0:
            return Polygon(self.points.copy())

        points_np = numpy.array([(point.x, point.y) for point in self.points])
        lerp_points_np: list[numpy.ndarray] = []
        for i in range(len(points_np) - 1):
            start_point_np = points_np[i]
            end_point_np = points_np[i + 1]
            lerp_segment_np = numpy.linspace(start_point_np, end_point_np, steps + 2)
            lerp_points_np.extend(lerp_segment_np)

        lerp_points = starmap(Point, numpy.round(lerp_points_np).astype(int).tolist())
        return Polygon(list(dict.fromkeys(lerp_points)))


def find_contours(points: Iterable[Point]) -> Iterator[Polygon]:
    unique_points = set(points)
    if not unique_points:
        return

    width = max(point.x for point in unique_points) + 1
    height = max(point.y for point in unique_points) + 1

    mask = numpy.zeros((height, width), dtype=numpy.uint8)
    for point in unique_points:
        mask[point.y, point.x] = 255

    contours_raw, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for contour_np in contours_raw:
        contour_points = contour_np.squeeze(axis=1).tolist()
        if not contour_points:
            continue

        yield Polygon(list(starmap(Point, contour_points)))


def find_path(start: Point, points: set[Point], max_length: int, predicate: Callable[[Point], bool]) -> Polygon | None:
    if max_length <= 0:
        raise ValueError("Max length must be greater than 0")

    if max_length == 1:
        if predicate(start):
            return Polygon([start])
        return None

    visited = set()
    queue = [[start]]

    while queue:
        current_path = queue.pop(0)
        last_point = current_path[-1]
        assert len(current_path) < max_length

        for neighbor in last_point.neighbors:
            if neighbor not in points:
                continue

            if neighbor in visited:
                continue

            if predicate(neighbor):
                current_path.append(neighbor)
                return Polygon(current_path)

            if len(current_path) == max_length - 1:
                continue

            new_path = current_path.copy()
            new_path.append(neighbor)
            queue.append(new_path)
            visited.add(neighbor)

    return None


class _PolygonGenerator:
    def __init__(self, points: set[Point], polygon_length: int) -> None:
        self._points: set[Point] = points
        self._polygon_length: int = polygon_length
        self._unvisited_points: set[Point] = points.copy()
        self._unvisited_contours: list[Polygon] | None = []

    def _next_contour(self) -> Polygon | None:
        while self._unvisited_contours is not None:
            while self._unvisited_contours:
                return self._unvisited_contours.pop()

            for contour in find_contours(self._unvisited_points):
                for short_contour in contour.split(self._polygon_length):
                    if len(short_contour.points) == self._polygon_length:
                        self._unvisited_contours.append(short_contour)

            if not self._unvisited_contours:
                self._unvisited_contours = None

        return None

    def __iter__(self) -> Iterator[Polygon]:
        return self

    def __next__(self) -> Polygon:
        if not self._unvisited_points:
            raise StopIteration

        polygon = self._next_contour() or self._next_random_polygon()
        self._unvisited_points.difference_update(polygon.points)

        return polygon

    def _next_random_polygon(self) -> Polygon:
        points = [next(iter(self._unvisited_points))]
        visit_count = Counter(points)

        def is_unvisited(point: Point) -> bool:
            return point in self._unvisited_points and point not in visit_count

        while len(points) < self._polygon_length:
            max_length = self._polygon_length - len(points)
            last_point = points[-1]
            tail = find_path(last_point, self._points, max_length, is_unvisited)
            if tail:
                visit_count.update(islice(tail.points, 1, None))
                points.extend(islice(tail.points, 1, None))
                continue

            first_point = points[0]
            head = find_path(first_point, self._points, max_length, is_unvisited)
            if head:
                visit_count.update(islice(head.points, 1, None))
                head.points.reverse()
                points, tail_points = head.points, points
                points.extend(islice(tail_points, 1, None))
                continue

            break

        while len(points) < self._polygon_length:
            last_point = points[-1]
            tail_neighbor = self._find_least_visited_neighbor(last_point, visit_count, self._points)
            if tail_neighbor:
                points.append(tail_neighbor)
                visit_count[tail_neighbor] += 1
                continue

            first_point = points[0]
            head_neighbor = self._find_least_visited_neighbor(first_point, visit_count, self._points)
            if head_neighbor:
                points.insert(0, head_neighbor)
                visit_count[head_neighbor] += 1
                continue

            break

        last_point = points[-1]
        pad = self._polygon_length - len(points)
        points.extend(islice(repeat(last_point), pad))

        return Polygon(points)

    def _find_least_visited_neighbor(
        self, point: Point, visit_count: Counter[Point], all_points: set[Point]
    ) -> Point | None:
        least_visited_neighbor = None
        min_visit_count = visit_count.most_common(1)[0][1] + 1
        for neighbor in point.neighbors:
            if neighbor not in all_points:
                continue

            if neighbor in self._unvisited_points and neighbor not in visit_count:
                return neighbor

            neighbor_visit_count = visit_count[neighbor]
            if neighbor_visit_count < min_visit_count:
                least_visited_neighbor = neighbor
                min_visit_count = neighbor_visit_count

        return least_visited_neighbor


def points_to_polygons(points: set[Point], polygon_length: int) -> Iterator[Polygon]:
    yield from _PolygonGenerator(points, polygon_length)


def polygons_to_points(polygons: Iterable[Polygon]) -> Iterator[Point]:
    all_points = []
    for polygon in polygons:
        all_points.extend(polygon.points)

    yield from dict.fromkeys(all_points)


def bounding_rect(points: Iterable[Point]) -> Rect:
    if not points:
        return Rect(Point(0, 0), Point(0, 0))

    min_x = min(point.x for point in points)
    min_y = min(point.y for point in points)
    max_x = max(point.x for point in points)
    max_y = max(point.y for point in points)

    return Rect(Point(min_x, min_y), Point(max_x, max_y))
