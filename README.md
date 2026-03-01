# Consiglio (MVP)

Consiglio is a CLI tool that turns actor assumptions into a predicted bargaining outcome on a single 0-100 axis.

Core promise: it does not predict the future; it shows the future implied by your assumptions.

## Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

```bash
consiglio predict actors.example.yaml
```

```bash
consiglio shock actors.example.yaml --change "Regulator.power+=0.1"
```

## Workflow

1. Define the axis (0-100) in plain language.
2. List actors with positions and influence inputs.
3. Run a baseline prediction.
4. Run shocks to test what moves the outcome.

## Methodology

Consiglio uses a transparent, assumption-first approach:

1. Translate the policy question into one bounded axis (`0-100`).
2. Encode each actor's preference (`position`) and leverage profile (`power`, `salience`, `risk`).
3. Convert actor inputs into influence weights.
4. Compute a baseline equilibrium from weighted positions.
5. Estimate uncertainty and contestation from position dispersion.
6. Run counterfactual shocks by changing one or more actor fields.
7. Compare baseline vs. shock deltas to identify pivotal actors and assumptions.

This is a structured scenario engine, not an event prediction system. Output quality depends on input quality.

## Model Description

Core weight equation:

`weight_i = power_i * salience_i * (1 - risk_i)`

Equilibrium equation:

`equilibrium = sum(position_i * weight_i) / sum(weight_i)`

If all weights are zero, the model falls back to a simple average position.

Derived outputs:

- `confidence`: higher when actor positions cluster tightly.
- `conflict_index`: higher when actor positions are more dispersed.
- `implied outcome band`: a dispersion band around the equilibrium derived from weighted standard deviation.
- `negotiation intensity (est.)`: a heuristic score derived from conflict index.
- `revised positions`: a concession-adjusted post-negotiation estimate per actor.
- `alliances`: actors grouped as higher/lower/neutral relative to equilibrium.
- `top influencers`: actors ranked by influence share.

Interpretation bands:

- `0-33`: low
- `34-66`: medium
- `67-100`: high

## Limitations

- This is a single-pass heuristic model, not a calibrated forecast model.
- The implied outcome band is not a statistical confidence interval.
- Output is highly sensitive to input assumptions and actor definitions.
- `confidence` and `conflict_index` are inverse transforms of the same dispersion signal.

## Input format

```yaml
scenario: "2018-2019 US-China trade war tariffs"
axis: "trade restrictiveness (0=open trade, 100=high tariffs)"
actors:
  - name: Regulator
    position: 80
    power: 0.7
    salience: 0.9
    risk: 0.2
```

Actor attributes (plain English):

- `name`: human-readable label for the actor
- `position`: preferred outcome on the 0-100 axis (higher = more of the policy)
- `power`: capability to influence the outcome
- `salience`: how much the actor cares about this issue
- `risk`: willingness to accept downside; higher risk reduces influence weight

Ranges:

- `position`: 0 to 100
- `power`, `salience`, `risk`: 0.0 to 1.0

## Demo dataset (global event)

`projects/global-trade-war/actors.yaml` models the 2018-2019 US-China trade war tariffs on a 0-100 "trade restrictiveness" axis.

```bash
consiglio predict projects/global-trade-war/actors.yaml
```

## Demo dataset (known outcome)

`projects/brexit-referendum/actors.yaml` models the 2016 UK Brexit referendum on a 0-100 "EU integration level" axis.

```bash
consiglio predict projects/brexit-referendum/actors.yaml
```

## Demo dataset (tech policy)

`projects/us-ai-chip-export-controls/actors.yaml` models a US AI chip export controls negotiation on a 0-100 "export control strictness" axis.

```bash
consiglio predict projects/us-ai-chip-export-controls/actors.yaml
```

## Demo dataset (historical back-check)

`projects/us-debt-ceiling-2023/actors.yaml` models the 2023 US debt ceiling negotiations ending in the Fiscal Responsibility Act.

```bash
consiglio predict projects/us-debt-ceiling-2023/actors.yaml
```

## Demo dataset (live geopolitical stress test)

`projects/iran-power-transition-2026/actors.yaml` models possible post-crisis Iranian power outcomes on a 0-100 axis from monarchy restoration to IRGC-dominant consolidation.

```bash
consiglio predict projects/iran-power-transition-2026/actors.yaml
```

## Output (example)

```
Scenario: 2018-2019 US-China trade war tariffs
Axis: trade restrictiveness (0=open trade, 100=high tariffs)
Equilibrium outcome: 53.96
Interpretation: medium
Median actor position: 37.50
Implied outcome band: 21.46 - 86.46
Negotiation intensity (est.): 10
Model pass: single-pass heuristic
Confidence: 49%
Conflict index: 51%

Top pushers:
Higher: US Administration, China Government | Lower: Multinational Manufacturers, EU Commission

Alliances (final positions):
Higher: US Administration, China Government | Lower: US Consumers, WTO Secretariat, Multinational Manufacturers, EU Commission | Neutral: none
```

## Optional JSON output

```bash
consiglio predict actors.example.yaml --json
```

## Optional table output

```bash
consiglio predict actors.example.yaml --table
consiglio shock actors.example.yaml --change "Regulator.power+=0.1" --table
```

## Example files

- `actors.example.yaml`
- `projects/global-trade-war/actors.yaml`
- `projects/brexit-referendum/actors.yaml`
- `projects/us-greenland/actors.yaml`
- `projects/us-ai-chip-export-controls/actors.yaml`
- `projects/us-debt-ceiling-2023/actors.yaml`
- `projects/iran-power-transition-2026/actors.yaml`

## License

TBD
