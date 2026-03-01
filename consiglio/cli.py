import argparse
import json
import sys
from dataclasses import replace

from .io import InputError, load_input
from .model import compute_equilibrium, influence_ranking, serialize_actors


def main() -> None:
    parser = argparse.ArgumentParser(prog="consiglio", description="Bargaining forecast CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict_parser = subparsers.add_parser("predict", help="Predict equilibrium outcome.")
    predict_parser.add_argument("actors", help="Path to actors YAML/JSON file.")
    predict_parser.add_argument("--json", action="store_true", help="Output JSON.")
    predict_parser.add_argument("--table", action="store_true", help="Output table view.")
    predict_parser.add_argument("--export", dest="export_path", help="Export influence CSV.")
    predict_parser.add_argument("--iterations", type=int, default=100, help=argparse.SUPPRESS)
    predict_parser.add_argument("--epsilon", type=float, default=1e-4, help=argparse.SUPPRESS)

    shock_parser = subparsers.add_parser("shock", help="Run a shock scenario.")
    shock_parser.add_argument("actors", help="Path to actors YAML/JSON file.")
    shock_parser.add_argument(
        "--change",
        action="append",
        default=[],
        metavar="NAME.FIELD=VALUE|NAME.FIELD+=DELTA",
        help="Change an actor field (repeatable).",
    )
    shock_parser.add_argument("--json", action="store_true", help="Output JSON.")
    shock_parser.add_argument("--table", action="store_true", help="Output table view.")
    shock_parser.add_argument("--set", action="append", default=[], help=argparse.SUPPRESS)
    shock_parser.add_argument("--delta", action="append", default=[], help=argparse.SUPPRESS)
    shock_parser.add_argument("--iterations", type=int, default=100, help=argparse.SUPPRESS)
    shock_parser.add_argument("--epsilon", type=float, default=1e-4, help=argparse.SUPPRESS)

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
    actors, meta = load_input(args.actors)
    result = compute_equilibrium(actors, args.iterations, args.epsilon)
    ranking = influence_ranking(actors, result["weights"])
    pushers = top_pushers(actors, result["weights"], result["equilibrium"])
    interpretation = interpret_outcome(result["equilibrium"])
    actor_summaries = build_actor_summaries(
        actors, result["positions_final"], result["weights"], result["equilibrium"]
    )
    alliances = alliance_summary(actor_summaries, result["equilibrium"])

    if args.export_path:
        export_csv(args.export_path, ranking)

    if args.json:
        payload = {
            "scenario": meta.get("scenario"),
            "axis": meta.get("axis"),
            "equilibrium": result["equilibrium"],
            "iterations": result["iterations"],
            "rounds_estimate": result["iterations"],
            "converged": result["converged"],
            "confidence": result["confidence"],
            "interpretation": interpretation,
            "median_position": result["median_position"],
            "outcome_range": {
                "p10": result["outcome_range"][0],
                "p90": result["outcome_range"][1],
            },
            "conflict_index": result["conflict_index"],
            "top_pushers": pushers,
            "analyst_assessment": analyst_assessment(result, interpretation, pushers, meta.get("axis")),
            "influence": ranking,
            "actors": actor_summaries,
            "alliances": alliances,
        }
        print(json.dumps(payload, indent=2))
        return

    if args.table:
        print_table_summary(result, ranking, meta, interpretation, pushers, actor_summaries, alliances)
        return
    print_text_summary(result, ranking, meta, interpretation, pushers, actor_summaries, alliances)


def handle_shock(args: argparse.Namespace) -> None:
    actors, meta = load_input(args.actors)
    baseline = compute_equilibrium(actors, args.iterations, args.epsilon)
    baseline_ranking = influence_ranking(actors, baseline["weights"])
    baseline_pushers = top_pushers(actors, baseline["weights"], baseline["equilibrium"])
    baseline_interpretation = interpret_outcome(baseline["equilibrium"])
    baseline_actor_summaries = build_actor_summaries(
        actors, baseline["positions_final"], baseline["weights"], baseline["equilibrium"]
    )
    baseline_alliances = alliance_summary(baseline_actor_summaries, baseline["equilibrium"])

    shocked = apply_shocks(actors, args.change, args.set, args.delta)
    shocked_result = compute_equilibrium(shocked, args.iterations, args.epsilon)
    shocked_ranking = influence_ranking(shocked, shocked_result["weights"])
    shocked_pushers = top_pushers(shocked, shocked_result["weights"], shocked_result["equilibrium"])
    shocked_interpretation = interpret_outcome(shocked_result["equilibrium"])
    shocked_actor_summaries = build_actor_summaries(
        shocked,
        shocked_result["positions_final"],
        shocked_result["weights"],
        shocked_result["equilibrium"],
    )
    shocked_alliances = alliance_summary(shocked_actor_summaries, shocked_result["equilibrium"])

    if args.json:
        payload = {
            "baseline": {
                "scenario": meta.get("scenario"),
                "axis": meta.get("axis"),
                "equilibrium": baseline["equilibrium"],
                "iterations": baseline["iterations"],
                "rounds_estimate": baseline["iterations"],
                "converged": baseline["converged"],
                "confidence": baseline["confidence"],
                "interpretation": baseline_interpretation,
                "median_position": baseline["median_position"],
                "outcome_range": {
                    "p10": baseline["outcome_range"][0],
                    "p90": baseline["outcome_range"][1],
                },
                "conflict_index": baseline["conflict_index"],
                "top_pushers": baseline_pushers,
                "analyst_assessment": analyst_assessment(
                    baseline, baseline_interpretation, baseline_pushers, meta.get("axis")
                ),
                "influence": baseline_ranking,
                "actors": baseline_actor_summaries,
                "alliances": baseline_alliances,
            },
            "shock": {
                "scenario": meta.get("scenario"),
                "axis": meta.get("axis"),
                "equilibrium": shocked_result["equilibrium"],
                "iterations": shocked_result["iterations"],
                "rounds_estimate": shocked_result["iterations"],
                "converged": shocked_result["converged"],
                "confidence": shocked_result["confidence"],
                "interpretation": shocked_interpretation,
                "median_position": shocked_result["median_position"],
                "outcome_range": {
                    "p10": shocked_result["outcome_range"][0],
                    "p90": shocked_result["outcome_range"][1],
                },
                "conflict_index": shocked_result["conflict_index"],
                "top_pushers": shocked_pushers,
                "analyst_assessment": analyst_assessment(
                    shocked_result, shocked_interpretation, shocked_pushers, meta.get("axis")
                ),
                "influence": shocked_ranking,
                "actors": shocked_actor_summaries,
                "alliances": shocked_alliances,
            },
            "delta": shocked_result["equilibrium"] - baseline["equilibrium"],
            "actors": serialize_actors(shocked),
        }
        print(json.dumps(payload, indent=2))
        return

    if args.table:
        print_shock_table_summary(
            baseline,
            shocked_result,
            baseline_ranking,
            shocked_ranking,
            meta,
            baseline_interpretation,
            shocked_interpretation,
        )
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


def print_text_summary(
    result: dict,
    ranking: list[dict],
    meta: dict,
    interpretation: str,
    pushers: dict,
    actor_summaries: list[dict],
    alliances: dict,
) -> None:
    if meta.get("scenario"):
        print("Scenario:", meta["scenario"])
    if meta.get("axis"):
        print("Axis:", meta["axis"])
    print("Equilibrium outcome:", format_value(result["equilibrium"]))
    print("Interpretation:", interpretation)
    print("Median actor position:", format_value(result["median_position"]))
    range_low, range_high = result["outcome_range"]
    print("Implied outcome band:", f"{format_value(range_low)} - {format_value(range_high)}")
    print("Negotiation intensity (est.):", result["iterations"])
    print("Model pass:", "single-pass heuristic")
    print("Confidence:", format_percent(result["confidence"]))
    print("Conflict index:", format_percent(result["conflict_index"]))
    print(
        "Analyst take:",
        analyst_assessment(result, interpretation, pushers, meta.get("axis")),
    )
    print("")
    print("Top pushers:")
    print(format_pushers(pushers))
    print("")
    print("Alliances (final positions):")
    print(format_alliances(alliances))
    print("")
    print("Revised positions:")
    print_revised_positions(actor_summaries)
    print("")
    print("Top influencers:")
    print_influence_table(ranking)


def print_table_summary(
    result: dict,
    ranking: list[dict],
    meta: dict,
    interpretation: str,
    pushers: dict,
    actor_summaries: list[dict],
    alliances: dict,
) -> None:
    if meta.get("scenario"):
        print("Scenario:", meta["scenario"])
    if meta.get("axis"):
        print("Axis:", meta["axis"])
    range_low, range_high = result["outcome_range"]
    metric_rows = [
        ("Equilibrium", format_value(result["equilibrium"])),
        ("Interpretation", interpretation),
        ("Median", format_value(result["median_position"])),
        ("Implied band", f"{format_value(range_low)} to {format_value(range_high)}"),
        ("Negotiation intensity", str(result["iterations"])),
        ("Model pass", "single-pass heuristic"),
        ("Confidence", format_percent(result["confidence"])),
        ("Conflict index", format_percent(result["conflict_index"])),
    ]
    print("")
    print_table(["Metric", "Value"], metric_rows)
    print("")
    print_table(
        ["Pusher Direction", "Actors"],
        [
            ("Higher", ", ".join(item["name"] for item in pushers.get("higher", [])) or "none"),
            ("Lower", ", ".join(item["name"] for item in pushers.get("lower", [])) or "none"),
        ],
    )
    print("")
    print_table(
        ["Alliance", "Actors"],
        [
            ("Higher", ", ".join(alliances.get("higher", [])) or "none"),
            ("Lower", ", ".join(alliances.get("lower", [])) or "none"),
            ("Neutral", ", ".join(alliances.get("neutral", [])) or "none"),
        ],
    )
    print("")
    revised_rows = [
        (
            actor["name"],
            format_value(actor["position_initial"]),
            format_value(actor["position_final"]),
            format_signed(actor["shift"]),
            format_value(actor["pressure"]),
        )
        for actor in actor_summaries
    ]
    print("Revised positions")
    print_table(["Actor", "Initial", "Final", "Shift", "Pressure"], revised_rows)
    print("")
    top_rows = [
        (
            str(idx),
            item["name"],
            f"{item['weight']:.3f}",
            f"{item['share'] * 100:.1f}%",
            format_value(item["position"]),
        )
        for idx, item in enumerate(ranking[:5], start=1)
    ]
    print("Top influencers")
    print_table(["Rank", "Actor", "Weight", "Share", "Position"], top_rows)


def print_shock_table_summary(
    baseline: dict,
    shocked_result: dict,
    baseline_ranking: list[dict],
    shocked_ranking: list[dict],
    meta: dict,
    baseline_interpretation: str,
    shocked_interpretation: str,
) -> None:
    if meta.get("scenario"):
        print("Scenario:", meta["scenario"])
    if meta.get("axis"):
        print("Axis:", meta["axis"])
    print("")
    metric_rows = [
        (
            "Equilibrium",
            format_value(baseline["equilibrium"]),
            format_value(shocked_result["equilibrium"]),
            format_signed(shocked_result["equilibrium"] - baseline["equilibrium"]),
        ),
        (
            "Interpretation",
            baseline_interpretation,
            shocked_interpretation,
            "n/a",
        ),
        (
            "Confidence",
            format_percent(baseline["confidence"]),
            format_percent(shocked_result["confidence"]),
            format_signed((shocked_result["confidence"] - baseline["confidence"]) * 100, suffix="pp"),
        ),
        (
            "Conflict index",
            format_percent(baseline["conflict_index"]),
            format_percent(shocked_result["conflict_index"]),
            format_signed(
                (shocked_result["conflict_index"] - baseline["conflict_index"]) * 100,
                suffix="pp",
            ),
        ),
    ]
    print_table(["Metric", "Baseline", "Shock", "Delta"], metric_rows)
    print("")
    print("Top influencers (baseline)")
    print_rank_table(baseline_ranking)
    print("")
    print("Top influencers (shock)")
    print_rank_table(shocked_ranking)


def print_influence_table(ranking: list[dict], limit: int = 5) -> None:
    header = f"{'Rank':<5} {'Actor':<20} {'Weight':<10} {'Share':<8} {'Position':<9}"
    print(header)
    print("-" * len(header))
    for idx, item in enumerate(ranking[:limit], start=1):
        share = f"{item['share'] * 100:.1f}%"
        print(
            f"{idx:<5} {item['name']:<20} {item['weight']:<10.3f} {share:<8} {item['position']:<9.2f}"
        )


def print_rank_table(ranking: list[dict], limit: int = 5) -> None:
    rows = [
        (
            str(idx),
            item["name"],
            f"{item['weight']:.3f}",
            f"{item['share'] * 100:.1f}%",
            format_value(item["position"]),
        )
        for idx, item in enumerate(ranking[:limit], start=1)
    ]
    print_table(["Rank", "Actor", "Weight", "Share", "Position"], rows)


def print_table(headers: list[str], rows: list[tuple[str, ...]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(str(value)))
    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    divider_line = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(divider_line)
    for row in rows:
        print(" | ".join(str(value).ljust(widths[idx]) for idx, value in enumerate(row)))


def export_csv(path: str, ranking: list[dict]) -> None:
    lines = ["name,weight,share,position"]
    for item in ranking:
        lines.append(
            f"{item['name']},{item['weight']:.6f},{item['share']:.6f},{item['position']:.2f}"
        )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def apply_shocks(
    actors,
    change_specs: list[str],
    set_changes: list[str],
    delta_changes: list[str],
) -> list:
    updated = list(actors)
    for change in change_specs:
        name, field, value, is_delta = parse_change(change)
        updated = [apply_change(actor, name, field, value, is_delta=is_delta) for actor in updated]
    for change in set_changes:
        name, field, value, _ = parse_change(change)
        updated = [apply_change(actor, name, field, value, is_delta=False) for actor in updated]
    for change in delta_changes:
        name, field, value, _ = parse_change(change)
        updated = [apply_change(actor, name, field, value, is_delta=True) for actor in updated]
    return updated


def parse_change(raw: str) -> tuple[str, str, float, bool]:
    if "+=" in raw:
        left, value_str = raw.split("+=", 1)
        is_delta = True
    elif "=" in raw:
        left, value_str = raw.split("=", 1)
        is_delta = False
    else:
        raise InputError("Shock changes must be NAME.FIELD=VALUE or NAME.FIELD+=DELTA.")
    if "." not in left:
        raise InputError("Shock changes must target NAME.FIELD.")
    name, field = left.split(".", 1)
    try:
        value = float(value_str)
    except ValueError as exc:
        raise InputError("Shock change value must be numeric.") from exc
    return name.strip(), field.strip(), value, is_delta


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


def format_signed(value: float, suffix: str = "") -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}{suffix}"


def format_percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def interpret_outcome(value: float) -> str:
    if value <= 33:
        return "low"
    if value <= 66:
        return "medium"
    return "high"


def top_pushers(actors, weights: list[float], equilibrium: float, limit: int = 2) -> dict:
    higher = []
    lower = []
    for actor, weight in zip(actors, weights):
        if actor.position > equilibrium:
            higher.append((actor, weight))
        elif actor.position < equilibrium:
            lower.append((actor, weight))
    higher.sort(key=lambda item: item[1], reverse=True)
    lower.sort(key=lambda item: item[1], reverse=True)
    return {
        "higher": [
            {
                "name": actor.name,
                "position": actor.position,
                "weight": weight,
            }
            for actor, weight in higher[:limit]
        ],
        "lower": [
            {
                "name": actor.name,
                "position": actor.position,
                "weight": weight,
            }
            for actor, weight in lower[:limit]
        ],
    }


def format_pushers(pushers: dict) -> str:
    higher = ", ".join(item["name"] for item in pushers.get("higher", [])) or "none"
    lower = ", ".join(item["name"] for item in pushers.get("lower", [])) or "none"
    return f"Higher: {higher} | Lower: {lower}"


def analyst_assessment(
    result: dict, interpretation: str, pushers: dict, axis: str | None
) -> str:
    outcome = format_value(result["equilibrium"])
    confidence = format_percent(result["confidence"])
    higher = ", ".join(item["name"] for item in pushers.get("higher", [])) or "none"
    lower = ", ".join(item["name"] for item in pushers.get("lower", [])) or "none"
    axis_text = f" on {axis}" if axis else ""
    return (
        f"The balance of forces points to a {interpretation} outcome at {outcome}{axis_text} "
        f"(confidence {confidence}). The main push is upward from {higher}, "
        f"with counterweight from {lower}."
    )


def build_actor_summaries(
    actors, final_positions: list[float], weights: list[float], equilibrium: float
) -> list[dict]:
    summaries = []
    for actor, final_pos, weight in zip(actors, final_positions, weights):
        shift = final_pos - actor.position
        pressure = abs(actor.position - equilibrium) * weight
        summaries.append(
            {
                "name": actor.name,
                "position_initial": actor.position,
                "position_final": final_pos,
                "shift": shift,
                "weight": weight,
                "pressure": pressure,
            }
        )
    return summaries


def alliance_summary(actor_summaries: list[dict], equilibrium: float) -> dict:
    higher = []
    lower = []
    neutral = []
    for actor in actor_summaries:
        if abs(actor["position_final"] - equilibrium) <= 1.0:
            neutral.append(actor)
        elif actor["position_final"] > equilibrium:
            higher.append(actor)
        else:
            lower.append(actor)
    higher.sort(key=lambda item: item["position_final"], reverse=True)
    lower.sort(key=lambda item: item["position_final"])
    neutral.sort(key=lambda item: item["weight"], reverse=True)
    return {
        "higher": [actor["name"] for actor in higher],
        "lower": [actor["name"] for actor in lower],
        "neutral": [actor["name"] for actor in neutral],
    }


def format_alliances(alliances: dict) -> str:
    higher = ", ".join(alliances.get("higher", [])) or "none"
    lower = ", ".join(alliances.get("lower", [])) or "none"
    neutral = ", ".join(alliances.get("neutral", [])) or "none"
    return f"Higher: {higher} | Lower: {lower} | Neutral: {neutral}"


def print_revised_positions(actor_summaries: list[dict]) -> None:
    header = f"{'Actor':<20} {'Initial':<8} {'Final':<8} {'Shift':<8} {'Pressure':<9}"
    print(header)
    print("-" * len(header))
    for actor in actor_summaries:
        print(
            f"{actor['name']:<20} {actor['position_initial']:<8.2f} "
            f"{actor['position_final']:<8.2f} {actor['shift']:<8.2f} "
            f"{actor['pressure']:<9.2f}"
        )


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
