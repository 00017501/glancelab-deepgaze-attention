# CLAUDE.md

Supporting repository for a group coursework report (CW2): predicted attention from DeepGaze IIE for
variants of one static ad that differ only in the position of the promo price tag.

**Everything this repository produces is predicted attention, not real eye-tracking.** Say so in any
output or text you add.

## Stack

Python 3.13, CPU. DeepGaze IIE at a pinned commit (`setup.sh`), numpy, Pillow, pydantic. No plotting
library. Code conventions: [.claude/rules/python.md](.claude/rules/python.md).

## Commands

```bash
./setup.sh                                   # environment (safe to rerun)
.venv/bin/ruff format src tests && .venv/bin/ruff check src tests
.venv/bin/pytest -m "not slow"               # seconds, no model
.venv/bin/pytest -m slow                     # real model
.venv/bin/python -m src.glance_attention <preview|validate|run|compare|report> --study <folder>
```

## Map

- `src/glance_attention/`: `cli` → `pipeline` (run, compare, report) → `validate`, `model`, `stats`,
  `compare`, `jitter`, `visuals`, `report`, `longtable`, `runlog`; `placeholder`, `preview`,
  `annotate/` are helpers.
- `examples/placeholder/`: generated study; all outputs marked PLACEHOLDER.
- `data/`: the real study.
- `docs/`: METHOD, DECISIONS, AI_USE_AND_PROMPTS, ANALYSIS_GUIDE, AOI_GENERATION.

## Always

- Keep the code free of variant names, file names and image sizes: a study is driven by its folder
  and `study.toml`.
- After changing `src/`, rerun the placeholder study and check the CSVs are unchanged unless the
  change was meant to alter numbers.
- Record a methodological choice as a new entry in `docs/DECISIONS.md`.
- Record any AI-assisted change in `docs/AI_USE_AND_PROMPTS.md` with a one-line summary of the
  request, not its wording. Fold repeat rounds on the same work into one entry.

## Ask first

- Changing a metric definition, the overlap rule, the priors, the threshold default or the jitter
  design.
- Changing pinned versions or the DeepGaze commit.

## Never

- Edit an existing entry in `docs/DECISIONS.md`; add a correcting entry instead.
- Change an AOI file after a model run without recording why.
- Remove or weaken the PLACEHOLDER marking or the "not real eye-tracking" caveat.
- Add personal names or local file paths anywhere; the author is the student ID.
