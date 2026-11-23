# Method

> All values are **predicted** free-viewing attention from DeepGaze IIE (Linardos et al., 2021).
> They are not real eye-tracking and say nothing about memory.

Decisions are referenced as D1, D2, ... and explained in [DECISIONS.md](DECISIONS.md).

## 0. What is being tested

Research question: where should the promo price go so it is noticed and remembered, without reducing
attention on the product?

This is a placement decision with a trade-off (D14):

- **A comparison against a baseline, not a diagnosis.** Version A has the price in the conventional
  position. The other versions move it to positions expected to draw more attention. Every result is
  a difference from A. Nothing here says whether the price is noticed too little in the
  advertiser's current ads; there is no data on those.
- **Two conditions, both required.** A version is better than A only if the price's share of
  predicted attention goes up **and** the product's share is held (D7). Maximising attention
  on the price alone is not the goal: a price that takes attention from the product fails.
- **Chosen in advance.** The versions, the AOIs and the threshold are fixed before the model runs,
  so the comparison is a planned test and not a search through variations for a good-looking number.
- **Noticed, not remembered.** The model predicts where people look. The *remembered* half of the
  question is outside what it can show (section 6).

## 1. Stimuli

Three or more versions of one static ad. They are identical except for the position of the promo
price tag: one moved layer with the same size, colour and text. Version A, the conventional
placement, is the baseline. All versions must have the same pixel size; `validate` stops otherwise.

Until the real ads exist, the pipeline runs on generated placeholders (1080 x 1350 px): a plain
background, a grey product shape, a logo block, a headline bar and a red PRICE box at three
positions (D3). Their outputs are marked **PLACEHOLDER – not results**.

## 2. Model

- DeepGaze IIE, pretrained, from the official repository at a pinned commit (`setup.sh`), with one
  patch that makes an unused import optional (D1).
- Run on the CPU at the image's native resolution, one image at a time.
- **Primary prior:** the MIT1003 centre bias, resized to the image and renormalised.
- **Sensitivity prior:** uniform, meaning no centre bias (D6). The centre bias favours central
  positions, and position is the thing varied here, so every metric is computed under both.
- The model's log-density is exponentiated and normalised to sum to 1. Each pixel then holds a share
  of predicted attention.

### The centre bias and MIT1003, in plain terms

- **Saliency model.** DeepGaze IIE looks at an image and estimates, for every pixel, how likely a
  viewer is to look there. It was trained on recordings of where real people looked at other images.
- **Centre bias.** Across almost any set of pictures, people look at the middle more than the
  edges, whatever is shown: photographers centre their subject, and eyes start from the middle of
  a screen. A saliency model has to account for this to match real viewing.
- **Prior.** DeepGaze takes this tendency as a separate input, called a prior: a map saying how
  likely each position is to be looked at before the image content is considered. The model
  combines it with what it finds in the image.
- **MIT1003.** A public eye-tracking dataset of 1003 images, each viewed freely for three seconds
  by 15 people (Judd et al., 2009). The prior used here is the average of where those viewers
  looked across the whole dataset, published with DeepGaze as `centerbias_mit1003.npy`. It is
  densest in the middle and fades towards the edges.
- **Uniform prior.** A flat map: every position equally likely. Using it removes the centre bias,
  so what remains is the model's response to the image content alone.

Why both are reported: this study moves one element to different positions. With the MIT1003
prior, an element nearer the middle gains predicted attention simply for being there. Comparing the
two sets separates "this position sits where people tend to look" from "this element stands out
more". Neither is the true answer. The MIT1003 set is closer to how people view images in general;
the uniform set shows how much of a result depends on that general tendency.

Reference: Judd, T., Ehinger, K., Durand, F. and Torralba, A. (2009) 'Learning to predict where
humans look', *IEEE 12th International Conference on Computer Vision*, pp. 2106-2113.

## 3. AOIs

- One AOI file per variant, `aois/<variant>.json`. Boxes are `[x0, y0, x1, y1]` in image pixels.
- AOIs: `price`, `product`, `logo`, `headline`, plus `rest` (every pixel outside all boxes), which is
  computed.
- `product`, `logo` and `headline` are identical in every variant; only `price` moves, and its box
  keeps the same size. `validate` enforces both.
- **Overlap rule (D4):** where the price box covers another AOI, those pixels count for `price` only.
  Every pixel belongs to exactly one AOI, so shares always sum to 100%.
- **Fixed before the model (D5):** `validate` locks the AOI files by SHA-256 and time in
  `aoi_lock.json`. `run` refuses to start unless the files match the lock, and writes the hashes and
  lock time into the run log before the model is loaded. If a later run uses different AOIs, the run
  log and the report say so.
- AOI boxes for the real ads are proposed by an AI and confirmed by a person (D9,
  [AOI_GENERATION.md](AOI_GENERATION.md)). The same boxes are redrawn by hand in the two commercial
  tools from the pixel and % list that `preview` writes.

## 4. Metrics

Per variant and AOI:

| Metric | Definition | Reading |
|---|---|---|
| `share_pct` (attention %) | 100 x sum of the density inside the AOI | Share of predicted attention |
| `area_pct` | 100 x AOI pixels / image pixels | Size of the AOI |
| `density` (attention density) | `share_pct / area_pct` | Above 1: more attention than its size alone would get. Makes AOIs of different size comparable |
| `peak` | Highest density in the AOI x 1e6 | Strength of the hottest point |
| `share_rank` (AOI rank) | Order of the drawn AOIs by share, 1 = highest | |
| `first_look_rank` | Order of the drawn AOIs by peak, 1 = highest | A proxy for what draws the eye first. **Not a scanpath** |

Per variant:

| Metric | Definition | Reading |
|---|---|---|
| `entropy_norm` | Shannon entropy of the density pooled on a 10 px grid, divided by its maximum | 0-1, lower = more focused |
| `clarity` | `1 - entropy_norm` | 0-1, higher = more focused |
| `top10_pct` | % of attention in the 10% most-attended pixels | Concentration |
| `first_look_order` | AOI names in first-look rank order | |

**Comparison against the baseline (D7).** For every AOI and metric: the difference (variant minus
baseline) and the difference as a % of the baseline value. The key test per variant:

- *price up*: price share is higher than in the baseline;
- *product held*: product share fell by no more than `product_drop_threshold_pct` (default 10) % of
  the baseline product share. Otherwise the variant is flagged.

The product's density change is shown next to it: when the price sits on the product, the product
loses area, and density shows whether the remaining product area lost attention too.

**Robustness (D8).** Every box edge is moved at random by up to ±5% of the box's width or height,
200 times with a fixed seed. One draw moves an AOI the same way in every variant, as if one person
had drawn the boxes slightly differently. Reported: mean, SD, minimum and maximum of each share, and
how often the price-share ordering of the variants and each product-drop flag stay unchanged.

## 5. Procedure

1. Put the images in `images/` and write `study.toml`.
2. Produce the AOI files ([AOI_GENERATION.md](AOI_GENERATION.md)) and check them with `preview`.
3. `validate`: checks, then locks the AOIs.
4. `run`: model under both priors, tables, heatmaps, panels, jitter, run log.
5. `compare`, then `report`.

Heatmaps of all variants share one colour scale per prior (D10), so colours can be compared across
variants.

## 6. Limitations

- **Predicted, not measured.** DeepGaze IIE predicts where people tend to look in free viewing of
  photographs. It was not trained on ads, has no reading model and no notion of price or brand.
- **No memory.** The research question asks about being *remembered*. This tool can only speak to
  being *noticed*; memory needs the group's other evidence.
- **Centre bias and position are confounded.** That is why the no-centre-bias set is reported. A
  position that wins only with the centre bias should be described as such.
- **First-look order is not a scanpath.** It ranks AOIs by peak density.
- **Clarity barely separates variants of one ad**, since only one small element moves.
- **AOI choices matter.** The jitter check shows how much; it does not remove the dependence.
- **Cross-tool numbers are not on one scale.** The `scale` column records each tool's own scale;
  compare directions and rankings across tools, not raw values.
