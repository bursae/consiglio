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
actors:
  - name: Regulator
    position: 80
    power: 0.7
    salience: 0.9
    risk: 0.2
```

Ranges:

- `position`: 0 to 100
- `power`, `salience`, `risk`: 0.0 to 1.0

## What the model does

- Converts each actor into an influence weight: `power * salience * (1 - risk)`
- Computes a weighted average outcome
- Ranks actors by influence share

## Demo dataset (global event)

`actors.global_event.yaml` models a hypothetical global policy event on a 0-100 "trade restrictiveness" axis.

```bash
consiglio predict actors.global_event.yaml
```

## Optional JSON output

```bash
consiglio predict actors.example.yaml --json
```

## Example files

- `actors.example.yaml`
- `actors.global_event.yaml`

## License

TBD
