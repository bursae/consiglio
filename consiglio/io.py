import json
from pathlib import Path

import yaml

from .types import Actor


class InputError(ValueError):
    pass


def load_actors(path: str) -> list[Actor]:
    actors, _ = load_input(path)
    return actors


def load_input(path: str) -> tuple[list[Actor], dict]:
    raw = _load_file(path)
    meta: dict = {}
    if isinstance(raw, dict):
        meta = _extract_meta(raw)
        if "actors" in raw:
            raw = raw["actors"]
    if not isinstance(raw, list):
        raise InputError("Input must be a list of actors or a mapping with an 'actors' list.")

    actors: list[Actor] = []
    for item in raw:
        if not isinstance(item, dict):
            raise InputError("Each actor must be a mapping with required fields.")
        actor = _parse_actor(item)
        actors.append(actor)

    if not actors:
        raise InputError("Input contains zero actors.")
    return actors, meta


def _extract_meta(raw: dict) -> dict:
    meta = {}
    for key in ("scenario", "axis"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            meta[key] = value.strip()
    return meta


def _load_file(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise InputError(f"File not found: {path}")
    text = file_path.read_text(encoding="utf-8")

    if file_path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if file_path.suffix.lower() == ".json":
        return json.loads(text)
    raise InputError("Unsupported file type. Use .yaml, .yml, or .json.")


def _parse_actor(item: dict) -> Actor:
    name = _required_str(item, "name")
    position = _required_number(item, "position")
    power = _required_number(item, "power")
    salience = _required_number(item, "salience")
    risk = _required_number(item, "risk", default=0.0)

    _validate_range("position", position, 0.0, 100.0)
    _validate_range("power", power, 0.0, 1.0)
    _validate_range("salience", salience, 0.0, 1.0)
    _validate_range("risk", risk, 0.0, 1.0)

    return Actor(
        name=name,
        position=float(position),
        power=float(power),
        salience=float(salience),
        risk=float(risk),
    )


def _required_str(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"Actor field '{key}' must be a non-empty string.")
    return value.strip()


def _required_number(item: dict, key: str, default=None) -> float:
    if key not in item:
        if default is not None:
            return default
        raise InputError(f"Actor field '{key}' is required.")
    value = item[key]
    if isinstance(value, (int, float)):
        return float(value)
    raise InputError(f"Actor field '{key}' must be a number.")


def _validate_range(field: str, value: float, min_value: float, max_value: float) -> None:
    if value < min_value or value > max_value:
        raise InputError(f"Actor field '{field}' must be between {min_value} and {max_value}.")
