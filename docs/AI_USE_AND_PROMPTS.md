# AI use and prompts (CW2)

This file discloses every AI-assisted step in this repository. The AOI annotation prompt is given
word for word (2b). The requests behind the other steps are summarised, not reproduced.
All attention values the pipeline produces are predicted by a model (DeepGaze IIE); they are not
real eye-tracking.

## Summary

| # | Step | What the AI did | Human check |
|---|---|---|---|
| 1 | Building the pipeline (2026-11-22) | Claude Code (Anthropic; model `claude-fable-5-2`, with `claude-sonnet` sub-agents for reading files) read the earlier repository, asked the design questions in section 1, wrote the plan, and wrote all code, tests, placeholder images and documentation in this repository | The student wrote the request, answered every question in section 1 and approved the plan before any code was written. Review of the code and of the placeholder outputs by the student: **to be recorded here when done** |
| 2 | AOI boxes for the real ads (not done yet) | Claude (`claude-opus-5-5` by default) proposes boxes for one image from the prompt in 2b | The student checks every box on the `preview` image before `aoi apply`, and again before `validate` locks the files. Each proposal's prompt, model, request ID and raw reply are saved in `provenance/aois/` |
| 3 | Attention prediction | DeepGaze IIE, a pretrained saliency model, predicts the attention maps | Not a generative-AI step; listed for completeness. Settings are in `run_log.json` |

Not AI-assisted: the research question, the choice of stimuli and tools, the answers to the design
questions, and the interpretation in the report.

The placeholder AOI files are not AI proposals: the generator writes them from the same coordinates
it draws the boxes with.

## 1. Building the pipeline

The student asked for the earlier single-image pipeline to be adapted to compare variants of one
ad that differ only in the price position, built and tested on placeholders. The request itself is
not reproduced here.

### The questions the AI asked and the answers given

Each question came with options and the AI's recommendation. The student chose.

| # | Question (as asked) | Answer chosen | Decision |
|---|---|---|---|
| 1 | "The price tag moves between variants and in some positions may sit on top of the product. When the price box overlaps the fixed product box, who gets those pixels?" | "Price wins" (the AI's recommendation) | D4 |
| 2 | "For the real ads, how will the AOI boxes be produced? The same boxes also have to be redrawn by hand inside Attention Insight and Neurons/Expoze, so whatever we choose is the single source of truth for all three tools." | "AI proposes, you confirm" (the AI had recommended typing them by hand) | D9 |
| 3 | "A variant gets flagged when product attention falls too far below baseline A. How should 'too far' be measured?" | "Relative drop in share" (recommended) | D7 |
| 4 | "DeepGaze adds a centre bias (people tend to look at the middle), so a price moved toward the centre gains share from that prior alone. Since position is exactly what you vary, how should the pipeline treat it?" | "Both, MIT1003 primary" (recommended) | D6 |
| 5 | "The shared cross-tool CSV gets empty template rows for Attention Insight and Neurons/Expoze. [...] Which rows should the template contain for the other tools?" | "Listed in config" (recommended) | D12 |
| 6 | "This is group coursework but the repo must carry student IDs only. Whose ID(s) go in LICENSE, README and the docs as the author?" | "00017501 only" (recommended) | D0 |
| 7 | "The empty `glancelab-deepgaze-attention` repo is where I plan to build [...]. How should I handle git while building?" | "Commit and push" | – |

Points the AI raised unprompted, which shaped the design: the centre bias is confounded with
position (D6); clarity will barely differ between variants; heatmaps scaled per image are not
comparable (D10); the earlier pipeline did not enforce non-overlapping AOIs (D4) and recorded no
run metadata (the run log).

Choices the AI made without asking, each recorded as a decision the student can overturn: the study
folder layout (D2), the placeholder marking (D3), the lock mechanism (D5), the jitter design (D8),
one colour scale (D10), CPU only (D13), the default 10% threshold (D7), the placeholder layout and
the three price positions.

The plan the student approved is summarised by the decisions D0-D13 in
[DECISIONS.md](DECISIONS.md).

## 2. AOI boxes for the real ads

### 2a. How it runs

`python -m src.glance_attention aoi propose <variant> --study data` sends one image and the prompt
below to Claude and saves the proposal and an audit record (model requested and used, effort, SDK
versions, prompt text and hash, image hash, request ID, token counts, the raw reply, any box
problems) in `provenance/aois/`. Nothing is adopted until `aoi apply`. See
[AOI_GENERATION.md](AOI_GENERATION.md).

### 2b. The prompt, verbatim

`{WIDTH}` and `{HEIGHT}` are replaced by the size of the image as sent. A test keeps this block
identical to `prompts/aoi/annotation.txt`.

```
You are annotating areas of interest (AOIs) on a static retail advertisement for an
attention study. The image is {WIDTH} x {HEIGHT} pixels.

Find each of these elements if present, and give a tight bounding rectangle for each
in image pixel coordinates [x0, y0, x1, y1] (x0,y0 = top-left; x1,y1 = bottom-right):
- price: the promotional price tag (the price figure with its own badge, panel or sticker)
- product: the main product being advertised (the whole object, not the room around it)
- logo: the brand logo or wordmark
- headline: the main title text

Rules:
1. Name the four AOIs exactly "price", "product", "logo" and "headline", with the matching type.
2. Omit any element that is not in the image. Do not invent one.
3. The product, logo and headline rectangles must not overlap each other. If two touch, split
   the boundary between them. The price rectangle may overlap another element when the price
   tag really sits on top of it.
4. Include a text element's own background panel or banner, but not empty space around it.
5. Use one rectangle per AOI unless the element is clearly in separate pieces.
```

### 2c. Log of proposals

None yet: the real ads do not exist. Add one line per proposal here (date, variant, model used,
request ID, what the reviewer changed) when they are made.

## 3. Later AI-assisted changes

One entry per piece of AI-assisted work after the initial build. The request column summarises what
the student asked for; it is not the wording used. Several rounds on the same piece of work are
recorded as one entry.

| Date | Request (summarised) | What the AI did | Human check |
|---|---|---|---|
