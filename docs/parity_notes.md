# HA2 Parity Notes

## Believed To Match Current AS Translation
- Player spawn uses `map[y][x][0] == 32`, sets `x = tile * 50 + 25`, and starts at `y = -50`.
- Runtime map setup now clears `32` spawn markers to `0`, matching AS `assignents()`.
- Core movement values currently match the inspected AS2 constants: width `48`, height `48`, player hitbox `10 x 42`, gravity increment `+1`, walk acceleration `1`, walk clamp near `5`, velocity clamp near `6`, jump hold `6`, jump impulse `-8`, hyperjump charge `150`, and hyperjump impulse `-32`.
- Current collision math follows the inspected `heroAction` tile probes and pixel snap formulas.
- Tile rendering uses FFDEC `DefineSprite_318_tiles` frames with AS mapping `map_graphic_index + 1` and the original `-1` draw offset.
- The left world boundary can leave part of the visible sprite outside the world because AS collision uses a narrow centered hitbox and snaps `_x` using the logical `width=48`, not the full visible body.
- Player body rendering does not mirror on left/right movement; inspected AS did not show a hero body `_xscale` flip. Walking currently alternates colored bitmap exports `126.png` and `128.png`.

## Uncertain
- Decompiled AS uses mixed variable casing such as `defplayerwidth` in setup and `defPlayerWidth` in action, plus `playerWidth`/`playerwidth`. Current Python uses the lowercase working fields from the previous port; exact Flash runtime behavior needs verification.
- `hitCheck` in AS assumes map indexes are valid. Current Python bounds-checks indexes, preserving prior port behavior but possibly hiding original edge behavior.
- Player rendering uses colored FFDEC bitmap image exports centered in the logical 48x48 hero box. Exact Flash registration point and walk animation cadence should still be verified.
- Camera/parallax currently approximates visible behavior and has not been verified against Flash traces.

## Intentionally Simplified For Now
- No crates, health drops, ammo drops, weapon switching, non-basic weapons, helicopter AI, projectile systems, or score/combat simulation.
- Reward is a simple survival baseline.
- Replay schema records actions and state hashes for the current Python simulator; it is not an AS parity trace format.

## Needs Later Verification
- Golden traces for idle, walk right, jump, double jump, duck/stand, and hyperjump.
- Player bitmap registration and walk animation cadence.
- Headless-to-GUI replay determinism after combat/enemies are added.
- Exact camera and background scroll behavior.
