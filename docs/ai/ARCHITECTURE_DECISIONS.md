# Architecture Decisions

This is an append-only decision log. Future ChatGPT/Codex decisions should be added with date, decision, rationale, and consequences.

## 2026-05-03 - Bootstrap Handoff System Only
- Decision: Codex made no new simulator architecture decision during bootstrap.
- Rationale: The requested Phase 0 scope was documentation and repository handoff setup, not feature work.
- Consequences: Existing apparent architecture is documented in `PROJECT_CONTEXT.md` and `CURRENT_STATE.md`; future architecture changes should be explicitly logged here.

## Prior Context From Existing Summaries, Not Revalidated As Formal Codex Decisions
- `Summary_1.md` and `Summary_2.md` describe intended directions: bit-for-bit AS parity, Gymnasium interface, multi-discrete keyboard-like actions, vector/RAM observations, and future SB3 training.
- Some summary claims are not verified in current code, including W&B integration, threaded/asynchronous GIF recording, and complete training/checkpoint pipelines.
- Treat these summaries as useful planning context, not authoritative implementation state.

## 2026-05-03 - Deterministic Replay Foundation
- Decision: Use simple JSONL replays with one header plus one action/state-hash record per tick.
- Rationale: Human-inspectable and enough to verify headless-to-GUI determinism before adding combat.
- Consequences: Schema v1 does not yet support mid-replay reset events or full AS parity traces.
