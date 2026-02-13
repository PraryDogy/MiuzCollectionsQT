from typing_extensions import Optional, Literal
from dataclasses import dataclass

@dataclass(slots=True)
class Test:
    varibale: Literal["a", "b"]


data = {
    "a": 1,
    "b": 2
}