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

## What the model does

- Converts each actor into an influence weight: `power * salience * (1 - risk)`
- Computes a weighted average outcome
- Simulates bargaining rounds and revised actor positions
- Adds a simple confidence score based on how tightly actor positions cluster
- Adds a plain-language interpretation (low/medium/high) and top pushers
- Groups actors into higher/lower/neutral alliances relative to the outcome
- Reports an implied outcome range and a conflict index
- Ranks actors by influence share

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

## Output (example)

```
Scenario: 2018-2019 US-China trade war tariffs
Axis: trade restrictiveness (0=open trade, 100=high tariffs)
Equilibrium outcome: 53.96
Interpretation: medium
Median actor position: 37.50
Implied range (10-90%): 21.46 - 86.46
Bargaining rounds (est.): 10
Converged: yes
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

## Example files

- `actors.example.yaml`
- `projects/global-trade-war/actors.yaml`
- `projects/brexit-referendum/actors.yaml`
- `projects/us-greenland/actors.yaml`

## License

TBD
