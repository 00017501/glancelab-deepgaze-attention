<div align="center">

# Where should the promo price go?

Predicted attention for versions of one furniture ad that differ only in where the price tag sits

[What you get](#what-you-get) · [Set it up](#set-it-up) · [Use it](#use-it) · [What is where](#what-is-where) · [Documents](#documents)

</div>

<table align="center">
  <tr>
    <td align="center">
      <br>
      <sub><b>RESEARCH QUESTION</b></sub>
      <h3>Where should the promo price go so that it is noticed and remembered,<br>without reducing attention on the product?</h3>
    </td>
  </tr>
</table>

> [!WARNING]
> **Predicted attention, not real eye-tracking.** Every number and heatmap here comes from a model (DeepGaze IIE). It says nothing about memory or about real viewers.

> [!NOTE]
> **No results yet.** The real ads do not exist yet. Every picture on this page is from grey-box placeholder images, marked **PLACEHOLDER – not results**.

## The idea

| | |
|---|---|
| **What we test** | Several versions of one ad, identical except for the position of the price tag |
| **The baseline** | Version A, with the price in the usual place. Every other version is compared with it |
| **What counts as better** | The price gets more attention **and** the product keeps its share. A price that pulls attention off the product is a bad result |
| **The tool** | DeepGaze IIE, a free research model that predicts where people are likely to look at an image |
| **Where it fits** | One of three attention tools in a group coursework (CW2). All three feed one shared table |

**Read more →** [what the study does and does not claim](docs/METHOD.md) · [why each choice was made](docs/DECISIONS.md)

---

## What you get

### 1. All versions side by side

Brighter means more predicted attention. Each box shows its share of it.

![Placeholder panel: versions A, B and C side by side with boxes and shares](examples/placeholder/output/PLACEHOLDER_panel.png)

### 2. Each version, step by step

<table>
  <tr>
    <th align="center">Image</th>
    <th align="center">Areas to measure</th>
    <th align="center">Heatmap</th>
    <th align="center">Share per area</th>
  </tr>
  <tr>
    <td><img src="examples/placeholder/images/C.png" width="200" alt="Placeholder version C"></td>
    <td><img src="examples/placeholder/output/preview/PLACEHOLDER_C_aois.png" width="200" alt="Boxes drawn on placeholder version C"></td>
    <td><img src="examples/placeholder/output/heatmaps/PLACEHOLDER_C_heatmap.png" width="200" alt="Predicted heatmap for placeholder version C"></td>
    <td><img src="examples/placeholder/output/heatmaps/PLACEHOLDER_C_aoi.png" width="200" alt="Heatmap with boxes and shares for placeholder version C"></td>
  </tr>
</table>

### 3. The answer, version by version

| Version | Price share | Change vs A | Product change vs A | Verdict |
|:---:|---:|---:|---:|---|
| **B** | 15.4% | −0.7 points | +2.8% | price not up; product held |
| **C** | 37.9% | +21.8 points | −3.0% | **price up; product held** |

<sub>Placeholder values, not results.</sub>

It also writes the tables behind these, a written summary, and the shared table for all three tools.

**Read more →** [every output explained, with examples](docs/ANALYSIS_GUIDE.md) · [how each number is calculated](docs/METHOD.md)

---

## Set it up

**You need:** Python 3.13, git and [`just`](https://github.com/casey/just), a small tool that gives the commands short names.

| System | What to do first |
|---|---|
| **macOS** | `brew install just python@3.13` |
| **Linux** | Install Python 3.13, git and `just` with your package manager |
| **Windows** | Install WSL (`wsl --install` in PowerShell), open Ubuntu, then follow the Linux steps inside it |

**Then, on any system:**

```bash
git clone https://github.com/00017501/glancelab-deepgaze-attention.git
cd glancelab-deepgaze-attention
just setup    # installs everything; takes a few minutes
just demo     # runs the whole thing on the placeholder images
```

> [!NOTE]
> The first run downloads the model (about 1 GB). It has been run on macOS only so far.

**Read more →** [setup step by step for each system](docs/SETUP.md)

---

## Use it

| Step | Command | What it does |
|:---:|---|---|
| 1 | `just preview` | Draws the measured areas on each image so you can check them |
| 2 | `just validate` | Checks the images and areas, then locks the areas |
| 3 | `just run` | Runs the model and makes the heatmaps and tables |
| 4 | `just compare` | Compares every version with the baseline |
| 5 | `just report` | Writes the summary and the shared table |
| – | `just demo` | Does all of the above on the placeholder images |

`just` on its own lists every command.

> [!IMPORTANT]
> The areas are locked in step 2, before the model runs. No box can be adjusted after a heatmap has been seen.

**Read more →** [using it on the real ads, step by step](docs/ANALYSIS_GUIDE.md) · [making the area files](docs/AOI_GENERATION.md)

---

## What is where

| Folder | What is in it |
|---|---|
| `data/` | The real study: put the ad images and area files here |
| `examples/placeholder/` | The placeholder study and its example outputs |
| `docs/` | The guides and the method |
| `updates/` | Status updates for the group |
| `src/`, `tests/` | The code and its tests |

Results land in an `output/` folder inside the study: `data/output/` for the real ads.

**Read more →** [which file comes from which step](docs/ANALYSIS_GUIDE.md#where-everything-ends-up)

---

## Documents

| Document | Read it when you want to |
|---|---|
| [Setup](docs/SETUP.md) | Install it on macOS, Linux or Windows |
| [Analysis guide](docs/ANALYSIS_GUIDE.md) | Run the real ads, and see what every step produces |
| [AOI generation](docs/AOI_GENERATION.md) | Make the files that say which areas are measured |
| [Method](docs/METHOD.md) | Know how each number is calculated, and the limits |
| [Decisions](docs/DECISIONS.md) | Know why each choice was made |
| [AI use and prompts](docs/AI_USE_AND_PROMPTS.md) | See which steps were AI-assisted, and how |

---

<sub>MIT licence, see [LICENSE](LICENSE). Model: Linardos, A., Kümmerer, M., Press, O. and Bethge, M. (2021) 'DeepGaze IIE: Calibrated prediction in and out-of-domain for state-of-the-art saliency modeling', <i>ICCV 2021</i>. Code: <a href="https://github.com/matthias-k/DeepGaze">github.com/matthias-k/DeepGaze</a></sub>
