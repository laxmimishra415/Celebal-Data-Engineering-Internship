# Databricks notebook source
# MAGIC %md
# MAGIC #  Customer Support Ticket Resolution Pipeline
# MAGIC ### Data Engineering Project — Celebal Technologies Internship
# MAGIC **Author:** Laxmi Mishra
# MAGIC
# MAGIC ## Problem Overview
# MAGIC A company ran a 2-day Customer Support Efficiency Review. Every resolved/unresolved 
# MAGIC ticket was logged and uploaded as CSV files to Azure Data Lake Storage Gen2 (ADLS Gen2) 
# MAGIC at the end of each day. The raw data is messy — it has unresolved tickets, agents outside 
# MAGIC review scope, and resolution times stored as text (e.g. "1h 10m 20s"). This pipeline 
# MAGIC cleans, validates, transforms and aggregates that data using the **Bronze → Silver → Gold** 
# MAGIC medallion architecture to answer 4 business questions for leadership.
# MAGIC
# MAGIC ## Business Questions
# MAGIC 1. **Team-wise resolution rate** — how many tickets resolved under each Team Lead (TL01–TL08)?
# MAGIC 2. **Per-agent Day 1 vs Day 2 performance** — who improved, declined, or was active only one day?
# MAGIC 3. **Quality threshold compliance** — a ticket only counts if resolved status AND time > 15 mins
# MAGIC 4. **Day 2 carry-over** — agents who already succeeded on Day 1 are excluded from Day 2 (avoid double-counting)
# MAGIC
# MAGIC ## Business Rules
# MAGIC | Rule | Description |
# MAGIC |------|-------------|
# MAGIC | R1 | Resolution time text ("Xh Xm Xs") → converted to total decimal minutes |
# MAGIC | R2 | Rounding: seconds ≥ 30 → round up to next minute |
# MAGIC | R3 | Successful resolution = status "Resolved" AND time > 15 minutes |
# MAGIC | R4 | Scope filter: only agents under TL01–TL08 included |
# MAGIC | R5 | Drop rows with null/blank ticket_id, agent_id, or resolution_time |
# MAGIC | R6 | Day 2 carry-over: agents who succeeded Day 1 excluded from Day 2 results |
# MAGIC
# MAGIC ## Pipeline Design
# MAGIC - **Bronze Layer** → Raw ingestion, no business logic, just mirror source data + add Day column
# MAGIC - **Silver Layer** → Clean nulls, convert time, apply scope filter, apply quality threshold
# MAGIC - **Gold Layer** → Carry-over rule + aggregate to answer the 4 business questions

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ## ⚙️ Configuration
# MAGIC Centralizing business-rule constants here instead of hardcoding them throughout the 
# MAGIC notebook — makes the pipeline easier to maintain if thresholds or scope change in future.

# COMMAND ----------

# ── Pipeline Configuration ──
QUALITY_THRESHOLD_MINUTES = 15          # ticket must take > this to count as "successful"
IN_SCOPE_TEAM_LEADS = {f"TL{str(i).zfill(2)}" for i in range(1, 9)}  # TL01-TL08
ROUND_UP_SECONDS_THRESHOLD = 30         # seconds >= this rounds up to next minute

print("Pipeline Config:")
print(f"  Quality threshold: > {QUALITY_THRESHOLD_MINUTES} minutes")
print(f"  In-scope team leads: {sorted(IN_SCOPE_TEAM_LEADS)}")
print(f"  Rounding threshold: >= {ROUND_UP_SECONDS_THRESHOLD} seconds")

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC ## 🗄️ Bronze Source Data — Simulated ADLS Gen2 CSVs
# MAGIC Since we don't have real ADLS Gen2 access, we simulate the 3 source tables that would 
# MAGIC normally be uploaded as CSV files. Includes intentional edge cases: nulls, rushed tickets 
# MAGIC (<=15 min), out-of-scope agents (TL09+), and malformed time strings — to properly test 
# MAGIC the pipeline's validation logic.

# COMMAND ----------

from pyspark.sql import functions as F

# ── agent_profiles: 40 in-scope agents (TL01-TL08) + 4 out-of-scope (TL09-TL10) ──
profiles_data = []
roles = ["Junior Support Agent", "Senior Support Agent"]
for tl_num in range(1, 9):
    tl_id = f"TL{tl_num:02d}"
    for a in range(1, 6):  # 5 agents per team lead
        agent_num = (tl_num - 1) * 5 + a
        agent_id = f"A{agent_num:03d}"
        role = roles[0] if a % 2 == 0 else roles[1]
        profiles_data.append((agent_id, f"Agent_{agent_id}", role, tl_id))

# out-of-scope agents (should be filtered out later)
profiles_data += [
    ("A041", "Agent_A041", "Senior Support Agent", "TL09"),
    ("A042", "Agent_A042", "Junior Support Agent", "TL09"),
    ("A043", "Agent_A043", "Senior Support Agent", "TL10"),
    ("A044", "Agent_A044", "Junior Support Agent", "TL10"),
]

agent_profiles = spark.createDataFrame(
    profiles_data, ["agent_id", "agent_name", "role", "team_lead_id"]
)
display(agent_profiles)

# COMMAND ----------

# ── day1_tickets: mix of valid, rushed, unresolved, null, bad-format, out-of-scope ──
import random
random.seed(42)

day1_data = []
ticket_num = 1
categories = ["Technical", "Billing", "General", "Account"]

# Valid resolved tickets (>15 min) — most agents get 2-4 good tickets
for tl_num in range(1, 9):
    for a in range(1, 6):
        agent_num = (tl_num - 1) * 5 + a
        agent_id = f"A{agent_num:03d}"
        num_tickets = random.randint(2, 4)
        for _ in range(num_tickets):
            mins = random.randint(16, 90)
            secs = random.randint(0, 59)
            day1_data.append((f"TKT{ticket_num:05d}", agent_id, "Resolved",
                               f"0h {mins}m {secs}s", random.choice(categories)))
            ticket_num += 1

# Rushed tickets (<=15 min) — should NOT count as successful
for agent_id in ["A001", "A007", "A015", "A023"]:
    day1_data.append((f"TKT{ticket_num:05d}", agent_id, "Resolved", "0h 12m 30s", "Technical"))
    ticket_num += 1

# Pending / unresolved tickets
for agent_id in ["A002", "A010", "A018"]:
    day1_data.append((f"TKT{ticket_num:05d}", agent_id, "Pending", "0h 25m 00s", "Billing"))
    ticket_num += 1

# Null / blank critical fields — should be dropped (R5)
day1_data.append((f"TKT{ticket_num:05d}", None, "Resolved", "0h 30m 00s", "Technical"))
ticket_num += 1
day1_data.append((f"TKT{ticket_num:05d}", "A005", "Resolved", None, "Billing"))
ticket_num += 1
day1_data.append((None, "A006", "Resolved", "0h 20m 00s", "General"))
ticket_num += 1

# Bad/malformed time format — should fail parsing and be dropped
day1_data.append((f"TKT{ticket_num:05d}", "A009", "Resolved", "invalid_time", "Technical"))
ticket_num += 1

# Out-of-scope agent ticket— should be filtered by scope rule (R4)
day1_data.append((f"TKT{ticket_num:05d}", "A041", "Resolved", "0h 40m 00s", "Technical"))
ticket_num += 1

day1_tickets = spark.createDataFrame(
    day1_data, ["ticket_id", "agent_id", "status", "resolution_time", "category"]
)
print(f"Total Day 1 rows: {day1_tickets.count()}")
display(day1_tickets)

# COMMAND ----------

# ── day2_tickets: includes some Day-1-successful agents (to test carry-over rule R6) ──
day2_data = []
ticket_num = 200  # different numbering range from Day 1

# ALL 40 in-scope agents get some Day 2 activity — pipeline's carry-over rule
# will later remove those who already succeeded on Day 1
for tl_num in range(1, 9):
    for a in range(1, 6):
        agent_num = (tl_num - 1) * 5 + a
        agent_id = f"A{agent_num:03d}"
        num_tickets = random.randint(1, 3)
        for _ in range(num_tickets):
            mins = random.randint(10, 80)
            secs = random.randint(0, 59)
            status = "Resolved" if mins > 10 else "Pending"
            day2_data.append((f"TKT{ticket_num:05d}", agent_id, status,
                               f"0h {mins}m {secs}s", random.choice(categories)))
            ticket_num += 1

# A couple more rushed tickets on Day 2 too
day2_data.append((f"TKT{ticket_num:05d}", "A012", "Resolved", "0h 09m 15s", "General"))
ticket_num += 1

# Null field on Day 2 as well
day2_data.append((f"TKT{ticket_num:05d}", "A020", "Resolved", None, "Technical"))
ticket_num += 1

day2_tickets = spark.createDataFrame(
    day2_data, ["ticket_id", "agent_id", "status", "resolution_time", "category"]
)
print(f"Total Day 2 rows: {day2_tickets.count()}")
display(day2_tickets)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC ---
# MAGIC ## 🥉 Layer 1 · BRONZE — Raw Ingestion
# MAGIC **What happens here:** Mirror the source data exactly as-is. Only add a literal `Day` 
# MAGIC column (1 or 2) to identify which day's file the ticket came from. No cleaning, no 
# MAGIC filtering, no business logic — that all happens in Silver.

# COMMAND ----------

from pyspark.sql.types import IntegerType

# ── Bronze: raw ingestion, add Day marker only ──
bronze_day1 = day1_tickets.withColumn("Day", F.lit(1).cast(IntegerType()))
bronze_day2 = day2_tickets.withColumn("Day", F.lit(2).cast(IntegerType()))
bronze_profiles = agent_profiles

print(f"Bronze Day 1: {bronze_day1.count()} rows")
print(f"Bronze Day 2: {bronze_day2.count()} rows")
print(f"Bronze Profiles: {bronze_profiles.count()} rows")

display(bronze_day1.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ## 🥈 Layer 2 · SILVER — Cleaning & Transformation
# MAGIC
# MAGIC ### 2-A · Data Quality Gate (R5)
# MAGIC Records missing `ticket_id`, `agent_id`, or `resolution_time` cannot be validated 
# MAGIC downstream, so they're dropped here. We log the before/after counts for audit purposes 
# MAGIC — this is important in real pipelines so you can trace data loss.

# COMMAND ----------

def drop_critical_nulls(df, label: str):
    """
    Drops rows where ticket_id, agent_id, or resolution_time is null or blank.
    Logs before/after counts for audit trail.
    """
    before = df.count()
    clean = df.filter(
        F.col("ticket_id").isNotNull() & (F.col("ticket_id") != "") &
        F.col("agent_id").isNotNull() & (F.col("agent_id") != "") &
        F.col("resolution_time").isNotNull() & (F.col("resolution_time") != "")
    )
    after = clean.count()
    print(f"🔍 {label}: {before} → {after} rows ({before - after} dropped for null/blank critical fields)")
    return clean

silver_day1_clean = drop_critical_nulls(bronze_day1, "Day 1")
silver_day2_clean = drop_critical_nulls(bronze_day2, "Day 2")

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ### 2-B · Resolution Time Conversion (R1 & R2)
# MAGIC Resolution time is stored as text: `"Xh Xm Xs"` (e.g. `"0h 22m 45s"`). We need to convert 
# MAGIC this into a single number — total decimal minutes — so we can compare and threshold it.
# MAGIC
# MAGIC **Rounding rule:** if seconds ≥ 30, round UP to next whole minute. If seconds < 30, drop them.
# MAGIC
# MAGIC | Raw string   | Hours→min + Minutes | Seconds rule | Result |
# MAGIC |--------------|---------------------|--------------|--------|
# MAGIC | `0h 22m 45s` | 0 + 22 = 22          | 45 ≥ 30 → +1 | 23 min |
# MAGIC | `0h 14m 20s` | 0 + 14 = 14          | 20 < 30 → +0 | 14 min |
# MAGIC | `1h 10m 30s` | 60 + 10 = 70         | 30 ≥ 30 → +1 | 71 min |

# COMMAND ----------

import re
from pyspark.sql.types import IntegerType as _IntType

def parse_resolution_time(time_str: str):
    """
    Converts 'Xh Xm Xs' string into total integer minutes.
    - hours are converted to minutes (h * 60)
    - seconds >= ROUND_UP_SECONDS_THRESHOLD round the total UP by 1 minute
    - seconds below that are simply dropped
    - returns None if the string doesn't match the expected pattern
      (this naturally handles our bad-format test case, e.g. "invalid_time")
    """
    if not time_str:
        return None
    
    # Regex captures: (digits)h (digits)m (digits)s
    match = re.match(r"(\d+)h\s*(\d+)m\s*(\d+)s", time_str.strip())
    if not match:
        return None  # malformed string → gets filtered out later
    
    hours, minutes, seconds = int(match.group(1)), int(match.group(2)), int(match.group(3))
    total_minutes = (hours * 60) + minutes
    
    if seconds >= ROUND_UP_SECONDS_THRESHOLD:
        total_minutes += 1  # round up
    
    return total_minutes

# Register as a Spark UDF so we can use it on DataFrame columns
parse_time_udf = F.udf(parse_resolution_time, _IntType())

# Quick sanity test against the rule table above
test_cases = ["0h 22m 45s", "0h 14m 20s", "1h 10m 30s", "0h 15m 00s", "invalid_time", None]
for t in test_cases:
    print(f"{t} → {parse_resolution_time(t)}")

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ### 2-C · Apply Time Conversion & Normalize Status
# MAGIC Apply the UDF to get `resolved_minutes`. Also normalize `status` (uppercase + trim) so 
# MAGIC that inconsistent casing/whitespace in source data doesn't break comparisons later. Rows 
# MAGIC where the time string was malformed (UDF returned None) are dropped here too.

# COMMAND ----------

def apply_time_conversion(df):
    """
    Adds resolved_minutes column and normalizes status text.
    Drops rows where resolution_time couldn't be parsed (malformed strings).
    """
    return (
        df
        .withColumn("status_clean", F.upper(F.trim(F.col("status"))))
        .withColumn("resolved_minutes", parse_time_udf(F.col("resolution_time")))
        .filter(F.col("resolved_minutes").isNotNull())
    )

silver_day1_times = apply_time_conversion(silver_day1_clean)
silver_day2_times = apply_time_conversion(silver_day2_clean)

print(f"Day 1 after time conversion: {silver_day1_times.count()} rows "
      f"(malformed time strings dropped)")
print(f"Day 2 after time conversion: {silver_day2_times.count()} rows")

display(silver_day1_times.select("ticket_id", "agent_id", "status_clean", 
                                    "resolution_time", "resolved_minutes").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ### 2-D · Scope Filter — TL01–TL08 Only (R4)
# MAGIC Join tickets with `agent_profiles` to bring in `team_lead_id`, then keep only agents 
# MAGIC whose team lead is TL01 through TL08. Anyone under TL09+ (out-of-scope) is discarded — 
# MAGIC even if their tickets look perfectly valid.

# COMMAND ----------

def enrich_and_scope_filter(tickets_df, profiles_df):
    """
    Joins tickets to agent_profiles (inner join — drops tickets whose agent
    isn't even in the profiles table), then filters to only in-scope team leads
    (see IN_SCOPE_TEAM_LEADS in the Configuration cell above).
    """
    enriched = tickets_df.join(
        F.broadcast(profiles_df.select("agent_id", "agent_name", "role", "team_lead_id")),
        on="agent_id", how="inner"
    )
    return enriched.filter(F.col("team_lead_id").isin(IN_SCOPE_TEAM_LEADS))

silver_day1_scoped = enrich_and_scope_filter(silver_day1_times, agent_profiles)
silver_day2_scoped = enrich_and_scope_filter(silver_day2_times, agent_profiles)

print(f"Day 1 after scope filter: {silver_day1_scoped.count()} rows")
print(f"Day 2 after scope filter: {silver_day2_scoped.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2-E · Quality Threshold (R3)
# MAGIC A ticket only counts as **successfully resolved** when BOTH conditions are true:
# MAGIC 1. `status_clean == 'RESOLVED'`
# MAGIC 2. `resolved_minutes > 15` (strictly greater — exactly 15 does NOT count)
# MAGIC
# MAGIC This filters out rushed/improperly-handled tickets and anything still pending.

# COMMAND ----------

def apply_quality_threshold(df):
    """
    Marks and keeps only tickets that meet BOTH the status and time-threshold rules
    (see QUALITY_THRESHOLD_MINUTES in the Configuration cell above).
    """
    return (
        df
        .withColumn("is_successful",
            (F.col("status_clean") == "RESOLVED") & (F.col("resolved_minutes") > QUALITY_THRESHOLD_MINUTES))
        .filter(F.col("is_successful") == True)
    )

silver_day1_success = apply_quality_threshold(silver_day1_scoped)
silver_day2_success = apply_quality_threshold(silver_day2_scoped)

print(f"Day 1 successful (quality-passed) tickets: {silver_day1_success.count()}")
print(f"Day 2 successful (quality-passed) tickets: {silver_day2_success.count()}")

display(silver_day1_success.select("ticket_id", "agent_id", "team_lead_id", 
                                      "status_clean", "resolved_minutes").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ## 🥇 Layer 3 · GOLD — Business Logic & Aggregation
# MAGIC
# MAGIC ### 3-A · Day 2 Carry-over Rule (R6)
# MAGIC Agents who had **≥1 successful ticket on Day 1** are assumed "done" — their Day 2 records 
# MAGIC are removed via a **left anti-join** to prevent double-counting an agent's success across 
# MAGIC both days.

# COMMAND ----------

# Get distinct agent_ids who succeeded on Day 1
day1_successful_agents = silver_day1_success.select("agent_id").distinct()
print(f"👥 Day-1 successful agents (to be excluded from Day 2): {day1_successful_agents.count()}")

# Left anti-join: keep only Day 2 rows whose agent_id is NOT in the Day-1-successful list
silver_day2_carryover_applied = silver_day2_success.join(
    day1_successful_agents, on="agent_id", how="left_anti"
)

print(f"Day 2 successful BEFORE carry-over filter: {silver_day2_success.count()}")
print(f"Day 2 successful AFTER carry-over filter: {silver_day2_carryover_applied.count()}")

# Combine Day 1 + filtered Day 2 into one Gold dataset
gold_combined = silver_day1_success.unionByName(silver_day2_carryover_applied)
print(f"\n✅ Gold combined dataset: {gold_combined.count()} total successful ticket records")

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ### ✅ Q1 — Ticket Resolution Rates Across the Team Hierarchy
# MAGIC
# MAGIC **Business question:** How many tickets were successfully resolved under each Team Lead 
# MAGIC (TL01–TL08)? Which teams have the highest throughput and efficiency?

# COMMAND ----------

gold_q1 = (
    gold_combined
    .groupBy("team_lead_id")
    .agg(
        F.count("ticket_id").alias("total_resolved_tickets"),
        F.countDistinct("agent_id").alias("active_agents"),
        F.round(F.count("ticket_id") / F.countDistinct("agent_id"), 2).alias("avg_tickets_per_agent")
    )
    .orderBy(F.desc("total_resolved_tickets"))
)

display(gold_q1)

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ### ✅ Q2 — Per-Agent Performance for Day 1 and Day 2
# MAGIC **Business question:** How did each agent perform separately on Day 1 vs Day 2? Who 
# MAGIC improved, declined, or was active on only one day?

# COMMAND ----------

day1_counts = (silver_day1_success.groupBy("agent_id", "agent_name", "team_lead_id")
               .agg(F.count("ticket_id").alias("day1_resolved")))

day2_counts = (silver_day2_carryover_applied.groupBy("agent_id")
               .agg(F.count("ticket_id").alias("day2_resolved")))

gold_q2 = (
    day1_counts.join(day2_counts, on="agent_id", how="full_outer")
    .fillna(0, subset=["day1_resolved", "day2_resolved"])
    .withColumn("trend",
        F.when(F.col("day2_resolved") > F.col("day1_resolved"), "Improved")
         .when(F.col("day2_resolved") < F.col("day1_resolved"), "Declined")
         .otherwise("Same/No Day 2 Activity"))
    .orderBy("team_lead_id", "agent_id")
)

display(gold_q2)

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ### ✅ Q3 — Compliance with the Resolution Quality Threshold
# MAGIC **Business question:** How many agents/teams are meeting the >15-minute quality standard 
# MAGIC vs. how many tickets were rushed/rejected?

# COMMAND ----------

# Combine ALL scoped tickets (before quality filter) to compute compliance %
all_scoped = silver_day1_scoped.withColumn("Day", F.lit(1)).unionByName(
    silver_day2_scoped.withColumn("Day", F.lit(2)), allowMissingColumns=True
)

gold_q3 = (
    all_scoped
    .withColumn("passes_quality",
        (F.col("status_clean") == "RESOLVED") & (F.col("resolved_minutes") > 15))
    .groupBy("team_lead_id")
    .agg(
        F.count("ticket_id").alias("total_tickets"),
        F.sum(F.col("passes_quality").cast("int")).alias("quality_passed"),
        F.round(F.sum(F.col("passes_quality").cast("int")) / F.count("ticket_id") * 100, 1).alias("compliance_pct")
    )
    .orderBy(F.desc("compliance_pct"))
)

display(gold_q3)

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ### ✅ Q4 — Agents Who Carried Over Unresolved Work from Day 1
# MAGIC **Business question:** Which agents did NOT succeed on Day 1 and continued into Day 2? 
# MAGIC How many records were excluded due to the carry-over rule?

# COMMAND ----------

day1_agent_ids = set(r["agent_id"] for r in day1_successful_agents.collect())
day2_before_ids = set(r["agent_id"] for r in silver_day2_success.select("agent_id").distinct().collect())

carried_over_agents = day2_before_ids - day1_agent_ids   # genuinely continued from Day 1
excluded_agents = day2_before_ids & day1_agent_ids        # succeeded Day 1, excluded from Day 2

print(f"🔁 Agents who carried over (no Day 1 success, active Day 2): {len(carried_over_agents)}")
print(f"🚫 Agents excluded from Day 2 (already succeeded Day 1): {len(excluded_agents)}")

gold_q4 = spark.createDataFrame(
    [(a, "Carried Over") for a in carried_over_agents] +
    [(a, "Excluded - Already Succeeded Day 1") for a in excluded_agents],
    ["agent_id", "carryover_status"]
)
display(gold_q4.orderBy("agent_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ## 📋 Data Quality Audit Trail
# MAGIC Tracking row counts at each pipeline stage helps verify data integrity and makes it easy 
# MAGIC to spot exactly where records were dropped and why — a standard practice in production 
# MAGIC data pipelines.

# COMMAND ----------

# ── Consolidated audit trail across the pipeline ──
audit_data = [
    ("Bronze (raw ingested)", bronze_day1.count(), bronze_day2.count()),
    ("Silver - after null/blank drop (R5)", silver_day1_clean.count(), silver_day2_clean.count()),
    ("Silver - after time parsing (malformed dropped)", silver_day1_times.count(), silver_day2_times.count()),
    ("Silver - after scope filter TL01-TL08 (R4)", silver_day1_scoped.count(), silver_day2_scoped.count()),
    ("Silver - after quality threshold >15min (R3)", silver_day1_success.count(), silver_day2_success.count()),
    ("Gold - Day 2 after carry-over filter (R6)", "N/A", silver_day2_carryover_applied.count()),
]

audit_df = spark.createDataFrame(audit_data, ["pipeline_stage", "day1_row_count", "day2_row_count"])
display(audit_df)

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ---
# MAGIC ## 📊 Pipeline Summary
# MAGIC This Bronze → Silver → Gold pipeline processed **220 raw ticket records** across 2 days, 
# MAGIC applying 6 business rules (data quality gate, time conversion, scope filter, quality 
# MAGIC threshold, carry-over rule) to produce **122 validated successful resolutions** across 
# MAGIC 40 agents under 8 Team Leads (TL01–TL08). The Gold layer answers all 4 leadership 
# MAGIC questions: team-wise throughput, per-agent daily trends, quality compliance (88–100%), 
# MAGIC and Day-2 carry-over tracking — enabling data-driven performance decisions.

# COMMAND ----------

# MAGIC %md
# MAGIC ⚠️ Assumptions & Known Limitations
# MAGIC Documenting these openly is good engineering practice — it shows what was decided, why, and what a production version would need to address next.
# MAGIC
# MAGIC Simulated data — Real ADLS Gen2 access wasn't available for this project, so all three source tables (agent_profiles, day1_tickets, day2_tickets) were synthetically generated with realistic edge cases (nulls, rushed tickets, out-of-scope agents, malformed time strings) to properly exercise every business rule.
# MAGIC
# MAGIC Time format assumption — The parser only handles the exact "Xh Xm Xs" pattern. A production version would need to handle variants (e.g. missing hour component like "22m 45s", or different separators) more defensively.
# MAGIC
# MAGIC Carry-over edge case — In this run, all 40 in-scope agents happened to succeed on Day 1, so the entire Day 2 dataset was excluded by the carry-over rule. This is correct behavior per the business rule, but it also means the "carried over" path (Q4) wasn't exercised with real data here — worth validating separately with a dataset where some agents genuinely fail Day 1.
# MAGIC
# MAGIC Scope filter join type — An inner join is used against agent_profiles, meaning any ticket referencing an agent_id missing from the profiles table is silently dropped. In production, this would ideally also be logged as a data-quality exception rather than dropped silently.
# MAGIC
# MAGIC No persistence layer — For this exercise, Gold tables are kept as in-memory DataFrames. A production pipeline would write these to Delta tables in Unity Catalog for downstream dashboarding.

# COMMAND ----------

