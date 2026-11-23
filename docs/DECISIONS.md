# Decisions (CW2)

Entries are never edited after they are written. A correction is a new entry that names the one it
corrects. All values produced by this repository are predicted attention, not real eye-tracking.

### D0 – Scope (2026-11-22)

**Decision.** This repository is the DeepGaze IIE part of a group coursework (CW2) that tests where
the promo price tag should sit on a static furniture ad. It produces numbers for one shared
cross-tool table; the other two tools are commercial and exported by hand.
**Identity.** The repository contains no personal names and no local file paths.

### D1 – Start from the earlier DeepGaze pipeline (2026-11-22)

**Decision.** Reuse the model runner, the AOI share, entropy and peak maths, the heatmap rendering,
the pinned environment and the AI AOI-proposal helper from an earlier single-image
DeepGaze coursework pipeline. Rebuild everything that depends on the scenario.
**Carried over unchanged.** DeepGaze IIE at commit `c7db17e`, the patch that makes the unused
`deepgazemsdb` import optional (it needs a package this model does not use), Python 3.13, the pinned
package versions, CPU inference at native resolution, the MIT1003 centre-bias template.
**New.** A study folder with a config file, one AOI file per variant, validation and an AOI lock,
two priors, comparison against a baseline, jitter, a long-format table, a run log, panels,
placeholders.
**Why.** The carried-over parts were already checked in the earlier work; the earlier pipeline had no
notion of variants, a baseline or a run log.

### D2 – A study is a folder; nothing is hard-coded (2026-11-22)

**Decision.** Variants are whatever image files are in `images/`; a variant's name is its file name
without extension; its AOIs are in `aois/<name>.json`; settings are in `study.toml`.
**Why.** The real ads do not exist yet. Swapping them in must need no code change, and the number of
variants must stay open.

### D3 – Placeholders are generated and loudly marked (2026-11-22)

**Decision.** A script draws the placeholder ads and writes their AOI files from the same
coordinates. A study with `placeholder = true` gets `PLACEHOLDER_` on every output file name, a red
"PLACEHOLDER – NOT RESULTS" banner on every image, the same line at the top of the report, and
`PLACEHOLDER` at the start of the `version` column of the long table (including the empty rows for
the other tools).
**Why.** A placeholder number in the report would be a fabricated result. The marking has to survive
a file being copied out of its folder.

### D4 – Where the price covers another AOI, the price wins (2026-11-22)

**Decision.** Overlapping pixels count for `price` only. Fixed AOIs may not overlap each other.
**Why.** Shares must sum to 100%, and a hotspot on the price tag is attention to the price.
**Alternatives.** Forbid overlap (rules out a price placed on the product); count the pixels for both
(shares exceed 100% and one hotspot is counted twice).
**Effect.** A price on the product shrinks the product's area in that variant, so the product
comparison shows density next to share (D7).

### D5 – AOIs are locked before the model runs (2026-11-22)

**Decision.** `validate` writes `aoi_lock.json` (SHA-256, file time and lock time per AOI file).
`run` refuses to start if the files differ from the lock, and writes the hashes and lock time to the
run log before the model loads. The run log keeps a fingerprint of the AOI set of every earlier run;
if it ever changes, the run log and the report carry a warning.
**Why.** The brief requires AOIs to be fixed before any heatmap is generated. Drawing boxes after
seeing the heatmap would let the result shape the measurement.
**Limit.** The lock proves the files did not change between `validate` and `run`. It cannot prove
nobody looked at a heatmap from another tool first.

### D6 – Two priors: MIT1003 centre bias (primary) and none (sensitivity) (2026-11-22)

**Decision.** Headline numbers use the standard centre bias. Every metric is also computed with a
uniform prior and reported as a sensitivity check.
**Why.** The centre bias adds attention to the middle of any image. Here position is the manipulated
variable, so a price moved toward the centre would gain share from the prior alone.
**Alternative.** Centre bias only, with the confound mentioned as a limitation.
**Note.** The uniform prior is outside the model's trained setup, so it is a check on the
conclusion, not a second result.

### D7 – Product-drop flag is a relative drop in share (2026-11-22)

**Decision.** A variant is flagged when its product share is more than
`product_drop_threshold_pct` % (default 10) below the baseline product share. The change in product
density is shown beside it and does not drive the flag.
**Why.** A relative threshold means the same thing whatever the product's share is.
**Alternatives.** A percentage-point threshold; flagging on share or density.
**Note.** The default of 10% is a convention chosen before any real data, not an empirical cut-off.

### D8 – Jitter: ±5% per edge, 200 seeded draws, on saved densities (2026-11-22)

**Decision.** Each box edge moves independently by a uniform random amount up to ±5% of the box's
width or height. One draw applies the same shifts to an AOI in every variant. Seed and draw count
are in `study.toml`. The model is not rerun.
**Why.** AOI boxes are a judgement. The check shows whether the conclusion depends on exactly where
the lines were drawn. Applying one draw to all variants keeps the fixed AOIs identical across
variants inside each draw, as they are in the study.

### D9 – AOI boxes for the real ads: AI proposes, a person confirms (2026-11-22)

**Decision.** Boxes are proposed by Claude through `aoi propose`, reviewed on the `preview` image,
and adopted with `aoi apply`. For every variant except the baseline, only the price box is taken
from the proposal; the fixed AOIs are copied from the baseline's file.
**Why.** Faster and more consistent than reading coordinates by hand, with a prompt and an audit
record for the disclosure. Copying the fixed AOIs removes drift between variants.
**Not applied to placeholders.** Their AOI files come from the generator's own coordinates.

### D10 – One colour scale for all variants (2026-11-22)

**Decision.** Heatmaps and panels use the highest density across all variants (per prior) as the
hottest colour.
**Why.** With a separate scale per image, the same colour would mean different amounts of attention
in different variants, and the side-by-side panel would mislead.

### D11 – AOI rank and first-look rank are different things (2026-11-22)

**Decision.** `share_rank` orders AOIs by attention share. `first_look_rank` orders them by peak
density and is always labelled "not a scanpath".
**Why.** DeepGaze IIE predicts a density, not a sequence of fixations.

### D12 – Cross-tool table: tools and metrics come from the config (2026-11-22)

**Decision.** `study.toml` lists each external tool and the metrics it will supply, each with its
own scale. Empty rows are generated from that list. DeepGaze-only metrics have DeepGaze rows only.
**Why.** The second commercial tool is not settled, and the tools do not export density, first-look
order or entropy. A full grid would be mostly empty for ever.

### D13 – CPU only (2026-11-22)

**Decision.** Inference runs on the CPU, with no device option.
**Why.** Numbers must be reproducible on the machine that produced them; other devices can differ in
the last digits. Three images under two priors take about half a minute.

### D14 – What the study claims (2026-11-22)

**Decision.** The study is framed as a placement decision with a trade-off: which price position
gains predicted attention for the price while the product keeps its share. Version A (conventional
position) is the baseline; the other versions are positions expected to draw more attention.
**Not claimed.** That the price is currently under-noticed in the advertiser's real ads (there is no
data on them), or that more attention on the price is good regardless of the product.
**Why.** A group member asked which of three readings was meant: the current price is too little
noticed; the price should be made more noticeable whatever the baseline; or versions are tried to
see which is best. It is none of the first two, and the third only in a structured form: versions,
AOIs and the product threshold are fixed before the model runs (D5, D7).
**Effect.** Wording only. No metric, threshold or output changes.

### D15 – AOI set for the real ad: tight product box, title and tagline separate (2026-11-23)

**Decision.** Five fixed-or-moving AOIs: `price` (the tag, moving), `product` (the bookcase only,
not the photo around it), `logo`, `headline` (product name and category line) and `tagline` (type
`text`, the two-sentence line under the rule). Everything else, including the photo background and
the disclaimer, is `rest`.
**Alternative considered.** A group member's earlier annotation, drawn on a previous export of the
ad, used the whole photo panel as the product and one "Text" box for name, rule and tagline.
**Why.** The photo panel is about half the image and mostly empty wall, so its share reflects the
centre of the image more than the product. Name and tagline are split because the tag sits beside
the name in one version and beside the tagline in another; the two shares can still be added to
compare with a single text box.
**Effect.** `tagline` was added by hand to the baseline proposal (measured from the text's pixel
extent); the other boxes are the AI proposal unchanged. Fixed before any model run (D5).

### D16 – The annotation prompt asks for the tagline too (2026-11-23)

**Decision.** The AOI prompt now names five elements (adding `tagline`, type `text`), describes
`headline` as the product name and category line, and tells the model to leave out divider lines
and small print.
**Why.** The adopted set (D15) had a hand-added tagline box, so the published prompt could not
reproduce it. With the extended prompt, anyone can regenerate the full set from the clean images.
**Check.** Two runs per variant with the extended prompt: price and logo identical to the adopted
boxes, product and headline within 2 px, tagline within 3 px except a 6 px lower bottom edge. All
of this is far inside the 5% jitter range.
**Effect.** The adopted AOI files are unchanged: four boxes from the earlier prompt, tagline by
hand. The trial runs are kept as evidence and were not adopted.

### D17 – Commercial tools: which ones, their settings, and how AOIs map (2026-11-23)

**Decision.** The cross-tool table carries DeepGaze IIE, Attention Insight and Brainsight. A third
commercial tool was tried and returned no results, so it is not part of the study.
**Settings.** Attention Insight: Advertising, channel Social Ads, objective Product Highlight.
Brainsight: type Social media. The clean images were uploaded; the locked AOIs (D15) were drawn by
mouse and read back from the page, every edge within 2 px.
**Mapping.** Attention Insight labels: Product Visual = `product`, Price = `price`, Product Name =
`headline`, Slogan = `tagline`, Logo = `logo`. Brainsight numbers boxes in drawing order: price,
product, logo, headline, tagline.
**Limits.** Both tools report whole percentages. Brainsight has no AOI data export, so its values
are typed from screenshots. Attention Insight's area percentages are not simple shares of one
total (its own summary total differs from their sum), and neither tool reports `rest`.
**Effect.** `external_tools` in the study file now names these two tools and the metrics they
export. No DeepGaze metric, threshold or output changed.
