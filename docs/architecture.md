# Architecture

## Components
- Web form: collects Category Name, Target Audience, optional Target Brand, etc.
- Airtable: source of truth for Projects, Runs, Brand Metrics, Sources (and factor tables).
- Make.com: orchestration pipeline (prompt gen → factor gen → tests → extraction).
- PythonAnywhere (scheduled): runs `report_factory.py` to build and publish reports.
- S3: hosts the final HTML report artifact.

## Data flow (high-level)
1) Project created / marked Ready in Airtable.
2) Scenario 1 (Dispatcher) watches Projects and triggers.
3) Dispatcher calls scenarios in sequence: 2 → 3 → 4 → 5 → 6
4) Python report factory finds Projects ready for report generation, pulls Runs/Metrics/Sources, builds one self-contained HTML file, uploads to S3, writes the report URL back to the Project record.

## Report generation
`src/report_factory.py`:
- queries Airtable for a project’s Runs, Metrics, and Sources
- structures them into a single JSON payload
- injects the JSON payload into the HTML template at `// DATA_INJECTION_POINT`
- uploads the resulting HTML to S3
- updates the Project record with the report URL
