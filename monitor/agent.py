"""
BigQuery AI Auto-Fix Agent
Monitors pipeline AND automatically fixes issues
"""
import os
import json
import requests
import subprocess
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID     = os.getenv("GCP_PROJECT_ID")
bq_client      = bigquery.Client(project=PROJECT_ID)

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "reports"
)

def ask_gemini(prompt):
    url     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    data     = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None

def run_query(sql):
    try:
        result = bq_client.query(sql).result()
        return [dict(row) for row in result]
    except Exception as e:
        return [{"error": str(e)}]

def collect_metrics():
    print("  → Collecting metrics...")
    today     = date.today()
    yesterday = today - timedelta(days=1)

    raw_orders = run_query(f"""
        SELECT
            COUNT(*)                        AS total_rows,
            MAX(DATE(order_date))           AS latest_date,
            COUNTIF(DATE(order_date) = '{today}')
                                            AS today_orders,
            COUNTIF(DATE(order_date) = '{yesterday}')
                                            AS yesterday_orders,
            ROUND(SUM(total_amount), 2)     AS total_revenue,
            ROUND(AVG(total_amount), 2)     AS avg_order_value
        FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
    """)

    daily_revenue = run_query(f"""
        SELECT
            COUNT(*)                         AS total_rows,
            MAX(report_date)                 AS latest_date,
            COUNTIF(report_date = '{today}') AS today_exists,
            ROUND(SUM(total_revenue), 2)     AS total_revenue
        FROM `{PROJECT_ID}.ecommerce_reports.daily_revenue`
    """)

    product_perf = run_query(f"""
        SELECT COUNT(*) AS total_products,
               MAX(report_date) AS latest_date
        FROM `{PROJECT_ID}.ecommerce_reports.product_performance`
    """)

    channel = run_query(f"""
        SELECT COUNT(*) AS total_channels,
               ROUND(SUM(total_revenue),2) AS total_revenue
        FROM `{PROJECT_ID}.ecommerce_reports.channel_performance`
    """)

    return {
        "check_date"         : str(today),
        "raw_orders"         : raw_orders[0] if raw_orders else {},
        "daily_revenue"      : daily_revenue[0] if daily_revenue else {},
        "product_performance": product_perf[0] if product_perf else {},
        "channel_performance": channel[0] if channel else {},
    }

def rule_based_decision(metrics):
    """Fallback: Make decision using rules (no AI needed)"""
    today_orders  = metrics["raw_orders"].get("today_orders", 0)
    today_exists  = metrics["daily_revenue"].get("today_exists", 0)
    latest_date   = str(metrics["raw_orders"].get("latest_date", ""))
    yesterday     = str(date.today() - timedelta(days=1))
    days_old      = (date.today() - date.fromisoformat(latest_date)).days \
                    if latest_date else 99

    if today_orders == 0:
        return {
            "action"  : "generate_orders",
            "reason"  : "No orders found for today",
            "severity": "critical",
            "details" : f"today_orders={today_orders}"
        }
    elif today_orders < 10:
        return {
            "action"  : "generate_orders",
            "reason"  : "Very few orders today — likely incomplete",
            "severity": "warning",
            "details" : f"today_orders={today_orders}"
        }
    elif today_exists == 0:
        return {
            "action"  : "refresh_reports",
            "reason"  : "Report tables not updated for today",
            "severity": "warning",
            "details" : f"today_exists={today_exists}"
        }
    elif days_old > 2:
        return {
            "action"  : "generate_orders",
            "reason"  : f"Data is {days_old} days old",
            "severity": "warning",
            "details" : f"latest_date={latest_date}"
        }
    else:
        return {
            "action"  : "do_nothing",
            "reason"  : "All metrics look healthy",
            "severity": "healthy",
            "details" : f"today_orders={today_orders}, revenue=${metrics['raw_orders'].get('total_revenue',0):,.2f}"
        }

def ai_decide_action(metrics):
    """Ask Gemini AI to decide — fallback to rules if quota exceeded"""
    print("  → Asking Gemini AI to decide action...")

    prompt = f"""
You are an autonomous AI Data Engineering Agent.
Analyze these pipeline metrics and decide what action to take.

Today's Date: {date.today()}

PIPELINE METRICS:
{json.dumps(metrics, indent=2, default=str)}

DECISION RULES:
- today_orders = 0 → generate_orders
- today_orders < 10 → generate_orders
- today_exists = 0 in daily_revenue → refresh_reports
- latest_date more than 2 days old → generate_orders
- Revenue drop > 80% compared to yesterday → alert_only
- Everything normal → do_nothing

Respond ONLY in this exact JSON format:
{{
  "action": "generate_orders",
  "reason": "one sentence explaining why",
  "severity": "critical",
  "details": "specific numbers from metrics"
}}

ONLY output JSON. No other text.
"""

    response = ask_gemini(prompt)

    if response:
        try:
            start    = response.find("{")
            end      = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                decision = json.loads(json_str)
                print("  ✅ AI decision received!")
                return decision
        except Exception:
            pass

    # Fallback to rule-based
    print("  ⚠️ Gemini quota exceeded — using rule-based decision")
    decision = rule_based_decision(metrics)
    print(f"  ✅ Rule-based decision: {decision['action'].upper()}")
    return decision

def run_generate_orders():
    print("  🔧 Fix: Generating today's orders...")
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "generate_today.py"
        )
        result = subprocess.run(
            ["python", script_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("  ✅ Orders generated!")
            return {"success": True, "output": result.stdout[-300:]}
        else:
            print(f"  ❌ Failed: {result.stderr[-200:]}")
            return {"success": False, "error": result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_refresh_reports():
    print("  🔧 Fix: Refreshing reports...")
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "refresh_reports.py"
        )
        result = subprocess.run(
            ["python", script_path],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            print("  ✅ Reports refreshed!")
            return {"success": True, "output": result.stdout[-300:]}
        else:
            print(f"  ❌ Failed: {result.stderr[-200:]}")
            return {"success": False, "error": result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_do_nothing():
    print("  ✅ Pipeline healthy — no action needed!")
    return {"success": True, "output": "Pipeline is healthy"}

def run_alert_only():
    print("  🚨 Issue too complex — alerting human!")
    return {"success": False, "output": "Requires human intervention"}

def verify_fix(action):
    print("  → Verifying...")
    today = date.today()

    if action == "generate_orders":
        result = run_query(f"""
            SELECT COUNTIF(DATE(order_date) = '{today}') AS today_orders
            FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
        """)
        orders = result[0].get("today_orders", 0) if result else 0
        if orders > 0:
            return {"verified": True,  "message": f"✅ {orders} orders now exist for today!"}
        else:
            return {"verified": False, "message": "❌ Still no orders after fix"}

    elif action == "refresh_reports":
        result = run_query(f"""
            SELECT COUNTIF(report_date = '{today}') AS today_exists
            FROM `{PROJECT_ID}.ecommerce_reports.daily_revenue`
        """)
        exists = result[0].get("today_exists", 0) if result else 0
        if exists > 0:
            return {"verified": True,  "message": "✅ Reports updated successfully!"}
        else:
            return {"verified": False, "message": "❌ Reports still not updated"}

    return {"verified": True, "message": "✅ No fix needed — pipeline healthy"}

def generate_report(metrics, decision, fix_result, verification):
    """Try Gemini first, fallback to template report"""
    prompt = f"""
Write a brief AI agent status report.

Today: {date.today()}
Action taken: {decision.get('action')}
Reason: {decision.get('reason')}
Severity: {decision.get('severity')}
Fix worked: {verification.get('verified')}
Fix message: {verification.get('message')}
Today's orders: {metrics['raw_orders'].get('today_orders', 0)}
Total revenue: ${metrics['raw_orders'].get('total_revenue', 0):,.2f}

Write sections:
1. AGENT ACTION SUMMARY
2. PIPELINE STATUS
3. FIX VERIFICATION
4. PLAIN ENGLISH SUMMARY
"""
    ai_report = ask_gemini(prompt)

    if ai_report:
        return ai_report

    # Fallback template report
    today_orders = metrics["raw_orders"].get("today_orders", 0)
    total_revenue = metrics["raw_orders"].get("total_revenue", 0)
    action   = decision.get("action", "unknown")
    severity = decision.get("severity", "unknown")
    reason   = decision.get("reason", "")
    verified = verification.get("verified", False)
    ver_msg  = verification.get("message", "")

    return f"""
1. AGENT ACTION SUMMARY
   Action taken : {action.upper()}
   Reason       : {reason}
   Severity     : {severity.upper()}

2. PIPELINE STATUS
   Today's orders : {today_orders}
   Total revenue  : ${total_revenue:,.2f}
   Latest date    : {metrics['raw_orders'].get('latest_date', 'unknown')}

3. FIX VERIFICATION
   Verified : {'YES' if verified else 'NO'}
   Result   : {ver_msg}

4. PLAIN ENGLISH SUMMARY
   The AI agent checked the ecommerce pipeline on {date.today()}.
   Action taken was {action.replace('_', ' ')}: {reason}.
   Pipeline status: {'All good!' if severity == 'healthy' else 'Issue detected and handled.'}
"""

def save_report(report, decision, metrics):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = os.path.join(REPORTS_DIR, f"agent_report_{timestamp}.txt")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    content = f"""
{'='*60}
🤖 AI AUTO-FIX AGENT REPORT
Generated  : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Project    : {PROJECT_ID}
Action     : {decision.get('action','unknown').upper()}
Severity   : {decision.get('severity','unknown').upper()}
{'='*60}

{report}

{'='*60}
RAW METRICS:
{'='*60}
{json.dumps(metrics, indent=2, default=str)}
{'='*60}
"""

    with open(filename, "w") as f:
        f.write(content)

    print(f"  ✅ Report saved: {filename}")
    return content

def main():
    print("=" * 60)
    print("🤖 BIGQUERY AI AUTO-FIX AGENT")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    print("📊 STEP 1: Collecting pipeline metrics...")
    metrics = collect_metrics()
    print(f"  Today orders : {metrics['raw_orders'].get('today_orders', 0)}")
    print(f"  Latest date  : {metrics['raw_orders'].get('latest_date', 'unknown')}")
    print(f"  Revenue      : ${metrics['raw_orders'].get('total_revenue', 0):,.2f}")
    print()

    print("🧠 STEP 2: AI deciding action...")
    decision = ai_decide_action(metrics)
    print(f"  Action   : {decision.get('action','').upper()}")
    print(f"  Reason   : {decision.get('reason','')}")
    print(f"  Severity : {decision.get('severity','').upper()}")
    print()

    print("🔧 STEP 3: Executing action...")
    action     = decision.get("action", "do_nothing")
    fix_result = {"success": True, "output": "No action needed"}

    if action == "generate_orders":
        fix_result = run_generate_orders()
        if fix_result.get("success"):
            print("  → Also refreshing reports...")
            run_refresh_reports()
    elif action == "refresh_reports":
        fix_result = run_refresh_reports()
    elif action == "do_nothing":
        fix_result = run_do_nothing()
    elif action == "alert_only":
        fix_result = run_alert_only()
    print()

    print("✅ STEP 4: Verifying fix...")
    verification = verify_fix(action)
    print(f"  {verification.get('message', '')}")
    print()

    print("📝 STEP 5: Generating report...")
    final_report = generate_report(
        metrics, decision, fix_result, verification
    )

    print("💾 STEP 6: Saving report...")
    full_report = save_report(final_report, decision, metrics)

    print()
    print(full_report)
    print("🤖 Agent complete!")

if __name__ == "__main__":
    main()
