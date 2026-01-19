from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    name: str
    position: float
    power: float
    salience: float
    risk: float
