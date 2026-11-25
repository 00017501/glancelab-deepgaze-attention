# AI use and prompts (CW2)

This file discloses every AI-assisted step in this repository. The AOI annotation prompt is given
word for word (2b). The requests behind the other steps are summarised, not reproduced.
All attention values the pipeline produces are predicted by a model (DeepGaze IIE); they are not
real eye-tracking.

## Summary

| # | Step | What the AI did | Human check |
|---|---|---|---|
| 1 | Building the pipeline (2026-11-22) | Claude Code (Anthropic; model `claude-fable-5-2`, with `claude-sonnet` sub-agents for reading files) read the earlier repository, asked the design questions in section 1, wrote the plan, and wrote all code, tests, placeholder images and documentation in this repository | The student wrote the request, answered every question in section 1 and approved the plan before any code was written. Review of the code and of the placeholder outputs by the student: **to be recorded here when done** |
| 2 | AOI boxes for the real ads (2026-11-23) | Claude (`claude-opus-5-5`) proposed boxes for each image from the prompt in 2b; see the log in 2c | The student checks every box on the `preview` image before `aoi apply`, and again before `validate` locks the files. Each proposal's prompt, model, request ID and raw reply are saved in `provenance/aois/` |
| 3 | Attention prediction | DeepGaze IIE, a pretrained saliency model, predicts the attention maps | Not a generative-AI step; listed for completeness. Settings are in `run_log.json` |

Not AI-assisted: the research question, the choice of stimuli and tools, and the answers to the
design questions. The reading of the results in the shared results folder was drafted by the AI
(section 3) and is for the group to check; the interpretation in the report is the group's own.

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
| 6 | "The empty `glancelab-deepgaze-attention` repo is where I plan to build [...]. How should I handle git while building?" | "Commit and push" | – |

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

`just aoi-propose <variant>` sends one image and the prompt
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
- headline: the main title text (the product name and any category line directly under it)
- tagline: the supporting slogan or short body copy that goes with the headline

Rules:
1. Name the AOIs exactly "price", "product", "logo", "headline" and "tagline". The type matches
   the name, except "tagline", whose type is "text".
2. Omit any element that is not in the image. Do not invent one.
3. The product, logo, headline and tagline rectangles must not overlap each other. If two touch,
   split the boundary between them. The price rectangle may overlap another element when the
   price tag really sits on top of it.
4. Include a text element's own background panel or banner, but not empty space around it.
5. Use one rectangle per AOI unless the element is clearly in separate pieces.
6. Leave out divider lines, disclaimers and other small print; they belong to no AOI.
```

### 2c. Log of proposals

One line per proposal: date, variant, model used, request ID, what the reviewer changed.

The three proposals below were made with the earlier four-AOI prompt, which each record in
`provenance/aois/` stores in full. The prompt in 2b was then extended with `tagline` and rule 6, so
that it yields the whole adopted set on its own (D16). Two trial runs of the extended prompt on each
variant are kept in `provenance/aois/regeneration_check/`; they were not adopted. Against the adopted
files: price and logo identical in all six runs, product and headline within 2 px on every edge,
tagline within 3 px except its bottom edge, which the model put 6 px lower.

| Date | Variant | Model used | Request ID | Reviewer's changes |
|---|---|---|---|---|
| 2026-11-23 | A | `claude-opus-5-5` | `msg_011ChK9Q5zLy6tbwVPNKs3dH` | Applied. `tagline` box `[703, 375, 928, 486]` (type `text`) added by hand from the text's pixel extent (D15); the four proposed boxes unchanged |
| 2026-11-23 | B | `claude-opus-5-5` | `msg_011ChK9RJgcTqsWGg5oBRUC1` | Applied. Only the price box is taken from this proposal, unchanged; the fixed AOIs are copied from A |
| 2026-11-23 | C | `claude-opus-5-5` | `msg_011ChK9RdJ38srVpi9GurSUG` | Applied. Only the price box is taken from this proposal, unchanged; the fixed AOIs are copied from A |

## 3. Later AI-assisted changes

One entry per piece of AI-assisted work after the initial build. The request column summarises what
the student asked for; it is not the wording used. Several rounds on the same piece of work are
recorded as one entry.

| Date | Request (summarised) | What the AI did | Human check |
|---|---|---|---|
| 2026-11-22 | Make the pipeline's commands shorter to type | Claude Code (`claude-fable-5-2`) wrote `justfile`, which only wraps the existing commands, and updated the command examples in the docs. No pipeline code, metric or output changed | To be recorded here by the student when reviewed |
| 2026-11-22 | Make the documentation easier to follow: show what each step produces, add example images, give setup steps for each operating system, and tidy the README for reading on GitHub | Claude Code (`claude-fable-5-2`) rewrote `docs/ANALYSIS_GUIDE.md` as a step-by-step guide with the placeholder images and table excerpts, rewrote `README.md` as a short overview, and wrote `docs/SETUP.md`. The Linux and Windows steps were written from the setup script and not run. Documentation only | To be recorded here by the student when reviewed |
| 2026-11-22 | Make clearer what the study does and does not claim, after a group member asked which of three readings was meant | Claude Code (`claude-fable-5-2`) reworded the research-question framing in `README.md` and `docs/METHOD.md` (section 0) and added D14 to `docs/DECISIONS.md`. Wording only; no metric or output changed | To be recorded here by the student when reviewed |
| 2026-11-23 | Let the API key for AOI proposals be kept in a local file | Claude Code (`claude-fable-5-2`) added a git-ignored `.env` that `just` reads, and updated `docs/AOI_GENERATION.md`. The key is never written by the pipeline or committed | To be recorded here by the student when reviewed |
| 2026-11-23 | Make the AOI labels on the preview and heatmap pictures smaller and easier to tell apart | Claude Code (`claude-fable-5-2`) reduced the label size and changed the headline and text box colours in `visuals.py`. Labels are drawn on output pictures only, never on the image the model sees; the placeholder CSV values are unchanged | To be recorded here by the student when reviewed |
| 2026-11-23 | Make the published annotation prompt able to reproduce the adopted AOI set on its own | Claude Code (`claude-fable-5-2`) added the `tagline` element and a rule about small print to the prompt (2b), ran it twice per variant to compare with the adopted boxes, kept those runs in `provenance/aois/regeneration_check/`, and added D16. The adopted AOI files were not changed | To be recorded here by the student when reviewed |
| 2026-11-23 | Run DeepGaze on the real ads and collect results from the commercial tools, with screenshots and raw exports as evidence | Claude Code (`claude-fable-5-2`) ran the pipeline, then operated the web tools in a browser the student had logged into: uploaded the clean images, chose the settings in D17, drew the locked AOIs and read their positions back, downloaded the exports and saved screenshots into `data/external/`. In Attention Insight it first analysed B and C with A's price box, then redrew and re-ran both. Brainsight values were typed from screenshots. A third tool returned no results | To be recorded here by the student when reviewed |
| 2026-11-23 | Compare the tools and put everything into one folder the group can read | Claude Code (`claude-fable-5-2`) named the two commercial tools in `data/study.toml` (D17), ran the comparison and report, filled the cross-tool table from the exports with a one-off script, and assembled `share/2026-11-23-results/` with a README per folder. **The reading of the results in those READMEs was drafted by the AI** and needs the group's review | To be recorded here by the student when reviewed |
| 2026-11-23 | Explain the centre bias and the MIT1003 dataset in plain language | Claude Code (`claude-fable-5-2`) added the explanation to `docs/METHOD.md` (section 2) and to the DeepGaze guide in the results folder. The dataset figures and the reference were written from the AI's general knowledge and should be checked against the paper before being cited | To be recorded here by the student when reviewed |
| 2026-11-26 | Update the README now that the real ads and the commercial tools' results exist: keep it brief, show some of the images, and compare the three models | Claude Code (`claude-fable-5-2`) rewrote `README.md` around the real ad versions, the cross-model heatmaps and a results table, with figures copied from the results folder and `data/output/verdict.csv`. **The short reading of the results repeats the AI-drafted one in the results folder** and needs the group's review. At the student's request it also renamed the results folder from `share/2026-11-23-results/` to `results/2026-11-23/` and updated the links; earlier entries keep the old name. Documentation only | To be recorded here by the student when reviewed |
