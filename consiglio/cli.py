import argparse
import json
import sys
from dataclasses import replace

from .io import InputError, load_actors
from .model import compute_equilibrium, influence_ranking, serialize_actors


def main() -> None:
    parser = argparse.ArgumentParser(prog="consiglio", description="Bargaining forecast CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict_parser = subparsers.add_parser("predict", help="Predict equilibrium outcome.")
    predict_parser.add_argument("actors", help="Path to actors YAML/JSON file.")
    predict_parser.add_argument("--iterations", type=int, default=100, help="Max iterations.")
    predict_parser.add_argument("--epsilon", type=float, default=1e-4, help="Convergence threshold.")
    predict_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    predict_parser.add_argument(
        "--export",
        dest="export_path",
        help="Export influence ranking to CSV at the given path.",
    )

    shock_parser = subparsers.add_parser("shock", help="Run a shock scenario.")
    shock_parser.add_argument("actors", help="Path to actors YAML/JSON file.")
    shock_parser.add_argument("--iterations", type=int, default=100, help="Max iterations.")
    shock_parser.add_argument("--epsilon", type=float, default=1e-4, help="Convergence threshold.")
    shock_parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="NAME.FIELD=VALUE",
        help="Set actor field to a value (repeatable).",
    )
    shock_parser.add_argument(
        "--delta",
        action="append",
        default=[],
        metavar="NAME.FIELD=DELTA",
        help="Add delta to actor field (repeatable).",
    )
    shock_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )

    args = parser.parse_args()

    try:
        if args.command == "predict":
            handle_predict(args)
        elif args.command == "shock":
            handle_shock(args)
    except InputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def handle_predict(args: argparse.Namespace) -> None:
    actors = load_actors(args.actors)
    result = compute_equilibrium(actors, args.iterations, args.epsilon)
    ranking = influence_ranking(actors, result["weights"])

    if args.export_path:
        export_csv(args.export_path, ranking)

    if args.format == "json":
        payload = {
            "equilibrium": result["equilibrium"],
            "iterations": result["iterations"],
            "converged": result["converged"],
            "influence": ranking,
            "actors": serialize_actors(actors),
        }
        print(json.dumps(payload, indent=2))
        return

    print_text_summary(result, ranking)


def handle_shock(args: argparse.Namespace) -> None:
    actors = load_actors(args.actors)
    baseline = compute_equilibrium(actors, args.iterations, args.epsilon)
    baseline_ranking = influence_ranking(actors, baseline["weights"])

    shocked = apply_shocks(actors, args.set, args.delta)
    shocked_result = compute_equilibrium(shocked, args.iterations, args.epsilon)
    shocked_ranking = influence_ranking(shocked, shocked_result["weights"])

    if args.format == "json":
        payload = {
            "baseline": {
                "equilibrium": baseline["equilibrium"],
                "iterations": baseline["iterations"],
                "converged": baseline["converged"],
                "influence": baseline_ranking,
            },
            "shock": {
                "equilibrium": shocked_result["equilibrium"],
                "iterations": shocked_result["iterations"],
                "converged": shocked_result["converged"],
                "influence": shocked_ranking,
            },
            "delta": shocked_result["equilibrium"] - baseline["equilibrium"],
            "actors": serialize_actors(shocked),
        }
        print(json.dumps(payload, indent=2))
        return

    print("Baseline equilibrium:", format_value(baseline["equilibrium"]))
    print("Shock equilibrium:", format_value(shocked_result["equilibrium"]))
    print("Delta:", format_value(shocked_result["equilibrium"] - baseline["equilibrium"]))
    print("")
    print("Top influencers (baseline):")
    print_influence_table(baseline_ranking)
    print("")
    print("Top influencers (shock):")
    print_influence_table(shocked_ranking)


def print_text_summary(result: dict, ranking: list[dict]) -> None:
    print("Equilibrium outcome:", format_value(result["equilibrium"]))
    print("Iterations:", result["iterations"])
    print("Converged:", "yes" if result["converged"] else "no")
    print("")
    print("Top influencers:")
    print_influence_table(ranking)


def print_influence_table(ranking: list[dict], limit: int = 5) -> None:
    header = f"{'Rank':<5} {'Actor':<20} {'Weight':<10} {'Share':<8} {'Position':<9}"
    print(header)
    print("-" * len(header))
    for idx, item in enumerate(ranking[:limit], start=1):
        share = f"{item['share'] * 100:.1f}%"
        print(
            f"{idx:<5} {item['name']:<20} {item['weight']:<10.3f} {share:<8} {item['position']:<9.2f}"
        )


def export_csv(path: str, ranking: list[dict]) -> None:
    lines = ["name,weight,share,position"]
    for item in ranking:
        lines.append(
            f"{item['name']},{item['weight']:.6f},{item['share']:.6f},{item['position']:.2f}"
        )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def apply_shocks(
    actors, set_changes: list[str], delta_changes: list[str]
) -> list:
    updated = list(actors)
    for change in set_changes:
        name, field, value = parse_change(change)
        updated = [apply_change(actor, name, field, value, is_delta=False) for actor in updated]
    for change in delta_changes:
        name, field, value = parse_change(change)
        updated = [apply_change(actor, name, field, value, is_delta=True) for actor in updated]
    return updated


def parse_change(raw: str) -> tuple[str, str, float]:
    if "=" not in raw:
        raise InputError("Shock changes must be NAME.FIELD=VALUE.")
    left, value_str = raw.split("=", 1)
    if "." not in left:
        raise InputError("Shock changes must target NAME.FIELD.")
    name, field = left.split(".", 1)
    try:
        value = float(value_str)
    except ValueError as exc:
        raise InputError("Shock change value must be numeric.") from exc
    return name.strip(), field.strip(), value


def apply_change(actor, target_name: str, field: str, value: float, is_delta: bool):
    if actor.name != target_name:
        return actor
    if not hasattr(actor, field):
        raise InputError(f"Unknown actor field: {field}")
    current = getattr(actor, field)
    updated_value = current + value if is_delta else value
    validate_actor_field(field, updated_value)
    return replace(actor, **{field: updated_value})


def format_value(value: float) -> str:
    return f"{value:.2f}"


def validate_actor_field(field: str, value: float) -> None:
    ranges = {
        "position": (0.0, 100.0),
        "power": (0.0, 1.0),
        "salience": (0.0, 1.0),
        "risk": (0.0, 1.0),
    }
    if field not in ranges:
        return
    min_value, max_value = ranges[field]
    if value < min_value or value > max_value:
        raise InputError(f"Actor field '{field}' must be between {min_value} and {max_value}.")
