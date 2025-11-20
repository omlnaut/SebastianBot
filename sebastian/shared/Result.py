from typing import Generic, List, TypeVar

T = TypeVar("T")


class Result(Generic[T]):
    def __init__(self, item: T | None = None, errors: List[str] | None = None):
        self.item: T | None = item
        self.errors: List[str] = errors or []

    @staticmethod
    def from_item(
        item: T | None = None, errors: List[str] | None = None
    ) -> "Result[T]":
        return Result(item=item, errors=errors)

    @property
    def errors_string(self) -> str:
        return "\n-------------\n".join(self.errors)

    def __str__(self) -> str:
        return f"Result(item={self.item}, errors={self.errors})"

    def __repr__(self) -> str:
        return self.__str__()
