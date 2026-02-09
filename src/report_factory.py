import os
import boto3
import re
import json
from pyairtable import Api
from dotenv import load_dotenv


# Load variables from .env file
load_dotenv()

# Access variables
API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
REGION = "eu-north-1" # Non-sensitive, can stay in code


# --- 2. TABLE CONFIGURATION ---
TABLE_PROJECTS = "tblHR5Dh46C9qNmcA"
TABLE_RUNS = "tbll0JcGZ5kxYXVag"
TABLE_METRICS = "tblbH5NbIIRoK5DeE"
TABLE_SOURCES = "tblP2XlgbxdNEqJJs"

# --- 3. FIELD NAME MAPPING ---
F_PROJECT_NAME = "Name"
F_PROJECT_BRAND = "Target Brand"
F_PROJECT_STATUS = "Status"
F_PROJECT_REPORT = "Report URL"
F_PROJECT_COUNTRY = "Country"

F_RUN_PROJECT = "Project"
F_RUN_TYPE = "Run Type"
F_RUN_PROMPT = "Prompt Text"
F_RUN_TARGET_BRAND = "Target Brand (from Prompt)"
F_RUN_FACTOR_KEY = "Factor Key"
F_RUN_FACTOR_LABEL = "Factor Label"
F_RUN_VALUE_KEY = "Value Key"
F_RUN_VALUE_DESC = "Value Description (from Factor Tests)"
F_RUN_VALUE_LABEL = "Value Label"
F_RUN_MODEL = "Model Used"  # Matches Airtable column name
F_RUN_FULL_OUTPUT = "Raw Answer"

F_METRIC_RUN = "Run"
F_METRIC_BRAND = "Brand Name"
F_METRIC_RANK = "Position Rank"
F_METRIC_SENTIMENT = "Sentiment Score"
F_METRIC_ROLE = "Brand Role"
F_METRIC_ISTARGET = "Is Target Brand"
F_METRIC_SNIPPET = "Answer Snippet"
F_METRIC_SOURCES = "Source (Domain)"
F_METRIC_FIT = "Category & Audience Fit"

F_SOURCE_NAME = "Name"
F_SOURCE_URL = "URL"
F_SOURCE_DOMAIN = "Primary Domain"
F_SOURCE_TYPE = "Page Type"

api = Api(API_KEY)
t_projects = api.table(BASE_ID, TABLE_PROJECTS)
t_runs = api.table(BASE_ID, TABLE_RUNS)
t_metrics = api.table(BASE_ID, TABLE_METRICS)
t_sources = api.table(BASE_ID, TABLE_SOURCES)

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)

def get_first(value):
    if isinstance(value, list):
        return value[0] if len(value) > 0 else None
    return value

def format_title(key):
    if not key: return "Scenario"
    return key.replace('_', ' ').title()

def calculate_source_stats(source_list):
    """
    Helper to calculate frequency stats for a list of sources.
    Returns sorted list of stats objects.
    """
    groups = {}
    total = len(source_list)
    if total == 0: return []

    for s in source_list:
        stype = s.get('type', 'Other')
        if stype not in groups:
            groups[stype] = {
                "type": stype,
                "count": 0,
                "brands": set(),
                "items": []
            }
        groups[stype]['count'] += 1
        # Track which brands are mentioned in this source type
        if s.get('brand'):
            groups[stype]['brands'].add(s['brand'])
        groups[stype]['items'].append(s)

    stats = []
    for k, v in groups.items():
        v['percentage'] = round((v['count'] / total) * 100)
        v['brands'] = list(v['brands']) # Convert set to list for JSON
        v['total'] = total
        stats.append(v)

    # Sort by frequency
    stats.sort(key=lambda x: x['count'], reverse=True)
    return stats

def calculate_dashboard_stats(factors, target_brand_name):
    # 1. Setup the scorecards
    total_scenarios = 0
    wins = 0
    threat_counts = {} # This is a dictionary to keep score: {"MarketMan": 5, "Kitchen CUT": 2}

    # 2. Loop through every "Factor" (e.g., "Number of Sites", "Cuisine Type")
    for factor in factors:
        # Loop through every specific Scenario (e.g., "1-5 Sites", "Italian")
        for value in factor.get("values", []):
            total_scenarios += 1
            mentions = value.get("mentions", [])

            # --- Step A: Find My Rank ---
            # We assume we are rank 999 (terrible) until we find our name.
            # This fixes the bug where "Unranked" was counting as a Win.
            my_rank = 999

            for m in mentions:
                if m["name"] == target_brand_name:
                    # If found, and rank is a real number, record it.
                    if m.get("rank") is not None:
                        my_rank = m["rank"]
                    break

            # --- Step B: Did I win? ---
            # If my rank is 1, 2, or 3, add to win count.
            if my_rank <= 3:
                wins += 1

            # --- Step C: Who beat me? (The Threat Radar) ---
            for m in mentions:
                comp_name = m["name"]
                comp_rank = m.get("rank")

                # Ignore myself and ignore anyone unranked
                if comp_name == target_brand_name or comp_rank is None:
                    continue

                # THE FIX: Only count them if their rank number is LOWER (better) than mine
                if comp_rank < my_rank:
                    # Add 1 to their threat score.
                    # .get(comp_name, 0) asks: "What's their score? If they don't have one, start at 0".
                    threat_counts[comp_name] = threat_counts.get(comp_name, 0) + 1

    # 3. Finalize the stats
    # Find the competitor with the highest score
    if threat_counts:
        top_threat_name = max(threat_counts, key=threat_counts.get)
        top_threat_count = threat_counts[top_threat_name]
    else:
        top_threat_name = "None"
        top_threat_count = 0

    # Calculate percentage (avoid dividing by zero)
    win_rate = round((wins / total_scenarios) * 100) if total_scenarios > 0 else 0

    return {
        "wins": wins,
        "scenarios": total_scenarios,
        "winRate": win_rate,
        "topThreatName": top_threat_name,
        "topThreatCount": top_threat_count
    }

def get_project_data(project_name, project_id, project_country):
    print(f"Fetching data for: {project_name} (ID: {project_id})...")

    # 1. Fetch ALL Runs
    all_runs = t_runs.all(fields=[F_RUN_PROJECT, F_RUN_TYPE, F_RUN_FACTOR_KEY, F_RUN_FACTOR_LABEL, F_RUN_VALUE_KEY, F_RUN_VALUE_DESC, F_RUN_VALUE_LABEL, F_RUN_TARGET_BRAND, F_RUN_MODEL, F_RUN_PROMPT, F_RUN_FULL_OUTPUT])

    runs = []
    for r in all_runs:
        project_lookup = r['fields'].get(F_RUN_PROJECT, [])
        if isinstance(project_lookup, list):
            if project_id in project_lookup:
                runs.append(r)
        elif project_lookup == project_id:
             runs.append(r)

    print(f" -> Match found: {len(runs)} Runs linked to {project_name}.")
    if not runs: return None

    run_ids = [r['id'] for r in runs]
    metrics = []

    # 2. Fetch Sources
    print(" -> Fetching Sources...")
    all_sources_raw = t_sources.all(fields=[F_SOURCE_NAME, F_SOURCE_URL, F_SOURCE_DOMAIN, F_SOURCE_TYPE])
    sources_map = { s['id']: s['fields'] for s in all_sources_raw }

    # 3. Fetch Metrics
    print(" -> Fetching Metrics...")
    all_metrics_raw = t_metrics.all()

    for m in all_metrics_raw:
        m_run = m['fields'].get(F_METRIC_RUN, [])
        run_id_val = m_run[0] if isinstance(m_run, list) and len(m_run) > 0 else m_run
        if run_id_val in run_ids:
            metrics.append(m)

    print(f" -> Match found: {len(metrics)} Metrics linked to these runs.")

    # --- STRUCTURE DATA ---
    try:
        # Find the Generic Run first - we need this record for IDs and Fields
        generic_run_record = next(r for r in runs if r['fields'].get(F_RUN_TYPE) == 'Generic')
        generic_run_fields = generic_run_record['fields']
    except StopIteration:
        print(f"Skipping {project_name}: No Generic Run found.")
        return None

    # Get Dynamic Values
    model_val = generic_run_fields.get(F_RUN_MODEL, "AI Model")
    country_val = project_country if project_country else "Global"

    # --- DEBUGGING PRINT ---
    print(f"DEBUG: Looking for column named '{F_RUN_PROMPT}'")
    print(f"DEBUG: Found value: {generic_run_fields.get(F_RUN_PROMPT)}")
    # -----------------------

    raw_prompt = generic_run_fields.get(F_RUN_PROMPT)
    prompt_val = get_first(raw_prompt)

    if not prompt_val:
        prompt_val = ""

    raw_chat = generic_run_fields.get(F_RUN_FULL_OUTPUT)
    chat_val = get_first(raw_chat)
    if not chat_val:
        chat_val = ""  # This ensures we never send "null" to the HTML

    report_data = {
        "project": {
            "name": get_first(generic_run_fields.get(F_RUN_TARGET_BRAND)),
            "prompt": prompt_val,
            "country": country_val,
            "model": model_val,
            "full_chat": chat_val

            },
        "baseline": { "brands": [], "sourceStats": [] },
        "factors": []
    }

    # --- PROCESS BASELINE ---
    # Now generic_run_record is defined, so this line won't crash
    base_metrics = [m['fields'] for m in metrics if m['fields'].get(F_METRIC_RUN) and m['fields'].get(F_METRIC_RUN)[0] == generic_run_record['id']]
    print(f" -> Baseline Metrics Found: {len(base_metrics)}")

    all_baseline_sources = [] # Collect all sources to calculate stats

    for m in base_metrics:
        # FILTER: Core Solution OR Target Brand
        role = m.get(F_METRIC_ROLE)
        is_target_raw = m.get(F_METRIC_ISTARGET)
        is_target = (isinstance(is_target_raw, int) and is_target_raw == 1) or (isinstance(is_target_raw, str) and is_target_raw == "1")

        if str(role).lower() != 'core solution' and not is_target:
            continue

        source_ids = m.get(F_METRIC_SOURCES, [])
        resolved_citations = []

        for sid in source_ids:
            if sid in sources_map:
                s_data = sources_map[sid]
                url = s_data.get(F_SOURCE_URL)
                if url:
                    # Create source object
                    src_obj = {
                        "url": url,
                        "type": s_data.get(F_SOURCE_TYPE, 'Other'),
                        "brand": m.get(F_METRIC_BRAND),
                        "snippet": m.get(F_METRIC_SNIPPET)
                    }
                    resolved_citations.append(src_obj)
                    all_baseline_sources.append(src_obj)

        report_data['baseline']['brands'].append({
            "rank": m.get(F_METRIC_RANK),
            "name": m.get(F_METRIC_BRAND),
            "isTarget": is_target,
            "sentiment": m.get(F_METRIC_SENTIMENT),
            "citations": resolved_citations,
            "snippet": m.get(F_METRIC_SNIPPET)
        })

    report_data['baseline']['brands'].sort(key=lambda x: x['rank'] if x['rank'] else 99)

    # Calculate Source Stats in Python
    report_data['baseline']['sourceStats'] = calculate_source_stats(all_baseline_sources)


    # --- PROCESS FACTORS ---
    factor_runs = [r for r in runs if r['fields'].get(F_RUN_TYPE) == 'Factor']
    print(f" -> Factor Runs Found: {len(factor_runs)}")

    # Dictionary to Group Factors (Swimlanes)
    factors_groups = {}

    for run in factor_runs:
        rf = run['fields']
        f_key = get_first(rf.get(F_RUN_FACTOR_KEY))
        f_label = get_first(rf.get(F_RUN_FACTOR_LABEL))

        if not f_key: continue

        # Initialize group if not exists
        if f_key not in factors_groups:
            factors_groups[f_key] = {
                "id": f_key,
                "title": f_label or format_title(f_key),
                "sensitivity": "Medium",
                "values": []
            }

        # Get metrics for this run
        run_metrics = [m['fields'] for m in metrics if m['fields'].get(F_METRIC_RUN) and m['fields'].get(F_METRIC_RUN)[0] == run['id']]

        target_metric = {}
        for m in run_metrics:
            it_raw = m.get(F_METRIC_ISTARGET)
            if (isinstance(it_raw, int) and it_raw == 1) or (isinstance(it_raw, str) and it_raw == "1"):
                target_metric = m
                break

        mentions = []
        factor_all_sources = [] # Collect all sources for this factor value

        for m in run_metrics:
             # --- FILTER LOGIC ---
             role_raw = m.get(F_METRIC_ROLE)
             role = role_raw[0] if isinstance(role_raw, list) and role_raw else role_raw
             is_t_raw = m.get(F_METRIC_ISTARGET)
             is_t = (isinstance(is_t_raw, int) and is_t_raw == 1) or (isinstance(is_t_raw, str) and is_t_raw == "1")

             # Only keep Core Solutions OR the Target Brand
             if str(role).lower() != 'core solution' and not is_t:
                 continue
             # --------------------

             m_source_ids = m.get(F_METRIC_SOURCES, [])
             m_citations = []

             for sid in m_source_ids:
                 if sid in sources_map:
                     s_data = sources_map[sid]
                     url = s_data.get(F_SOURCE_URL)
                     if url:
                         src_obj = {
                            "url": url,
                            "type": s_data.get(F_SOURCE_TYPE, 'Other'),
                            "brand": m.get(F_METRIC_BRAND),
                            "snippet": m.get(F_METRIC_SNIPPET)
                         }
                         m_citations.append(src_obj)
                         # Add to stats list
                         factor_all_sources.append(src_obj)

             mentions.append({
                 "name": m.get(F_METRIC_BRAND),
                 "rank": m.get(F_METRIC_RANK),
                 "sentiment": m.get(F_METRIC_SENTIMENT),
                 "role": m.get(F_METRIC_ROLE),
                 "text": m.get(F_METRIC_SNIPPET, '') if m.get(F_METRIC_SNIPPET) else "",
                 "citations": m_citations
             })
        mentions.sort(key=lambda x: x['rank'] if x['rank'] else 99)

        # Calculate Source Stats for this Factor Value
        val_source_stats = calculate_source_stats(factor_all_sources)

        val_key = get_first(rf.get(F_RUN_VALUE_KEY))
        val_desc = get_first(rf.get(F_RUN_VALUE_DESC))
        val_label = get_first(rf.get(F_RUN_VALUE_LABEL))
        if not val_desc: val_desc = val_key

        # Prefer human-friendly label when available (e.g., '50 to 149')
        ui_name = val_label if val_label else format_title(val_key)

        scenario_chat = get_first(rf.get(F_RUN_FULL_OUTPUT, ""))

        factors_groups[f_key]['values'].append({
            "id": val_key,
            "key": val_key,
            "name": ui_name,
            "desc": val_desc,
            "rank": target_metric.get(F_METRIC_RANK),
            "outcome": target_metric.get(F_METRIC_FIT, 'Unknown'),
            "competitor": "None", # Simplified
            "snippet": target_metric.get(F_METRIC_SNIPPET),
            "full_chat": scenario_chat,
            "lossReason": "",
            "mentions": mentions,
            "sourceStats": val_source_stats # Pre-calculated in Python!
        })

    # Convert groups dict to list
    report_data['factors'] = list(factors_groups.values())

    print(f" -> Constructed {len(report_data['factors'])} Factor Groups.")

    # ... existing code for constructing factors ...

    # --- NEW: Calculate Dashboard Stats ---
    print(" -> Calculating Dashboard Stats...")
    stats = calculate_dashboard_stats(report_data['factors'], report_data['project']['name'])

    # Save it into the data object so the HTML can see it
    report_data['dashboard'] = stats

    print(f" -> Constructed {len(report_data['factors'])} Factor Groups.")

    return report_data

def generate_html(data, template_path="AI_Category_Snapshot_Jelly.html"):
    with open(template_path, 'r') as f:
        html = f.read()

    # Python-to-JS Injection
    json_str = json.dumps(data)
    replacement = f"var reportData = {json_str}; // DATA_INJECTION_POINT"
    pattern = r"var reportData\s*=\s*[\s\S]*?;\s*//\s*DATA_INJECTION_POINT"

    return re.sub(pattern, lambda m: replacement, html)

def upload_s3(content, filename):
    try:
        s3.put_object(
            Bucket=BUCKET_NAME, Key=f"reports/{filename}", Body=content, ContentType='text/html'
        )
        return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/reports/{filename}"
    except Exception as e:
        print(f"S3 Upload Error: {e}")
        return None

def process_queue():
    print("Checking queue...")
    try:
        queue = t_projects.all(formula=f"{{{F_PROJECT_STATUS}}} = 'Ready for Report'")
    except Exception as e:
        print(f"Airtable Error: {e}")
        return

    print(f"Found {len(queue)} projects.")

    for record in queue:
        project_name = record['fields'].get(F_PROJECT_NAME)
        project_id = record['id']
        project_country = record['fields'].get(F_PROJECT_COUNTRY) # Grab Country here

        print(f"Processing: {project_name} ({project_id})...")
        if not project_name: continue

        data = get_project_data(project_name, project_id, project_country)
        if not data: continue

        html_content = generate_html(data)
        safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit()]).lower()
        file_name = f"{safe_name}_report.html"
        public_url = upload_s3(html_content, file_name)

        if public_url:
            t_projects.update(record['id'], {F_PROJECT_REPORT: public_url, F_PROJECT_STATUS: "Complete"}, typecast=True)
            print(f"✅ Finished: {public_url}")
        else:
            print(f"❌ Failed to upload.")

if __name__ == "__main__":
    process_queue()