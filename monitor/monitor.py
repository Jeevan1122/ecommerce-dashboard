"""
BigQuery AI Monitor - Ecommerce Only
Clean report - no raw metrics shown
"""
import os
import json
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID     = os.getenv("GCP_PROJECT_ID")
bq_client      = bigquery.Client(project=PROJECT_ID)
REPORTS_DIR    = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reports"
)

def ask_gemini(prompt):
    url      = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload  = {"contents": [{"parts": [{"text": prompt}]}]}
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
    print("  → Collecting ecommerce metrics...")
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

def fallback_report(metrics):
    today         = metrics["check_date"]
    today_orders  = metrics["raw_orders"].get("today_orders", 0)
    yest_orders   = metrics["raw_orders"].get("yesterday_orders", 0)
    total_revenue = metrics["raw_orders"].get("total_revenue", 0)
    latest_date   = str(metrics["raw_orders"].get("latest_date", ""))
    today_exists  = metrics["daily_revenue"].get("today_exists", 0)
    total_products= metrics["product_performance"].get("total_products", 0)
    total_channels= metrics["channel_performance"].get("total_channels", 0)

    if today_orders == 0:
        status = "CRITICAL"
        issue  = f"No orders recorded for today ({today})"
        rec    = "Run generate_today.py immediately"
    elif today_orders < 10:
        status = "WARNING"
        issue  = f"Only {today_orders} orders today — very low"
        rec    = "Check generate_today.py ran correctly"
    elif today_exists == 0:
        status = "WARNING"
        issue  = "Daily revenue table not updated today"
        rec    = "Run refresh_reports.py"
    else:
        status = "HEALTHY"
        issue  = "No issues detected"
        rec    = "No action needed"

    if yest_orders > 0 and today_orders > 0:
        change   = ((today_orders - yest_orders) / yest_orders) * 100
        trend    = f"{'Up' if change >= 0 else 'Down'} {abs(change):.1f}% vs yesterday"
    else:
        trend    = "No comparison available"

    return f"""
1. OVERALL HEALTH STATUS
   Status  : {status}
   Summary : {issue}

2. PIPELINE FINDINGS
   Today orders     : {today_orders} ({trend})
   Yesterday orders : {yest_orders}
   Total revenue    : ${total_revenue:,.2f}
   Products tracked : {total_products}
   Sales channels   : {total_channels}
   Data current to  : {latest_date}

3. ISSUES DETECTED
   {issue if status != "HEALTHY" else "No issues found"}

4. RECOMMENDATIONS
   {rec}

5. PLAIN ENGLISH SUMMARY
   The ecommerce pipeline was checked on {today}.
   Current status is {status} with {today_orders}
   orders today generating ${total_revenue:,.2f}
   in total revenue. {rec}.
"""

def analyze_with_gemini(metrics):
    print("  → Sending to Gemini AI...")
    prompt = f"""
You are an expert Data Engineer monitoring
an ecommerce BigQuery pipeline.
Analyze these metrics and write a health report.

Today's Date: {date.today()}

ECOMMERCE METRICS:
- Today orders    : {metrics['raw_orders'].get('today_orders', 0)}
- Yesterday orders: {metrics['raw_orders'].get('yesterday_orders', 0)}
- Total revenue   : ${metrics['raw_orders'].get('total_revenue', 0):,.2f}
- Latest date     : {metrics['raw_orders'].get('latest_date', 'unknown')}
- Today in reports: {'Yes' if metrics['daily_revenue'].get('today_exists', 0) else 'No'}
- Products        : {metrics['product_performance'].get('total_products', 0)}
- Channels        : {metrics['channel_performance'].get('total_channels', 0)}

Write ONLY these 5 sections.
No JSON. No raw data. Clean text only:

1. OVERALL HEALTH STATUS
2. PIPELINE FINDINGS
3. ISSUES DETECTED
4. RECOMMENDATIONS
5. PLAIN ENGLISH SUMMARY
"""
    return ask_gemini(prompt)

def save_report(report):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = os.path.join(
        REPORTS_DIR,
        f"ecommerce_health_{timestamp}.txt"
    )
    os.makedirs(REPORTS_DIR, exist_ok=True)

    full_report = f"""
{'='*60}
ECOMMERCE PIPELINE AI MONITOR
Generated : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Project   : {PROJECT_ID}
{'='*60}

{report}

{'='*60}
END OF REPORT
{'='*60}
"""

    with open(filename, "w") as f:
        f.write(full_report)

    print(f"  ✅ Report saved: {filename}")
    return full_report

def main():
    print("=" * 60)
    print("ECOMMERCE PIPELINE AI MONITOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    print("Step 1: Collecting metrics...")
    metrics = collect_metrics()
    print("  ✅ Done!")
    print()

    print("Step 2: Analyzing with Gemini AI...")
    ai_report = analyze_with_gemini(metrics)

    if ai_report:
        print("  ✅ Gemini AI report ready!")
        report = ai_report
    else:
        print("  ⚠️ Gemini unavailable — using rule-based report")
        report = fallback_report(metrics)

    print()
    print("Step 3: Saving report...")
    full_report = save_report(report)

    print()
    print(full_report)
    print("✅ Monitor complete!")

if __name__ == "__main__":
    main()
