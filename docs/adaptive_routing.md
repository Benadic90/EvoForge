# Adaptive Routing Intelligence

EvoForge Phase 3C introduces an adaptive routing layer (`adaptive-v1`) that dynamically adjusts the execution chain based on real-time and historical execution outcomes. The router replaces the static model selection layer with an empirically driven capability mapping algorithm.

## Multi-Factor Routing Algorithm

The `adaptive-v1` policy calculates a composite score for each candidate executor based on the following formula:

`Score = (w_cap * S_cap) + (w_hist * R_smooth) + (w_rec * R_rec) + (w_task * R_task) + (w_qual * Q_blend) + (w_rel * 0.95) - (P_cost + P_lat + P_fb)`

### Weights and Metrics

1. **Capability Match ($w_{cap} = 0.35$)**: Hard requirement matching based on agent contracts.
2. **Historical Success ($w_{hist} = 0.15$)**: Lifetime task success rate across all executions. Uses Bayesian smoothing (Beta distribution prior $\alpha=8, \beta=2$) to prevent new models from being starved due to lack of history.
3. **Recency Success ($w_{rec} = 0.20$)**: Time-decay weighted success rate. Emphasizes recent performance to quickly route around degrading APIs or local context limits. Uses an exponential decay formula $w = \exp(-\ln(2) \cdot \frac{\Delta t}{7.0})$.
4. **Task Type Success ($w_{task} = 0.15$)**: Specialized tracking for specific agent capabilities (e.g., coding, research, documentation).
5. **Quality Score ($w_{qual} = 0.10$)**: Evaluates code quality, tests passing, and reviewer approval flags.
6. **Reliability ($w_{rel} = 0.05$)**: Base reliability score.

### Penalties

- **Cost Penalty ($P_{cost}$)**: Up to $-0.15$ deduction for highly expensive APIs (>$0.10/task).
- **Latency Penalty ($P_{lat}$)**: Up to $-0.10$ deduction for consistently slow APIs (>30s avg).
- **Fallback Penalty ($P_{fb}$)**: Up to $-0.20$ deduction if the executor frequently triggers the orchestrated fallback chain.

## Data Persistence

All decisions are recorded in the `routing_decisions` SQLite table. Execution outcomes are written back into `execution_telemetry` and used in the next decision loop.
