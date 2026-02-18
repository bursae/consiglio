from dataclasses import asdict

from .types import Actor


def compute_equilibrium(
    actors: list[Actor], iterations: int = 100, epsilon: float = 1e-4
) -> dict:
    weights = [influence_weight(actor) for actor in actors]
    positions = [actor.position for actor in actors]
    total_weight = sum(weights)

    if total_weight <= 0:
        outcome = sum(positions) / len(positions)
        std_dev = weighted_std_dev(positions, weights)
        return {
            "equilibrium": outcome,
            "iterations": 0,
            "converged": True,
            "weights": weights,
            "confidence": confidence_score(positions, weights),
            "positions_initial": positions,
            "positions_final": positions,
            "median_position": median_position(positions),
            "outcome_range": implied_range(outcome, std_dev),
            "conflict_index": conflict_index(std_dev),
        }

    outcome = weighted_average(positions, weights)
    std_dev = weighted_std_dev(positions, weights)
    rounds = min(iterations, estimate_rounds(std_dev))
    final_positions = revise_positions(actors, outcome)
    return {
        "equilibrium": outcome,
        "iterations": rounds,
        "converged": True,
        "weights": weights,
        "confidence": confidence_score(positions, weights),
        "positions_initial": positions,
        "positions_final": final_positions,
        "median_position": median_position(positions),
        "outcome_range": implied_range(outcome, std_dev),
        "conflict_index": conflict_index(std_dev),
    }


def influence_weight(actor: Actor) -> float:
    return max(0.0, actor.power) * max(0.0, actor.salience) * max(0.0, 1.0 - actor.risk)


def weighted_average(values: list[float], weights: list[float]) -> float:
    total_weight = sum(weights)
    if total_weight == 0:
        return sum(values) / len(values)
    return sum(value * weight for value, weight in zip(values, weights)) / total_weight


def influence_ranking(actors: list[Actor], weights: list[float]) -> list[dict]:
    total_weight = sum(weights)
    ranking = []
    for actor, weight in zip(actors, weights):
        share = weight / total_weight if total_weight else 0.0
        ranking.append(
            {
                "name": actor.name,
                "weight": weight,
                "share": share,
                "position": actor.position,
            }
        )
    ranking.sort(key=lambda item: item["weight"], reverse=True)
    return ranking


def serialize_actors(actors: list[Actor]) -> list[dict]:
    return [asdict(actor) for actor in actors]


def confidence_score(positions: list[float], weights: list[float]) -> float:
    if not positions:
        return 0.0
    mean = weighted_average(positions, weights)
    total_weight = sum(weights)
    if total_weight == 0:
        variance = sum((position - mean) ** 2 for position in positions) / len(positions)
    else:
        variance = (
            sum(weight * (position - mean) ** 2 for position, weight in zip(positions, weights))
            / total_weight
        )
    std_dev = variance**0.5
    confidence = 1.0 - min(std_dev / 50.0, 1.0)
    return max(0.0, min(confidence, 1.0))


def revise_positions(actors: list[Actor], outcome: float) -> list[float]:
    revised = []
    for actor in actors:
        concession = 0.2 + 0.6 * (1.0 - actor.risk) * (0.5 + 0.5 * actor.salience)
        concession = max(0.0, min(concession, 0.9))
        revised.append(actor.position + concession * (outcome - actor.position))
    return revised


def weighted_std_dev(values: list[float], weights: list[float]) -> float:
    if not values:
        return 0.0
    mean = weighted_average(values, weights)
    total_weight = sum(weights)
    if total_weight == 0:
        variance = sum((value - mean) ** 2 for value in values) / len(values)
    else:
        variance = (
            sum(weight * (value - mean) ** 2 for value, weight in zip(values, weights))
            / total_weight
        )
    return variance**0.5


def median_position(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def implied_range(outcome: float, std_dev: float) -> tuple[float, float]:
    spread = 1.28 * std_dev
    lower = max(0.0, outcome - spread)
    upper = min(100.0, outcome + spread)
    return lower, upper


def conflict_index(std_dev: float) -> float:
    return max(0.0, min(std_dev / 50.0, 1.0))


def estimate_rounds(std_dev: float) -> int:
    return max(3, int(6 + 8 * conflict_index(std_dev)))
