# AOI generation

> AOIs feed **predicted** attention metrics from DeepGaze IIE, not real eye-tracking.

AOIs must be fixed before any heatmap is generated. The order below keeps it that way.

Commands are `just` recipes (see the `justfile`); the study folder defaults to `data`.

## AOI file format

One file per variant, `aois/<variant>.json`:

```json
{
  "image": "A.png",
  "aois": {
    "price":    {"type": "price",    "boxes": [[778, 1134, 1016, 1269]]},
    "logo":     {"type": "logo",     "boxes": [[65, 68, 281, 162]]},
    "headline": {"type": "headline", "boxes": [[65, 216, 864, 324]]},
    "product":  {"type": "product",  "boxes": [[216, 486, 864, 1026]]}
  }
}
```

- Boxes are `[x0, y0, x1, y1]` in image pixels: top-left corner, then bottom-right.
- An AOI may have several boxes. Types: `price`, `product`, `logo`, `headline`, `text`, `visual`.
- `rest` is computed; never write it.
- A top-level key starting with `_` (such as `_note`) is ignored.
- Every AOI except `price` must be identical in all variants; the price box must keep its size.

## Steps for the real ads (AI proposes, a person confirms)

1. Export `ANTHROPIC_API_KEY` in your own terminal. It is never written to any file.
2. Baseline first:
   ```bash
   just aoi-propose A
   ```
   This writes `provenance/aois/data__A.json` (the proposal) and `data__A.meta.json` (the audit
   record). It never overwrites an earlier proposal.
3. Open the proposal. Correct any box by editing the numbers in that file; note what you changed
   for the log in [AI_USE_AND_PROMPTS.md](AI_USE_AND_PROMPTS.md) section 2c.
4. Adopt it:
   ```bash
   just aoi-apply A
   ```
5. Repeat `propose` and `apply` for each other variant. For these, `apply` takes **only the price
   box** from the proposal and copies product, logo and headline from the baseline's file.
6. `just preview`, and check every image in `data/output/preview/`.
7. `just validate` locks the files. Commit.

`apply` refuses to replace an existing AOI file and refuses boxes that fail the checks.

## Writing a file by hand

Allowed: read the coordinates from the design file and type them in the format above. Then
`preview` and `validate` as usual. Record in
[AI_USE_AND_PROMPTS.md](AI_USE_AND_PROMPTS.md) that the boxes were drawn by hand.

## Drawing the same AOIs in the commercial tools

`preview` writes `output/preview/aoi_boxes.csv` with each box in pixels and as left, top, width and
height in % of the image. Draw the boxes in each tool from those numbers so that all three tools
measure the same regions. Where a tool cannot subtract the price box from the product box, note it:
that tool's product value then includes the price pixels, unlike here (D4).

## Placeholders

`just placeholder` writes the images and the AOI files from the same
coordinates. No AI is involved, and the command refuses to write into a study that is not marked
`placeholder = true`.
