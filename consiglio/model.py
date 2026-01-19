from dataclasses import asdict

from .types import Actor


def compute_equilibrium(
    actors: list[Actor], iterations: int = 100, epsilon: float = 1e-4
) -> dict:
    weights = [influence_weight(actor) for actor in actors]
    total_weight = sum(weights)

    positions = [actor.position for actor in actors]
    if total_weight <= 0:
        outcome = sum(positions) / len(positions)
        return {
            "equilibrium": outcome,
            "iterations": 0,
            "converged": True,
            "weights": weights,
        }

    outcome = sum(positions) / len(positions)
    converged = False
    for i in range(iterations):
        prev = outcome
        desired = weighted_average(positions, weights)
        outcome = prev + 0.5 * (desired - prev)
        if abs(outcome - prev) < epsilon:
            converged = True
            return {
                "equilibrium": outcome,
                "iterations": i + 1,
                "converged": True,
                "weights": weights,
            }

    return {
        "equilibrium": outcome,
        "iterations": iterations,
        "converged": converged,
        "weights": weights,
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
