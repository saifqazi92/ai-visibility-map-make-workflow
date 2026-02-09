# Make.com Scenarios (Overview)

Screenshot index:
- `assets/make/Screenshot 2026-02-07 at 19.57.43.png` — scenario list
- `assets/make/Screenshot 2026-02-07 at 19.57.51.png` — Scenario 1
- `assets/make/Screenshot 2026-02-07 at 19.58.07.png` — Scenario 2
- `assets/make/Screenshot 2026-02-07 at 19.58.32.png` — Scenario 3
- `assets/make/Screenshot 2026-02-07 at 19.59.39.png` — Scenario 4
- `assets/make/Screenshot 2026-02-07 at 20.01.34.png` — Scenario 5
- `assets/make/Screenshot 2026-02-07 at 20.02.00.png` — Scenario 6


# Make.com scenarios (public share links)

After importing, rewire the **Scenarios → Call a scenario** modules:
1 → 2 → 3 → 4 → 5 → 6

1) Category Prompt Dispatcher (1/6)
https://eu2.make.com/public/shared-scenario/WCHLk57UKBS/1-category-prompt-dispatcher-1-6

2) Run Category Prompts (2/6)
https://eu2.make.com/public/shared-scenario/VyL37ZBfavt/2-run-category-prompts-2-6

3) Extract Category Factors (3/6)
https://eu2.make.com/public/shared-scenario/LO4cc3BQFy9/3-extract-category-factors-3-6

4) Generate Factor Values (4/6)
https://eu2.make.com/public/shared-scenario/k6TU2vlGNTw/4-generate-factor-values-4-6

5) Run Factor Tests (5/6)
https://eu2.make.com/public/shared-scenario/ls8hitY0lxH/5-run-factor-tests-5-6

6) Category Brand Metrics (6/6)
https://eu2.make.com/public/shared-scenario/NI1jLUyVgYh/6-category-brand-metrics-6-6


## Scenario 1 — Category Prompt Dispatcher (Main Orchestrator)
Trigger: Airtable Watch Records on Projects.
- Detects Projects marked ready to run
- Updates Project status to “Running/Processing”
- Calls sub-scenarios in order (2 → 3 → 4 → 5 → 6)
- Passes the Airtable Project Record ID forward

## Scenario 2 — Run Category Prompts
- Fetch Project record (category + target audience)
- Call OpenAI to generate a list of realistic buyer prompts
- Create Run records in Airtable (Run Type = Generic)
- Update Project and call Scenario 3

## Scenario 3 — Extract Category Factors
- Fetch Project + sample prompts
- Call OpenAI to extract decision factors (dimensions) that change the answer
- Parse strict JSON (Make JSON Parse)
- Create Factor records in Airtable
- Aggregate results and call Scenario 4

Blueprint export example:
- `make/03_extract_category_factors.blueprint.redacted.json`

## Scenario 4 — Generate Factor Values
- For each Factor, call OpenAI to produce discrete values (4–8)
- Parse JSON, iterate, create Factor Value records
- Aggregate + update Project and call Scenario 5

## Scenario 5 — Run Factor Tests
- For each Factor Value, generate a scenario-specific variant of the prompt
- Call OpenAI for an answer
- Store the Raw Answer in Airtable Runs (Run Type = Factor)
- Update status and call Scenario 6

## Scenario 6 — Category Brand Metrics
- Load Runs for the Project
- For each run, call OpenAI to extract:
  - brand ranking list (rank, sentiment, role, snippet, fit)
  - sources/citations (domain, url, type)
- Parse JSON; write to Airtable:
  - Brand Metrics table
  - Sources table (dedupe by URL/domain)
- Mark Project “Ready for Report” (picked up by the Python report factory)
