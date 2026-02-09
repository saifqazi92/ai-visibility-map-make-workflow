# AI Visibility Tracker — Context Pack (end-to-end)

## 0) Summary (for a brand-new chat)

This project generates an **AI Category Visibility Map** for a brand/category/country using ChatGPT answers.

High level:
- Run **one baseline category prompt** (“best X software for Y”) and store ranked brands + citations.
- From the baseline answer, extract the AI’s **follow-up qualifiers** (the “it depends / tell me…” questions).
- For each qualifier, generate a few **segments** (e.g., size bands, budget bands, existing-tools yes/no) and run those back as additional prompts.
- Store everything in Airtable.
- A PythonAnywhere script renders a single HTML report from Airtable data and uploads it to S3.

Terminology used in UI/report:
- **AI Category Visibility Map** = the report.
- **Follow-up qualifier** = a decision dimension the AI asks about (team size, budget, etc.).
- **Segment** = a concrete value within that qualifier (e.g., “50–149 employees”).

---

## 1) What the output report contains

The HTML report shows:

1) **Baseline prompt snapshot**
- Ranked brands
- Snippets
- Citations/links
- A “sources by page type” breakdown (Homepage / Pricing / Reviews / Blog, etc.)

2) **Follow-up qualifiers → segments**
- Each qualifier is a row/section (e.g., “Team size”, “Budget”, “Existing tools”)
- Each segment is a card (e.g., “50–149 employees”, “$500–$2k/mo”, “Uses Intercom”) showing:
  - rank outcome for target brand and competitors
  - drill-down: per-segment ranked brands + citations + sources

3) **Dashboard stats**
- Win rate across segments (wins/scenarios)
- Primary threat (brand that outranks target most often)

4) **Raw transcript modal**
- You can view the full baseline chat or per-segment chat
- Brand names get highlighted in the transcript

---

## 2) System architecture

**Stack**
- Airtable = source of truth for all runs/results + project queue
- Make.com = orchestration to generate runs (baseline + segments)
- PythonAnywhere = scheduled job to generate report HTMLs from Airtable
- AWS S3 = report hosting (public static files)

**Data flow (conceptual)**
1. A project is created/updated in Airtable (brand, category prompt, country, model).
2. Make.com runs the baseline prompt via OpenAI API and stores:
   - raw answer
   - extracted ranked brands & snippets
   - extracted sources/citations
   - extracted follow-up qualifiers
3. Make.com generates segments for each qualifier and runs those prompts.
4. Make.com writes all segment runs back to Airtable.
5. When a project is ready, its status is set to **“Ready for report”**.
6. PythonAnywhere script reads Airtable, builds a JSON payload, injects it into the HTML template, uploads to S3, and writes back the **Report URL** + changes status to **“Reported”**.

---

## 3) Airtable base (reporting script contract)

The report generator expects these tables + fields (names must match exactly):

### 3.1 Tables used by `report_factory.py`

**Projects** (`tblHR5Dh46C9qNmcA`)
- `Name` (Project Name)
- `Target Brand`
- `Status` (must include: `Ready for report`, `Reported`)
- `Report URL`
- `Country`

**Runs** (`tbll0JcGZ5kxYXVag`)
- `Project` (linked to Projects)
- `Run Type` (e.g., `Generic` baseline vs `Factor`/segment runs)
- `Prompt Text`
- `Target Brand (from Prompt)`
- `Factor Key`
- `Factor Label`
- `Value Key`
- `Value Label`  ✅ (human label for segment; optional in code but recommended)
- `Value Description (from Factor Tests)`
- `Model Used`
- `Raw Answer`

**Brand Metrics** (`tblbH5NbIIRoK5DeE`)
- `Run` (linked to Runs)
- `Brand`
- `Rank`
- `Mention Text`
- `Brand Role`
- `Sentiment`

**Sources** (`tblP2XlgbxdNEqJJs`)
- `Run` (linked to Runs)
- `Brand`
- `Source Type` (e.g., Homepage / Pricing / Review / Blog / Comparison)
- `URL`
- `Context Snippet`

### 3.2 Important note: the “Value Label” field

If Airtable does **not** have a field named exactly `Value Label` in the **Runs** table, Airtable API calls will fail with:
`UNKNOWN_FIELD_NAME: "Value Label"`.

Best practice:
- Store the canonical segment label in your “Factor Tests / Segment Definitions” table.
- Link Runs → that record, then use a **Lookup** field on Runs called `Value Label`.

Fallback behavior:
- If `Value Label` is blank, the script falls back to a prettified version of `Value Key` (e.g., `400_plus` → `400 Plus`).

---

## 4) Make.com scenarios (conceptual)

Exact modules can vary, but the intended sequence is:

### 4.1 Baseline run
1. Trigger (manual or scheduled).
2. Search Projects where Status indicates “needs run” (your choice) and/or where the project is active.
3. Create a baseline Run record (Run Type = `Generic`).
4. Call OpenAI API with `Prompt Text`.
5. Save `Raw Answer` to Runs.
6. Parse answer into:
   - Ranked brands list + snippet + rank + sentiment
   - Citations/sources per brand
7. Write:
   - Brand Metrics records linked to the run
   - Sources records linked to the run

### 4.2 Extract follow-up qualifiers
1. Feed `Raw Answer` into an extraction prompt that:
   - finds the “follow-up / tailoring” section
   - reads bullet points in that section
   - splits multi-factor bullets into separate factors
2. Store qualifiers somewhere (either a “Category Factors” table or directly into a “Factor Tests”/“Segments” table).

### 4.3 Generate segments per qualifier
For each qualifier:
1. Use the model to propose ~3–6 segments that are realistic for that category (size bands, budgets, etc.).
2. Store for each segment:
   - `Value Key` (machine)
   - `Value Label` (human)
   - `Value Description`

### 4.4 Segment runs
For each (qualifier × segment):
1. Create a Run record (Run Type = `Factor` or similar).
2. Set:
   - `Factor Key`, `Factor Label`
   - `Value Key`
   - `Value Description` (and optionally `Value Label` via lookup)
3. Construct the segment prompt:
   - baseline prompt + one additional constraint representing that segment
4. Call OpenAI API.
5. Save `Raw Answer`.
6. Parse and store:
   - Brand Metrics
   - Sources

### 4.5 Ready-for-report state
When all runs for a project are complete:
- set Project `Status` = **Ready for report**

---

## 5) PythonAnywhere report generator

### 5.1 Script
- Main script: `report_factory.py` (updated version: `report_factory_updated.py`)
- Function: fetch Airtable data → compute report payload → inject into HTML template → upload to S3 → write back Report URL.

### 5.2 Inputs
Environment variables required:
- `AIRTABLE_API_KEY`
- `AIRTABLE_BASE_ID`
- AWS credentials (either env vars or IAM instance role):
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION` (or configured in script)

### 5.3 Report template
- HTML template file: `AI_Category_Snapshot_Jelly.html`
- JSON injection point in template:
  - `var reportData = /* JSON_PAYLOAD_HERE */ { ... }; // DATA_INJECTION_POINT`

### 5.4 Core behavior (as implemented)

- Script searches Projects with `Status == "Ready for report"`.
- For each project:
  - loads all Runs for that project
  - identifies the **baseline** run (`Run Type == "Generic"`)
  - groups segment runs by `Factor Key` / `Factor Label`
  - builds a nested structure:
    - `project`: name, prompt, country, model, etc.
    - `baseline`: brands[], sourceStats[]
    - `factors`: [ { title, key, values: [ { name, desc, mentions[], sourceStats[], full_chat } ] } ]
    - `dashboard`: wins/scenarios/winRate/topThreat...

### 5.5 Using “Value Label” for segment titles
In the updated script:
- segment card title uses:
  - `Value Label` if present, else
  - formatted `Value Key`

Relevant code (conceptually):
- `ui_name = run.get("Value Label") or format_title(val_key)`

So the only requirement to show human labels is:
- ensure Runs has a populated `Value Label` field.

---

## 6) AWS S3 hosting

Configured in script:
- Bucket: `ai-visibility-tracker-reports`
- Region: `eu-north-1`
- Key prefix: `reports/`

Upload behavior:
- uploads HTML to: `reports/{slug}_report.html`
- writes Project `Report URL` to:
  - `https://{bucket}.s3.{region}.amazonaws.com/reports/{slug}_report.html`

---

## 7) Report UI naming (current intended nomenclature)

Use these labels in the report:
- Title: **AI Category Visibility Map**
- Section header: **Follow-up Qualifiers**
- Cards: **Segments**

Copy snippet (baseline section):
- “Baseline answer to the generic category prompt. The sections below break this down using the AI’s follow-up qualifiers (the ‘it depends…’ questions) and segments within each.”

Tooltips:
- “These follow-up qualifiers come from the AI’s own ‘it depends…’ questions at the end of the baseline answer.”

---

## 8) Common issues + fixes

### 8.1 Airtable 422 UNKNOWN_FIELD_NAME
Symptom:
- `Unknown field name: "Value Label"`

Cause:
- Airtable field name mismatch (field doesn’t exist, or is named slightly differently).

Fix:
- Ensure the exact field name exists in the correct table.
- If you want it as a lookup, create:
  - Runs → link to Segment Definition (Factor Test) record
  - Lookup field named **Value Label**.

### 8.2 Segment card titles look like machine keys
Cause:
- `Value Label` is blank.

Fix:
- populate Value Label (manual, formula, lookup, or Make step).

### 8.3 Follow-up qualifier extraction returns empty array
Common causes:
- The answer’s follow-up questions are **numbered** (1., 2., 3.) instead of bullet points (`-` or `•`).
- The prompt instruction says “Consider only bullet points”, so numbered lines are ignored.

Fix options:
- Adjust extraction prompt to treat numbered lists as bullets too.
- Or normalize the follow-up section into bullet list before running extraction.

### 8.4 UI spacing: headline stuck to pill / rows too tight
Cause:
- nested flex containers without `gap-*` and missing spacing between elements.

Fix:
- Ensure the header block uses something like:
  - `flex items-center gap-2`
  - and add `mt-*` on the paragraph below.

---

## 9) Files (local paths from this workspace)

- HTML template: `/mnt/data/AI_Category_Snapshot_Jelly.html`
- Report generator scripts:
  - `/mnt/data/report_factory.py` (older)
  - `/mnt/data/report_factory_updated.py` (newer; supports Value Label)

---

## 10) What to provide in a future chat (minimal)

If you start a new chat and want to continue work fast, share:

1) A link or snippet to your current `report_factory.py` and HTML template.
2) Your Airtable table structure changes (especially Runs + Segment Definitions).
3) A sample project (brand/category/country) and one sample run record JSON.
4) The exact names of Run Types and Project Status values you’re using.

