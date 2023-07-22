from typing import TypeVar, Generic
from enum import StrEnum
from dataclasses import dataclass, field

T = TypeVar("T")


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class Range(Generic[T]):
    max: T | None = None
    min: T | None = None


@dataclass
class Preference:
    age: Range[int] = field(default_factory=Range)
    gender: list[Gender] | None = None
