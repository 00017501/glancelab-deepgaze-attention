# Exports from the commercial attention tools

> Everything here is **predicted** attention from third-party models, not real eye-tracking.

Collected on 2026-11-23 by uploading the clean ad images in `../images/` (no boxes or labels) and
drawing the locked AOIs from `../aois/` in each tool. Raw exports are kept as downloaded; only the
file names were shortened.

## Attention Insight

- Settings: asset type Advertising, channel Social Ads, objective Product Highlight.
- Per variant: `aoi_data.csv` (attention per area, and each box as % of the image), the exported
  images (`heatmap`, `saliency`, `focus`, `contrast`, `aoi`, `original`) and `validation_report.pdf`.
- Area names in the tool: Product Visual = `product`, Price = `price`, Product Name = `headline`,
  Slogan = `tagline`, Logo = `logo`.
- The tool reports attention to two decimals of a fraction (whole percent).
- B and C were first analysed with A's price box by mistake (the tool copied A's areas to them).
  Both were redrawn with the price box on the tag and analysed again; the exports here are from
  those second analyses, named "B redraw" and "C redraw" in the tool.

## Brainsight

- Settings: type Social media.
- Per variant: the downloaded heatmap, gaze plot, peek-through and template images.
- The tool has no AOI data export. `aoi_values.csv` and `image_scores.csv` were typed from the
  screenshots in `brainsight/screenshots/`. Boxes are numbered in drawing order: Box 1 `price`,
  Box 2 `product`, Box 3 `logo`, Box 4 `headline`, Box 5 `tagline`.

## How closely the boxes match the locked AOIs

Boxes were drawn by mouse, so they cannot be pixel-exact. Read back from each tool's page, every
edge is within 2 px of the locked box on the 1080 x 1350 image. The jitter check in the pipeline
moves edges by up to 5 % of the box size, which is larger than this.
