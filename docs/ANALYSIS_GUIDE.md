# Analysis guide: swapping in the real ads

> The pipeline produces **predicted** attention from DeepGaze IIE. It is not real eye-tracking.
> Say so wherever a number or heatmap from it is shown.

No code changes are needed. Everything below is files and one config.

`P` stands for `.venv/bin/python -m src.glance_attention`.

## 1. Put the images in `data/images/`

- One file per variant: `.png`, `.jpg`, `.jpeg` or `.webp`.
- The file name without extension is the variant's name in every table (`A.png` → `A`,
  `top_right.png` → `top_right`). Any number of variants from two upwards.
- All images must be exactly the same pixel size. Export them from the same design file, changing
  only the price layer's position.

## 2. Edit `data/study.toml`

- `title`: shown on the report and the panels.
- `baseline`: the name of the conventional-placement variant.
- `placeholder = false`.
- `external_tools`: the commercial tools actually used and the metrics each will supply, with each
  tool's own scale. Rename `neurons_predict` to `expoze` here if that is the tool the group uses.
- Leave the threshold, jitter settings and seed alone unless the group decides otherwise, and record
  any change in [DECISIONS.md](DECISIONS.md) **before** running the model.

## 3. Make the AOI files, then check them

Follow [AOI_GENERATION.md](AOI_GENERATION.md), then:

```bash
$P preview --study data
```

Open `data/output/preview/<variant>_aois.png` for every variant and check each box by eye.
`aoi_boxes.csv` in the same folder lists every box in pixels and as % of the image: use it to draw
the same AOIs in the commercial tools.

## 4. Validate and lock

```bash
$P validate --study data
```

Fix every error it prints. It checks that image sizes match, every image has an AOI file, the fixed
AOIs are identical in all variants, the price box keeps its size, and boxes are inside the image.
A warning that the price covers part of another AOI is expected when the price sits on the product.

On success it writes `data/aoi_lock.json`. **Commit the images, AOI files and lock now, before the
next step.** That commit is the evidence that the AOIs were fixed before any heatmap existed.

## 5. Run, compare, report

```bash
$P run --study data
$P compare --study data
$P report --study data
```

Commit `data/output/`. The run log records the commit the code was at; commit your work before
`run` so that it does not say "uncommitted changes".

## 6. Fill in the other tools

Open `data/output/cross_tool_long.csv`. For each empty row, type the value from the commercial tool
into `value`, the export date into `run_date` and the tool's version into `version`. Do not change
the DeepGaze rows. Keep a copy of the filled table outside `output/`, because `report` rewrites the
file.

## 7. Read the results

1. `report.md`, "Key test": for each variant, is the price share up and is the product held?
2. "Sensitivity: no centre bias": does the same variant still win? If not, its advantage may come
   from being central.
3. "Robustness": do the ordering and the flags survive the jittered boxes?
4. Across tools, compare directions and rankings, never raw values: the scales differ.

## Rules

- Never change an AOI file after looking at a heatmap. If a box is truly wrong, fix it, re-validate,
  rerun, and explain it in [DECISIONS.md](DECISIONS.md); the run log will show the change.
- Never copy anything from `examples/placeholder/` into the report.
- No personal names or local file paths in the repository; the author is the student ID.
- Git identity for commits is the student ID and its GitHub noreply address.
- Disclose every AI-assisted step in [AI_USE_AND_PROMPTS.md](AI_USE_AND_PROMPTS.md) with its exact
  prompt.
