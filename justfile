# Shortcuts for the pipeline. Needs `just` (brew install just). List recipes: `just`.
# Every study recipe takes the study folder as an optional argument (default: data), e.g.
#   just run                      # the real study in data/
#   just run examples/placeholder
# All outputs are predicted attention from DeepGaze IIE, not real eye-tracking.

# Read a git-ignored .env, if present, so the AOI recipes can find ANTHROPIC_API_KEY.
set dotenv-load

py := ".venv/bin/python -m src.glance_attention"

# List the recipes
default:
    @just --list --unsorted

# Create the environment (safe to rerun) and install the dev tools
setup:
    ./setup.sh
    .venv/bin/pip install -r requirements-dev.txt

# Draw the AOI boxes on the images; list them in pixels and %
preview study="data":
    {{py}} preview --study {{study}}

# Check images and AOIs, then lock the AOIs
validate study="data":
    {{py}} validate --study {{study}}

# Run the model; needs locked AOIs
run study="data":
    {{py}} run --study {{study}}

# Recompute tables and images from saved densities, without the model
rerun study="data":
    {{py}} run --skip-model --study {{study}}

# Deltas against the baseline and the key test
compare study="data":
    {{py}} compare --study {{study}}

# Write report.md and cross_tool_long.csv
report study="data":
    {{py}} report --study {{study}}

# run, compare and report in one go. Validate (and commit the lock) first: this never re-locks AOIs
analyse study="data": (run study) (compare study) (report study)

# An AI proposes AOI boxes for one variant (needs ANTHROPIC_API_KEY)
aoi-propose variant study="data":
    {{py}} aoi propose {{variant}} --study {{study}}

# Adopt a reviewed proposal as aois/<variant>.json
aoi-apply variant study="data":
    {{py}} aoi apply {{variant}} --study {{study}}

# Regenerate the placeholder images and AOI files
placeholder:
    {{py}} placeholder --study examples/placeholder

# Full placeholder flow, end to end (outputs are marked PLACEHOLDER, not results)
demo: placeholder (preview "examples/placeholder") (validate "examples/placeholder") (analyse "examples/placeholder")

# Format and lint
lint:
    .venv/bin/ruff format src tests
    .venv/bin/ruff check src tests

# Fast tests, no model
test:
    .venv/bin/pytest -m "not slow"

# The real-model smoke test
test-slow:
    .venv/bin/pytest -m slow

# Lint and fast tests
check: lint test
