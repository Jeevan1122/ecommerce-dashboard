"""
BigQuery AI Monitor - Ecommerce Only
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

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    data     = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini Error: {str(e)}\nResponse: {data}"

def run_query(sql):
    try:
        result = bq_client.query(sql).result()
        return [dict(row) for row in result]
    except Exception as e:
        return [{"error": str(e)}]

def collect_ecommerce_metrics():
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
        SELECT
            COUNT(*)         AS total_products,
            MAX(report_date) AS latest_date
        FROM `{PROJECT_ID}.ecommerce_reports.product_performance`
    """)

    customer_seg = run_query(f"""
        SELECT
            COUNT(*)             AS total_segments,
            SUM(total_customers) AS total_customers
        FROM `{PROJECT_ID}.ecommerce_reports.customer_segments`
    """)

    channel = run_query(f"""
        SELECT
            COUNT(*)                    AS total_channels,
            ROUND(SUM(total_revenue),2) AS total_revenue
        FROM `{PROJECT_ID}.ecommerce_reports.channel_performance`
    """)

    return {
        "check_date"         : str(today),
        "raw_orders"         : raw_orders[0] if raw_orders else {},
        "daily_revenue"      : daily_revenue[0] if daily_revenue else {},
        "product_performance": product_perf[0] if product_perf else {},
        "customer_segments"  : customer_seg[0] if customer_seg else {},
        "channel_performance": channel[0] if channel else {},
    }

def analyze_with_gemini(metrics):
    print("  → Sending to Gemini AI...")
    prompt = f"""
You are an expert Data Engineer monitoring an ecommerce BigQuery pipeline.
Analyze these metrics and provide a health report.

Today's Date: {date.today()}

ECOMMERCE PIPELINE METRICS:
{json.dumps(metrics, indent=2, default=str)}

Please provide:

1. OVERALL HEALTH STATUS
   - Healthy / Warning / Critical
   - One line summary

2. PIPELINE FINDINGS
   - Raw orders status
   - Revenue status
   - Today's data status
   - Any anomalies

3. ISSUES DETECTED
   - List problems or "No issues found"

4. RECOMMENDATIONS
   - Specific actions needed

5. PLAIN ENGLISH SUMMARY
   - Simple 3 sentences for business team

Be specific with numbers.
Flag if today's orders seem low or missing.
"""
    return ask_gemini(prompt)

def save_report(report, metrics):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = f"reports/ecommerce_health_{timestamp}.txt"
    os.makedirs("reports", exist_ok=True)

    full_report = f"""
{'='*60}
🛒 ECOMMERCE PIPELINE AI MONITOR
Generated : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Project   : {PROJECT_ID}
{'='*60}

{report}

{'='*60}
RAW METRICS:
{'='*60}
{json.dumps(metrics, indent=2, default=str)}
{'='*60}
"""

    with open(filename, "w") as f:
        f.write(full_report)

    print(f"  ✅ Report saved: {filename}")
    return full_report

def main():
    print("=" * 60)
    print("🛒 ECOMMERCE PIPELINE AI MONITOR")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    print("📊 Step 1: Collecting ecommerce metrics...")
    metrics = collect_ecommerce_metrics()
    print("  ✅ Metrics collected!")
    print()

    print("🧠 Step 2: Analyzing with Gemini AI...")
    ai_report = analyze_with_gemini(metrics)
    print("  ✅ Analysis complete!")
    print()

    print("💾 Step 3: Saving report...")
    full_report = save_report(ai_report, metrics)

    print()
    print(full_report)
    print("✅ Monitor complete!")

if __name__ == "__main__":
    main()
