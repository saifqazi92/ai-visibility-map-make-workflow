# Extract brand metrics + sources (template)

You are analysing how an AI answer recommends solutions for a specific user situation.

# PROJECT CONTEXT

Use this only to judge category/audience fit, not to change the answer.

- Business type: {{25.`Business Type (from Project) (from Prompt)`}}- Primary tool category: {{25.`Primary Category (from Project) (from Prompt)`}}
- Target audience: {{25.`Target Audience (from Project) (from Prompt)`}}

# SITUATION CONTEXT FOR THIS RUN

This run represents one concrete user situation (what the user told the assistant about themselves).

- Situation dimension: {{25.`Factor Label`}}
  (example: "Current POS system", "Software budget", "Number of locations", "Invoicing automation importance")

- Situation value: {{25.`Value Description (from Factor Tests)`}}
  (example: "Single, older POS with poor exports", "Very tight budget under £50/month", "Multi-site group with 11+ locations")

Treat this as:
“You are measuring how recommendations change when the user’s situation is:
[Situation dimension] = [Situation value].”


CANONICAL BRAND RULES (STRICT):

- Extract ONLY the canonical product or company name.
- IGNORE pricing tiers, plans, editions, SKUs, or descriptors.

Examples:
- “RepairDesk Growth”, “RepairDesk Enterprise”, “RepairDesk Starter” → brand = “RepairDesk”
- “Shopify Plus” → brand = “Shopify”
- “HubSpot Marketing Hub” → brand = “HubSpot”

NEVER include plan names, tiers, or pricing levels in the "brand" field.

If the answer explicitly mentions a plan/tier:
- Treat it as descriptive context ONLY.
- The "brand" field must still be the canonical brand.


# INPUTS

You will receive:

QUESTION (original category question):{{25.Prompt}}

ANSWER (assistant’s reply for this situation):{{25.`Raw Answer`}}


TASK

Your job is to extract a structured list of all solutions the ANSWER recommends for THIS specific situation and score how strongly they’re recommended.

A "solution" MUST be a named software product, SaaS platform, or vendor that someone can evaluate and use.

Examples of valid solutions:

repair-shop POS: "RepairDesk", "RepairShopr", "Fixably"

kitchen costing platforms: "Jelly", "MarketMan", "KitchenCUT"

hospitality stacks: "Lightspeed Restaurant", "Kobas", "3S POS"

accounting tools: "Xero", "QuickBooks Online"

general software brands explicitly named: "Microsoft Excel", "Excel", "Google Sheets", "Airtable"

EXCLUDE (do NOT output these as solutions):

frameworks, models, methods, or conceptual approaches

operational processes, steps, audits, checklists, KPIs, dashboards, or “what to do next” advice (unless a specific software brand is named)

spreadsheet templates/workflows/processes (e.g., "Excel template", "Sheets costing workflow", "spreadsheet dashboard") — ONLY include "Excel" or "Google Sheets" as brands if they are explicitly named

generic tool categories without a specific named product/vendor (e.g., "recipe costing tool", "waste management tool")

anything that is not a specific named software product/vendor

If the ANSWER contains no named software solutions, return [].

HOW TO INTERPRET THE ANSWER

Numbered and labelled options define the main ranking.

Pay special attention to structures like:

"Recommended paths: 1) … 2) … 3) …"

"Option 1 — …, Option 2 — …, Option 3 — …"

"1) MarketMan … 2) Maitre’D … 3) Lightspeed Restaurant … 4) Jelly … 5) 3S POS"

Rules:

Only treat a numbered/labelled option as a Core solution if the option title is a valid software solution under the rules above.

If a numbered/labelled option is a framework, process step, audit, KPI, dashboard, or generic category (not a named software brand), DO NOT output it and DO NOT assign a rank.

Combinations and “X + Y” options.

If an option heading is like:

"3) Lightspeed Restaurant (multi-location POS) + pairing with MarketMan or Jelly for costing"

then:

The brand in the option title ("Lightspeed Restaurant") is the main Core solution for that option.

Brands only mentioned as "pair with X", "add Y", "integrates with Z" are Supporting in that option, unless they ALSO have their own numbered option elsewhere in the ANSWER.

If a brand appears in multiple places, always take the strongest role and best rank:

If it ever has its own numbered option → treat it as Core with a rank.

If it never has its own option and only appears as an add-on → treat it as Supporting.

FIELDS TO OUTPUT

For EACH solution you identify, output an object with:

"brand": short software brand/product name only (e.g., "Jelly", "MarketMan", "KitchenCUT", "RepairDesk", "Excel", "Google Sheets")

"brand_role": one of:

"Core solution"

"Supporting"

"Mention-only"

"category_audience_fit": one of:

"Direct fit"

"Category fit, different audience"

"Adjacent"

"Out of scope"

"sentiment": number between 0 and 1 based on how positive the ANSWER is about this solution

"rank":

Core solution → integer rank (1, 2, 3, …)

Supporting / Mention-only → null

"source_urls":

array of URLs (strings) from the ANSWER that support this solution

Up to 5 URLs per solution

"answer_snippet":

exact text from the ANSWER that describes this solution (verbatim)

OUTPUT FORMAT

Return ONLY JSON. No extra commentary, no markdown, no plain text.

[
{
"brand": "BrandName",
"brand_role": "Core solution",
"category_audience_fit": "Direct fit",
"sentiment": 0.9,
"rank": 1,
"source_urls": ["https://example.com/page-1
"],
"answer_snippet": "Exact snippet from the ANSWER..."
}
]

Always include all fields.

Use null for "rank" when brand_role is "Supporting" or "Mention-only".

Use [] if there are no valid solutions in the answer.