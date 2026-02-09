# Copy/paste: Make.com “Additional information” text (per scenario)

Use these in the Make.com share dialog.

## 1) Category Prompt Dispatcher (Main scenario)
What it does
- Orchestrator. Watches Airtable Projects for records marked ready-to-run, marks them as “Running”, and calls sub-scenarios in order:
  2) Run Category Prompts → 3) Extract Category Factors → 4) Generate Factor Values → 5) Run Factor Tests → 6) Category Brand Metrics.

Important
- Make only shares the main scenario. To fully replicate:
  - Share/import each sub-scenario separately.
  - Reconnect every “Call a scenario” module to the imported sub-scenarios (2→3→4→5→6).
  - Point Airtable modules to your base/tables/fields.

Input
- Airtable Project record (Category Name, Target Audience, optional Target Brand/Country).

## 2) Run Category Prompts
What it does
- Generates a list of realistic buyer-style prompts for a category + target audience, stores them as “Generic” Runs in Airtable, then hands off to Scenario 3.

Called by
- Scenario 1

Reconnect
- Airtable connection/base/tables
- Final “Call a scenario” module → Scenario 3

## 3) Extract Category Factors
What it does
- Extracts the decision factors that change the “best tool” answer (e.g., company size, pricing, industry constraints), parses strict JSON, creates Factor records, then calls Scenario 4.

Called by
- Scenario 2

Reconnect
- Airtable modules
- OpenAI module
- Final “Call a scenario” module → Scenario 4

## 4) Generate Factor Values
What it does
- For each factor, generates discrete values (4–8) to test, creates Factor Value records, then calls Scenario 5.

Called by
- Scenario 3

Reconnect
- Airtable modules
- Final “Call a scenario” module → Scenario 5

## 5) Run Factor Tests
What it does
- Runs the prompt under each factor-value scenario, stores each response as a “Factor” Run in Airtable (Raw Answer), then calls Scenario 6.

Called by
- Scenario 4

Reconnect
- Airtable modules
- OpenAI module
- Final “Call a scenario” module → Scenario 6

## 6) Category Brand Metrics
What it does
- Converts raw model answers into structured metrics (ranking + sentiment + snippet + fit) and sources/citations (URL/domain/type). Writes into Airtable Brand Metrics + Sources and marks the Project as “Ready for Report”.

Called by
- Scenario 5

Reconnect
- Airtable modules for Runs/Metrics/Sources
- OpenAI module(s)
