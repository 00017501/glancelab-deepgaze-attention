# Promo price position: predicted attention (DeepGaze IIE)

_Predicted free-viewing attention from DeepGaze IIE (Linardos et al., 2021). Not real eye-tracking._

## Run

- Run date (UTC): 2026-11-23T04:06:49+00:00
- Model: DeepGaze IIE, DeepGaze commit `c7db17e`, device `cpu`
- Pipeline: version 0.1.0, commit `3623957` (uncommitted changes present)
- Images: 3 variants, 1080 x 1350 px; baseline `A`
- AOIs locked (UTC): 2026-11-23T03:58:09+00:00, before this model run

## Attention share per AOI (primary: MIT1003 centre bias)

| Variant | price % | product % | logo % | headline % | tagline % | rest % | Clarity (0-1) | First-look order (by peak) |
|---|---|---|---|---|---|---|---|---|
| A (baseline) | 5.9 | 29.6 | 1.7 | 12.8 | 29.7 | 20.4 | 0.168 | tagline > headline > product > price > logo |
| B | 20.1 | 24.0 | 1.4 | 11.4 | 24.9 | 18.3 | 0.180 | price > tagline > headline > product > logo |
| C | 11.2 | 27.1 | 1.5 | 12.9 | 28.1 | 19.1 | 0.172 | tagline > price > headline > product > logo |

## Key test against baseline A

Does the price share go up while the product share holds? A variant is flagged when its product share falls by more than 10% of the baseline product share.

| Variant | Price % | Price change (pp) | Product % | Product change (% of baseline) | Product density change (%) | Verdict |
|---|---|---|---|---|---|---|
| B | 20.1 | 14.23 | 24.0 | -18.8 | -18.8 | price share up; PRODUCT DROP FLAGGED |
| C | 11.2 | 5.35 | 27.1 | -8.3 | -8.3 | price share up; product held |

## Per-variant AOI tables (primary)

### Variant A

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 5.9 | 2.5 | 2.37 | 4 | 4 |
| product | product | 29.6 | 28.1 | 1.05 | 2 | 3 |
| logo | logo | 1.7 | 0.9 | 1.79 | 5 | 5 |
| headline | headline | 12.8 | 1.4 | 8.85 | 3 | 2 |
| tagline | text | 29.7 | 1.7 | 17.35 | 1 | 1 |
| rest | rest | 20.4 | 65.3 | 0.31 |  |  |

### Variant B

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 20.1 | 2.5 | 8.12 | 3 | 1 |
| product | product | 24.0 | 28.1 | 0.85 | 2 | 4 |
| logo | logo | 1.4 | 0.9 | 1.45 | 5 | 5 |
| headline | headline | 11.4 | 1.4 | 7.86 | 4 | 3 |
| tagline | text | 24.9 | 1.7 | 14.52 | 1 | 2 |
| rest | rest | 18.3 | 65.3 | 0.28 |  |  |

### Variant C

| AOI | Type | % attention | % area | Density | Share rank | First-look rank |
|---|---|---|---|---|---|---|
| price | price | 11.2 | 2.5 | 4.53 | 4 | 2 |
| product | product | 27.1 | 28.1 | 0.96 | 2 | 4 |
| logo | logo | 1.5 | 0.9 | 1.66 | 5 | 5 |
| headline | headline | 12.9 | 1.4 | 8.94 | 3 | 3 |
| tagline | text | 28.1 | 1.7 | 16.38 | 1 | 1 |
| rest | rest | 19.1 | 65.3 | 0.29 |  |  |

## Sensitivity: no centre bias

The same metrics with a uniform prior. The centre bias favours central positions, so a position that wins only in the primary table may be winning because it is central.

| Variant | price % | product % | logo % | headline % | tagline % | rest % | Clarity (0-1) | First-look order (by peak) |
|---|---|---|---|---|---|---|---|---|
| A (baseline) | 13.9 | 14.3 | 9.0 | 12.4 | 19.8 | 30.6 | 0.169 | price > logo > tagline > headline > product |
| B | 12.3 | 14.5 | 9.2 | 13.6 | 20.7 | 29.6 | 0.170 | logo > price > tagline > headline > product |
| C | 12.5 | 14.5 | 9.2 | 13.6 | 20.5 | 29.6 | 0.170 | logo > price > tagline > headline > product |

| Variant | Price % | Price change (pp) | Product % | Product change (% of baseline) | Product density change (%) | Verdict |
|---|---|---|---|---|---|---|
| B | 12.3 | -1.54 | 14.5 | 1.0 | 1.0 | price share not up; product held |
| C | 12.5 | -1.31 | 14.5 | 0.9 | 0.9 | price share not up; product held |

## Robustness: jittered AOI boxes

Every box edge was moved at random by up to 5% of the box's width or height, 200 times (seed 20261122). Shares are % of predicted attention.

| Variant | Prior | AOI | Share | Jitter mean | SD | Min | Max |
|---|---|---|---|---|---|---|---|
| A | mit1003 | price | 5.86 | 5.82 | 0.23 | 5.42 | 6.23 |
| A | mit1003 | product | 29.55 | 29.52 | 0.32 | 28.75 | 30.14 |
| A | uniform | price | 13.85 | 13.77 | 0.37 | 13.02 | 14.50 |
| A | uniform | product | 14.34 | 14.39 | 0.24 | 13.81 | 15.11 |
| B | mit1003 | price | 20.09 | 20.00 | 0.35 | 19.21 | 20.76 |
| B | mit1003 | product | 23.99 | 23.96 | 0.27 | 23.32 | 24.48 |
| B | uniform | price | 12.32 | 12.26 | 0.22 | 11.80 | 12.74 |
| B | uniform | product | 14.49 | 14.53 | 0.24 | 13.95 | 15.25 |
| C | mit1003 | price | 11.22 | 11.17 | 0.22 | 10.71 | 11.64 |
| C | mit1003 | product | 27.10 | 27.07 | 0.29 | 26.36 | 27.64 |
| C | uniform | price | 12.54 | 12.49 | 0.23 | 12.03 | 13.00 |
| C | uniform | product | 14.47 | 14.51 | 0.24 | 13.94 | 15.23 |

How often a conclusion stays the same as with the original boxes:

| Prior | Check | Unchanged (% of draws) |
|---|---|---|
| mit1003 | price_share_order | 100.0 |
| mit1003 | product_drop_flag:B | 100.0 |
| mit1003 | product_drop_flag:C | 100.0 |
| uniform | price_share_order | 100.0 |
| uniform | product_drop_flag:B | 100.0 |
| uniform | product_drop_flag:C | 100.0 |

## Reading notes

- Density = attention % divided by area %; above 1 means the AOI draws more attention than its size.
- Where the 'price' box covers another AOI, those pixels count for 'price' only.
- First-look order ranks AOIs by their peak predicted density. It is not a scanpath.
- Clarity barely differs between variants of one ad; do not read small differences into it.
- Predicted free-viewing attention from DeepGaze IIE (Linardos et al., 2021). Not real eye-tracking.
