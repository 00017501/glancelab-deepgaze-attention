# Price-position attention study: DeepGaze IIE pipeline

Predicted attention for several versions (A, B, C, ...) of one static furniture ad that are identical
except for where the promo price tag sits. Research question: *where should the promo price go so it
is noticed and remembered, without reducing attention on the product?* Version A is the conventional
placement and the baseline.

> **Caveat.** Every number and heatmap here is *predicted* free-viewing attention from DeepGaze IIE
> (Linardos et al., 2021). They are not eye-tracking measurements of real viewers, and they say
> nothing about memory, viewing goals or the context the ad appears in.

> **Status.** The real ads do not exist yet. The only outputs in this repository come from generated
> grey-box images in [`examples/placeholder/`](examples/placeholder/). Every one of them is marked
> **PLACEHOLDER – not results** and must never be reported.

DeepGaze is one of three attention tools in the group project (CW2). The other two are commercial and
their numbers are exported by hand; this pipeline writes one long-format table
(`cross_tool_long.csv`) with the DeepGaze rows filled in and empty rows for the other tools.

Author: student ID 00017501.

## Layout

| Path | What it is |
|---|---|
| `src/glance_attention/` | The pipeline and its command line |
| `examples/placeholder/` | Placeholder study: generated images, AOI files and marked outputs |
| `data/` | The real study goes here: `study.toml`, `images/`, `aois/` |
| `prompts/aoi/annotation.txt` | Prompt used when an AI proposes AOI boxes |
| `provenance/aois/` | AI AOI proposals and their audit records |
| `docs/` | [METHOD](docs/METHOD.md), [DECISIONS](docs/DECISIONS.md), [AI_USE_AND_PROMPTS](docs/AI_USE_AND_PROMPTS.md), [ANALYSIS_GUIDE](docs/ANALYSIS_GUIDE.md), [AOI_GENERATION](docs/AOI_GENERATION.md) |
| `setup.sh`, `requirements*.txt`, `patches/` | Pinned environment |
| `tests/` | Tests; all but one run without the model |

A **study** is a folder holding `study.toml`, `images/` and `aois/`. Each image file is one variant,
named by its file name (`A.png` is variant `A`), with a matching `aois/A.json`. Nothing in the code
names a variant, a file or an image size.

## Setup (macOS or Linux, CPU, Python 3.13)

```bash
./setup.sh                                        # venv, pinned packages, DeepGaze at a pinned commit
.venv/bin/pip install -r requirements-dev.txt     # tests, lint, AOI proposal helper
.venv/bin/pytest -m "not slow"                    # seconds, no model
.venv/bin/pytest -m slow                          # runs the real model once
```

The first model run downloads the pretrained weights (1-2 GB) into the torch cache.

## Use

Every command takes `--study <folder>` (default `data`).

```bash
P=".venv/bin/python -m src.glance_attention"
$P preview  --study data    # draw the AOI boxes on the images; list them in pixels and %
$P validate --study data    # check images and AOIs, then lock the AOIs
$P run      --study data    # run the model; needs locked AOIs
$P compare  --study data    # deltas against the baseline and the key test
$P report   --study data    # report.md and cross_tool_long.csv
```

Helpers:

```bash
$P placeholder --study examples/placeholder       # regenerate the placeholder images and AOI files
$P aoi propose A --study data                     # an AI proposes AOI boxes (needs ANTHROPIC_API_KEY)
$P aoi apply A --study data                       # adopt a reviewed proposal as aois/A.json
$P run --skip-model --study data                  # recompute tables and images from saved densities
```

To swap in the real ads, follow [docs/ANALYSIS_GUIDE.md](docs/ANALYSIS_GUIDE.md). No code changes
are needed: replace the files and edit `study.toml`.

## What comes out (`<study>/output/`)

| File | Content |
|---|---|
| `heatmaps/<variant>_heatmap.png`, `<variant>_aoi.png` | Heatmap, and heatmap with AOI boxes and shares |
| `panel.png`, `panel_no_centerbias.png` | All variants side by side on one colour scale |
| `<variant>_aoi.csv`, `summary.csv` | Per-AOI and whole-image metrics, both priors |
| `compare.csv`, `verdict.csv` | Deltas against the baseline; price-up / product-held test |
| `jitter.csv`, `jitter_stability.csv` | Robustness to slightly different AOI boxes |
| `cross_tool_long.csv` | `tool, variant, aoi, metric, value, scale, run_date, version` |
| `report.md` | Everything above in one readable page |
| `run_log.json` | Model version, settings, image and AOI hashes, date, commit |
| `preview/` | AOI boxes on the plain images, and `aoi_boxes.csv` in pixels and % |

Metric definitions are in [docs/METHOD.md](docs/METHOD.md).

## Licence and references

MIT, see [LICENSE](LICENSE).

- Linardos, A., Kümmerer, M., Press, O. and Bethge, M. (2021) 'DeepGaze IIE: Calibrated prediction
  in and out-of-domain for state-of-the-art saliency modeling', *ICCV 2021*.
- DeepGaze code: https://github.com/matthias-k/DeepGaze (pinned commit in `setup.sh`).
