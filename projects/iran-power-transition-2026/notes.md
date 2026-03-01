# Interpretation guide

Scenario: Iran power transition stress test (2026).

Axis meaning:
- `0-25`: high probability of monarchy restoration pathway.
- `35-65`: people-led plural transition or coalition transitional order.
- `75-100`: IRGC-dominant security-state consolidation.

Modeling notes:
- This is a stress-test baseline, not a forecast.
- To simulate momentum for a people-led transition, increase `power` for protest and labor actors and/or reduce IRGC salience.
- To simulate monarchy restoration momentum, increase diaspora monarchist organizational power and align more domestic actors toward low-axis positions.
- To simulate hardline consolidation, increase IRGC/state power and salience while reducing strike/protest influence.

Suggested run commands:

```bash
consiglio predict projects/iran-power-transition-2026/actors.yaml
consiglio shock projects/iran-power-transition-2026/actors.yaml --change "Urban Protest Networks.power+=0.10"
consiglio shock projects/iran-power-transition-2026/actors.yaml --change "Islamic Revolutionary Guard Corps (IRGC).power+=0.08"
```

