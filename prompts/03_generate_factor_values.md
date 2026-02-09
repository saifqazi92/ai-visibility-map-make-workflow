# Generate factor values (template)

Developer: You are tasked with defining value buckets for a single decision factor used to analyze AI software recommendations.

Each FACTOR represents exactly ONE underlying dimension (a single "knob"), such as:
- Importance of a capability (e.g., automation, support, integrations)
- Numeric scale (e.g., budget, ticket volume, number of locations)
- Deployment preference (cloud vs on-premises)
- Integration dependence (needs integrations vs no integrations)

Inputs Provided:

- BUSINESS CONTEXT (for understanding only):
  - Business type: {{2.`Business Type (from Project)`}}
  - Primary tool category: {{2.`Primary Category (from Project)`}}
  - Target audience: {{2.`Target Audience (from Project)`}}

- FACTOR DETAILS:
  - factor_key:  {{9.`Factor Key`}}  (machine-readable name, snake_case)
  - label:   {{9.Label}}  (short human-readable label)
  - question_summary: {{9.`Exact Question`}} (1–2 sentences describing this factor)

Your Steps:

1) Identify the ONE core dimension the factor addresses.
   - When question_summary lists multiple aspects (e.g., "number of locations AND budget AND integrations"), select the single most relevant axis aligning with the label and factor_key.
   - Exclude any extra dimensions from value creation.

2) Propose 3–4 VALUE OPTIONS that span only that dimension.
   - Value options must vary solely along this axis.
   - Do NOT include other attributes such as:
     - number of locations
     - company size
     - revenue
     - region/country
     - procurement structure
     - specific vertical (unless the factor is explicitly that)
   - These belong in separate factors (e.g., site_count, locations, revenue, region, procurement_setup).

3) Ensure value options are reusable and generic.
   - For "importance / priority" factors (e.g., invoicing_automation_importance, support_importance, integrations_importance), you MUST use these four levels:
     - not_important
     - nice_to_have
     - important
     - mission_critical
   - For numeric/continuous factors (e.g., budget, ticket volume, locations, revenue), use monotonic ranges:
     - very_low / low / medium / high
     - or explicit ranges such as under_50 / 50_149 / 150_399 / 400_plus
   - For categorical preference factors (e.g., deployment_model, integration_preference), offer 3–4 mutually exclusive categories covering common options for that dimension.

CONSTRAINTS:

value_key:

snake_case identifier with no spaces (e.g., "not_important", "nice_to_have", "important", "mission_critical", "under_50", "cloud_only").

Reuse the same patterns across categories when possible (e.g., all "*_importance" factors use the four keys above).

value_label:

Human-readable short label for UI.

2–3 words max (numeric ranges allowed).

Must reflect ONLY the value_key; do not introduce new attributes.

Formatting rules:

Convert snake_case to spaces and Title Case.

If value_key matches "^\d+_\d+$", format as "{a} to {b}" (e.g., "100_250" -> "100 to 250").

If value_key ends with "_plus", format as "{a}+" (e.g., "400_plus" -> "400+").

If value_key starts with "under_", format as "Under {a}".

If value_key starts with "over_", format as "Over {a}".

For "_importance" factors, labels must be:

not_important -> "Not important"

nice_to_have -> "Nice to have"

important -> "Important"

mission_critical -> "Mission critical"

value_description:

Short, 1-sentence description from the customer's perspective.

Must describe ONLY this factor's dimension; do not mention locations, size, revenue, or procurement unless the factor is explicitly defined around that.

Do not reference specific tools or brands.

IMPORTANT NEGATIVE EXAMPLE (DO NOT DO THIS):

Factor:

factor_key: "invoicing_automation_importance"

label: "Invoicing automation importance"

question_summary: "How much this buyer cares about automating supplier invoice processing."

INCORRECT values (mixing importance with business size and setup—NOT allowed):

not_important: "Single-site operator who manages supplier invoices manually and does not use central procurement."

mission_critical: "Large multi-site group with central procurement teams where automated invoicing is essential for finance workflows."

These are incorrect because they combine:

Importance of invoicing automation
AND

Number of sites
AND

Procurement structure

CORRECT values for the same factor (the proper approach):

not_important

"We’re comfortable handling invoices manually; automation is not a priority in the next 12–24 months."

nice_to_have

"Automation would be helpful to reduce admin, but we won’t choose a tool primarily for this."

important

"We actively prefer tools with solid invoice automation and will downgrade options that lack it."

mission_critical

"Invoice automation is non-negotiable; we will not adopt tools without strong, reliable automation."

Note:

The factor remains strictly about the importance of automation.

No mention of sites, revenue, region, or procurement setup.

OUTPUT FORMAT:

Return ONLY valid JSON in this structure:

{
"values": [
{
"value_key": "some_key",
"value_label": "Short Label",
"value_description": "One-sentence description from the buyer's point of view."
},
{
"value_key": "another_key",
"value_label": "Short Label",
"value_description": "..."
}
]
}

RULES FOR "values":

The "values" array must contain 3 or 4 objects.

Each object must include exactly these keys: "value_key", "value_label", "value_description".

For importance factors (where factor_key ends with "_importance"), you MUST use exactly these four value_key values:

"not_important"

"nice_to_have"

"important"

"mission_critical"

For non-importance factors, choose suitable value_key strings that vary only along that factor's dimension.

Each value_label must be 2–3 words max (numeric ranges allowed) and follow the formatting rules in CONSTRAINTS.

Each value_description must be exactly 1 sentence.

Do not add any other top-level fields.

Do not include explanations or comments outside this JSON object.

Output Verbosity:

Return only the JSON object, in the exact structure above.

Prioritize complete, actionable answers within these constraints.
