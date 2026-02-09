# AI Category Visibility Map — Pipeline Snapshot

Live demo (submit a category + target audience and generate a report):
https://ai-category-map.saifqazi.com/

This repo is a public snapshot of the system behind the **AI Category Visibility Map** (aka “AI Category Map”).

## What is the AI Category Visibility Map?

It answers a simple question:

> “When a buyer asks an LLM what the best tools are for a category, which brands show up — and why?”

For a given **category prompt** (e.g., “best restaurant inventory software for multi-location operators”) the system:
- runs a **baseline** LLM answer,
- extracts the LLM’s own “it depends…” **decision factors** (follow-up qualifiers),
- generates realistic **segments** (values) for each factor (e.g., budget tiers, size bands, integration needs),
- re-runs the same prompt under each segment,
- extracts structured **visibility metrics** (brand mentions, rank/order, sentiment, sources),
- renders a single shareable HTML report.

This is an automation workflow (Make + Airtable + a Python report job), not a big application.

## Quick mental model (end-to-end)

1) **User submits** a category + target audience (and optionally brand/country).
2) Airtable marks the project as ready to run.
3) Make runs the **baseline** prompt (baseline Run saved).
4) Make extracts **factors** from the baseline answer (e.g., budget, team size, integrations).
5) Make generates **values** for each factor (segments) and runs each as additional Runs.
6) Make extracts **brand metrics + sources** from every Run into Airtable.
7) A Python job builds an HTML report from Airtable data and uploads it to S3.
8) Airtable gets updated with the **Report URL**.

## Architecture (stack)

- **Make.com** — orchestration (scenario chain)
- **Airtable** — datastore + queue/state (Projects, Runs, Brand Metrics, Sources, Factors/Values)
- **OpenAI API** — generates answers + extracts structured outputs
- **Python report factory** — builds the HTML report payload and publishes to S3
- **AWS S3** — public report hosting (static HTML)

More detail: `docs/architecture.md`

## Make.com scenarios (public + docs)

- Scenario walkthrough + public share links: `docs/make_scenarios.md`
- Copy/paste text for Make “Public share” fields: `docs/make_public_share_text.md`

**Difference between the two docs**
- `docs/make_scenarios.md` = the directory (links) + how the pipeline is wired (1→6).
- `docs/make_public_share_text.md` = short descriptions you paste into Make’s “Description / Additional information” boxes when you share each scenario publicly.

## Repo contents (what’s included)

- `src/report_factory.py` — pulls Runs/Metrics/Sources from Airtable, injects JSON into the HTML template, uploads report to S3, writes report URL back to Airtable.
- `templates/AI_Category_Snapshot_Jelly.html` — report UI template (expects a `// DATA_INJECTION_POINT` marker).
- `make/03_extract_category_factors.blueprint.redacted.json` — example Make blueprint export (IDs partially redacted).
- `assets/make/` — Make scenario screenshots.
- `docs/architecture.md` — end-to-end architecture.
- `docs/make_scenarios.md` — scenario directory + wiring.
- `docs/make_public_share_text.md` — copy/paste text for Make public sharing.
- `prompts/` — prompt templates used inside Make modules.

## What’s intentionally NOT included

- API keys / secrets / Make connections / credentials
- Airtable base data
- AWS bucket policies + deployment credentials

## How to reuse this

If someone wants to replicate the workflow:
1) Create an Airtable base with the required tables/fields (see `docs/architecture.md` for the contract).
2) Import the Make scenarios via the public share links (see `docs/make_scenarios.md`).
3) Rewire any “Call a scenario” modules after import (Make public sharing does not preserve sub-scenario targets).
4) Configure OpenAI + Airtable connections.
5) Run the Python report job (or adapt it) to publish reports to your S3 bucket.
