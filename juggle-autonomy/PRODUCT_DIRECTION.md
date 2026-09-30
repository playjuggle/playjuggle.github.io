# Juggle durable product direction

This file defines the destination and decision principles that should survive individual milestones. It intentionally does **not** define the current task order. Current facts live in `CURRENT_STATE.md`; the active implementation slice lives in `HANDOFF.md`; short-lived candidate work lives in `juggle-autonomy/WORKING_BACKLOG.md`. Later explicit user direction supersedes this file.

## Destination

Build Juggle into a polished, reliable, distinctive daily word game that is satisfying on mobile and desktop, easy to understand without instruction debt, operationally easy to publish every day, and robust enough that content/data mistakes do not silently reach players. Preserve the game's intentionally lightweight feel: the product should feel simple to play even if the systems behind authoring, validation, persistence, accessibility, sharing, analytics, and release reliability become more mature.

The present vanilla static-site architecture is an implementation fact, not the end goal. Keep it when it remains the simplest reliable solution; change it only when a demonstrated product or operational need justifies the complexity.

## Product principles

- **Puzzle quality is the product.** Engineering, analytics, badges, sharing, and tooling support the puzzle experience rather than becoming the experience.
- **Daily trust matters.** The date shown, puzzle served, saved state, streak/completion behavior, and published schedule should agree. Silent fallback, duplicate-date overwrite, malformed content, or preview side effects are product defects when they can mislead players or operators.
- **Interaction should be obvious and low-friction.** Tile placement, swapping, cursor state, submission, hints, final-letter revelation, hard mode, sharing, and error feedback should feel deliberate on touch and mouse without unnecessary animation or visual noise.
- **Minimal presentation, high polish.** Preserve whitespace, legibility, restrained motion/color, responsive layout, and the word puzzle's focus. Add affordance where clarity requires it; avoid decorative complexity for its own sake.
- **Content operations should be boring and safe.** Creating, validating, previewing, scheduling, correcting, and publishing a daily puzzle should be deterministic, locally runnable, auditable, and difficult to do incorrectly. Routine publishing must not depend on an AI subscription.
- **Published content is historical data.** Never rewrite a live/past puzzle by inference. Corrections require explicit owner-confirmed intent and should preserve compatibility where practical.
- **Persistence should be unsurprising.** Existing players should not lose progress/preferences because of incidental refactors. Migrations must be explicit and testable.
- **Accessibility and device reality count.** Keyboard/touch behavior, focus, contrast, screen sizes, motion restraint, and actual mobile/browser behavior are part of correctness, not optional polish.
- **Measure without distorting.** Analytics/feedback should answer concrete product questions with minimal privacy/operational burden. Metrics are evidence, not goals to game.

## End-state coverage

Codex should periodically assess the game across these dimensions rather than over-optimizing whichever subsystem is currently open:

1. core puzzle mechanics and challenge quality;
2. mobile/desktop interaction, accessibility, onboarding, and visual polish;
3. puzzle-data correctness, authoring, validation, preview, scheduling, and publishing;
4. date/time behavior, persistence, streaks, achievements, and compatibility;
5. sharing, feedback, analytics, and privacy/reliability of integrations;
6. deployment/release safeguards and operational recoverability;
7. content cadence and maintainability after launch.

No dimension is automatically the next priority. Choose based on evidence, dependencies, player impact, operational risk, and the highest-leverage gap to the destination.

## Decision discipline

A current implementation, historical spec, backlog item, test metric, or previously chosen milestone is not self-justifying. When evidence changes, Codex should update or discard the plan. Prefer reversible experiments when product uncertainty is high, objective validation when correctness is knowable, and human/device evidence when the question is experiential.

Completion means the destination is credibly met across the relevant dimensions and remaining work is ordinary maintenance/content operation—not merely that the current backlog is empty.
