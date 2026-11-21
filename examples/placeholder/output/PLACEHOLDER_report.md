# PLACEHOLDER price-position study: predicted attention (DeepGaze IIE)

> **PLACEHOLDER – NOT RESULTS.** Generated from placeholder images. Never cite these numbers.

_Predicted free-viewing attention from DeepGaze IIE (Linardos et al., 2021). Not real eye-tracking._

## Run

- Run date (UTC): 2026-11-21T20:06:12+00:00
- Model: DeepGaze IIE, DeepGaze commit `c7db17e`, device `cpu`
- Pipeline: version 0.1.0, commit `a22b527`
- Images: 3 variants, 1080 x 1350 px; baseline `A`
- AOIs locked (UTC): 2026-11-21T19:59:47+00:00, before this model run

## Attention share per AOI (primary: MIT1003 centre bias)

| Variant | price % | logo % | headline % | product % | rest % | Clarity (0-1) | First-look order (by peak) |
|---|---|---|---|---|---|---|---|
| A (baseline) | 16.1 | 5.8 | 47.3 | 11.9 | 18.9 | 0.194 | headline > price > logo > product |
| B | 15.4 | 6.1 | 48.4 | 12.2 | 17.9 | 0.197 | headline > price > logo > product |
| C | 37.9 | 4.1 | 33.9 | 11.5 | 12.6 | 0.219 | price > headline > product > logo |

## Key test against baseline A

Does the price share go up while the product share holds? A variant is flagged when its product share falls by more than 10% of the baseline product share.

| Variant | Price % | Price change (pp) | Product % | Product change (% of baseline) | Product density change (%) | Verdict |
|---|---|---|---|---|---|---|
| B | 15.4 | -0.72 | 12.2 | 2.8 | 2.8 | price share not up; product held |
| C | 37.9 | 21.76 | 11.5 | -3.0 | 3.9 | price share up; product held |

## Per-variant AOI tables (primary)

### Variant A

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 16.1 | 2.2 | 7.32 | 2 | 2 |
| logo | logo | 5.8 | 1.4 | 4.19 | 4 | 3 |
| headline | headline | 47.3 | 5.9 | 7.99 | 1 | 1 |
| product | product | 11.9 | 24.0 | 0.49 | 3 | 4 |
| rest | rest | 18.9 | 66.5 | 0.28 |  |  |

### Variant B

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 15.4 | 2.2 | 6.99 | 2 | 2 |
| logo | logo | 6.1 | 1.4 | 4.37 | 4 | 3 |
| headline | headline | 48.4 | 5.9 | 8.18 | 1 | 1 |
| product | product | 12.2 | 24.0 | 0.51 | 3 | 4 |
| rest | rest | 17.9 | 66.5 | 0.27 |  |  |

### Variant C

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 37.9 | 2.2 | 17.19 | 1 | 1 |
| logo | logo | 4.1 | 1.4 | 2.97 | 4 | 4 |
| headline | headline | 33.9 | 5.9 | 5.72 | 2 | 2 |
| product | product | 11.5 | 22.4 | 0.51 | 3 | 3 |
| rest | rest | 12.6 | 68.1 | 0.18 |  |  |

## Sensitivity: no centre bias

The same metrics with a uniform prior. The centre bias favours central positions, so a position that wins only in the primary table may be winning because it is central.

| Variant | price % | logo % | headline % | product % | rest % | Clarity (0-1) | First-look order (by peak) |
|---|---|---|---|---|---|---|---|
| A (baseline) | 27.5 | 17.4 | 30.4 | 4.7 | 20.0 | 0.202 | price > logo > headline > product |
| B | 29.3 | 17.3 | 29.9 | 4.7 | 18.8 | 0.207 | price > logo > headline > product |
| C | 29.0 | 17.5 | 29.8 | 6.7 | 17.0 | 0.205 | price > logo > headline > product |

| Variant | Price % | Price change (pp) | Product % | Product change (% of baseline) | Product density change (%) | Verdict |
|---|---|---|---|---|---|---|
| B | 29.3 | 1.83 | 4.7 | -1.7 | -1.7 | price share up; product held |
| C | 29.0 | 1.46 | 6.7 | 42.1 | 52.3 | price share up; product held |

## Robustness: jittered AOI boxes

Every box edge was moved at random by up to 5% of the box's width or height, 200 times (seed 20261122). Shares are % of predicted attention.

| Variant | Prior | AOI | Share | Jitter mean | SD | Min | Max |
|---|---|---|---|---|---|---|---|
| A | mit1003 | price | 16.13 | 16.06 | 0.24 | 15.43 | 16.58 |
| A | mit1003 | product | 11.87 | 11.74 | 1.17 | 9.30 | 14.05 |
| A | uniform | price | 27.51 | 27.39 | 0.35 | 26.37 | 28.20 |
| A | uniform | product | 4.73 | 4.68 | 0.51 | 3.54 | 5.81 |
| B | mit1003 | price | 15.41 | 15.37 | 0.21 | 14.79 | 15.88 |
| B | mit1003 | product | 12.20 | 12.07 | 1.21 | 9.57 | 14.41 |
| B | uniform | price | 29.34 | 29.24 | 0.37 | 28.10 | 30.14 |
| B | uniform | product | 4.65 | 4.60 | 0.49 | 3.50 | 5.67 |
| C | mit1003 | price | 37.89 | 37.74 | 0.46 | 36.44 | 38.78 |
| C | mit1003 | product | 11.51 | 11.48 | 0.99 | 9.26 | 13.61 |
| C | uniform | price | 28.97 | 28.86 | 0.35 | 27.85 | 29.64 |
| C | uniform | product | 6.72 | 6.70 | 0.64 | 5.28 | 8.27 |

How often a conclusion stays the same as with the original boxes:

| Prior | Check | Unchanged (% of draws) |
|---|---|---|
| mit1003 | price_share_order | 100.0 |
| mit1003 | product_drop_flag:B | 100.0 |
| mit1003 | product_drop_flag:C | 97.5 |
| uniform | price_share_order | 98.5 |
| uniform | product_drop_flag:B | 100.0 |
| uniform | product_drop_flag:C | 100.0 |

## Reading notes

- Density = attention % divided by area %; above 1 means the AOI draws more attention than its size.
- Where the 'price' box covers another AOI, those pixels count for 'price' only.
- First-look order ranks AOIs by their peak predicted density. It is not a scanpath.
- Clarity barely differs between variants of one ad; do not read small differences into it.
- Predicted free-viewing attention from DeepGaze IIE (Linardos et al., 2021). Not real eye-tracking.
