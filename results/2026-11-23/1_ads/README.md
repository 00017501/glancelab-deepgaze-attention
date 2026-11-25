# 1. The ad versions

[Back to the overview](../README.md)

| File | Price tag position |
|---|---|
| `A.png` | top right (the baseline, the conventional place) |
| `B.png` | middle right |
| `C.png` | bottom right |
| `base_no_price.png` | no tag; the ad the versions were built from |

All files are 1080 × 1350 px. These are the clean images exactly as given to every tool, with no
boxes or labels on them.

## What was checked

Each version was compared with `base_no_price.png` pixel by pixel:

- The only difference is one block of 325 × 111 px, the price tag.
- The tag is identical in all three versions.
- The tag keeps the same horizontal position; only its height on the page changes.

So any difference between versions in the results comes from the tag's position and nothing else in
the image.
