# Consiglio (MVP)

Consiglio is a CLI bargaining-forecast engine that models outcomes as strategic bargaining among actors.

## Install (local)

```bash
python -m pip install -e .
```

## Usage

Predict equilibrium:

```bash
consiglio predict actors.example.yaml
```

Shock an actor field:

```bash
consiglio shock actors.example.yaml --delta "Regulator.power=0.1"
```

Export influence ranking:

```bash
consiglio predict actors.example.yaml --export influence.csv
```

## Input format

```yaml
actors:
  - name: Regulator
    position: 80
    power: 0.7
    salience: 0.9
    risk: 0.2
```

## Output (text)

```
Equilibrium outcome: 63.42
Iterations: 12
Converged: yes

Top influencers:
Rank  Actor                Weight     Share    Position
--------------------------------------------------------
1     Regulator            0.504      54.0%    80.00
```
