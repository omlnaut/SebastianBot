from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


def first_or_none(iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    return next((item for item in iterable if predicate(item)), None)
