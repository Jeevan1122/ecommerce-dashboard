# 🛒 E-Commerce Data Platform with AI Pipeline Monitor

> End-to-end automated GCP data engineering platform with AI-powered
> self-monitoring, auto-fix capabilities, and zero manual intervention —
> powered by BigQuery, Gemini AI, and GitHub Actions.

---

## 🔗 Live Links

| Resource | Link |
|----------|------|
| 📊 Live Dashboard | [E-Commerce Looker Studio Dashboard](https://datastudio.google.com/reporting/7ed1bb18-9d6b-43a9-a03c-11b4facc3e73) |
| 💻 GitHub Repo | [github.com/Jeevan1122/ecommerce-dashboard](https://github.com/Jeevan1122/ecommerce-dashboard) |

---

## 📌 What This Project Does

This platform automatically generates ecommerce order data daily,
loads it into BigQuery, refreshes all report tables, and uses
Google Gemini AI to monitor pipeline health — detecting anomalies
and fixing issues without any human intervention. The live Looker
Studio dashboard always shows fresh data every morning.

**Zero manual work. Mac can be completely OFF. Runs 100% on GitHub servers.**

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS                            │
│                                                                  │
│    11:00 PM Daily                       8:00 AM Daily            │
│    ┌────────────────────┐          ┌─────────────────────────┐   │
│    │  Ecommerce Pipeline│          │  AI Monitor + Agent     │   │
│    │  (Auto-triggered)  │          │  (Gemini AI powered)    │   │
│    └────────┬───────────┘          └────────────┬────────────┘   │
└─────────────┼────────────────────────────────────┼───────────────┘
              ↓                                    ↓
┌─────────────────────────┐          ┌─────────────────────────────┐
│   generate_today.py     │          │   monitor.py (Option A)     │
│   → 50-100 new orders   │          │   → Collects BQ metrics     │
│   → Realistic products  │          │   → Sends to Gemini AI      │
│   → Multiple channels   │          │   → Generates clean report  │
│   → Loads to BigQuery   │          │   → Saves to GitHub         │
└─────────────────────────┘          │                             │
              ↓                      │   agent.py (Option B)       │
┌─────────────────────────┐          │   → Detects pipeline issues │
│   refresh_reports.py    │          │   → AI decides action       │
│   → daily_revenue       │          │   → Auto-fixes problems     │
│   → product_performance │          │   → Verifies fix worked     │
│   → channel_performance │          │   → Saves report artifact   │
│   → customer_segments   │          └─────────────────────────────┘
└─────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────────────┐
│                         BIGQUERY                                 │
│                                                                  │
│  ecommerce_raw              ecommerce_reports                    │
│  ┌──────────────┐          ┌────────────────────┐               │
│  │ raw_orders   │    →     │ daily_revenue       │               │
│  │ 5,700+ rows  │          │ product_performance │               │
│  │ 875+ days    │          │ channel_performance │               │
│  └──────────────┘          │ customer_segments   │               │
│                            └────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      LOOKER STUDIO                               │
│           Live Dashboard — Auto-refreshes daily                  │
│   Revenue Trends │ Product Rankings │ Channel Mix │ Segments     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Blueprint

### Step 1 — Data Generation (11 PM Nightly)

GitHub Actions triggers `generate_today.py` automatically:

```
What it does:
→ Generates 50-100 realistic ecommerce orders
→ Products  : iPhone, Samsung, Nike, Dell, Sony, IKEA
→ Categories: Electronics, Clothing, Sports, Furniture
→ Channels  : Website, Mobile App, Marketplace, Email
→ Statuses  : Completed, Shipped, Processing, Cancelled
→ Prices    : Realistic ranges per product category
→ Loads directly to BigQuery ecommerce_raw.raw_orders
```

### Step 2 — Data Transformation (11 PM Nightly)

GitHub Actions triggers `refresh_reports.py` immediately after:

```
What it does:
→ daily_revenue table
   Aggregates: total orders, revenue, profit,
   avg order value, cancellation rate per day

→ product_performance table
   Aggregates: units sold, revenue rank,
   profit per product

→ channel_performance table
   Aggregates: revenue %, orders per
   sales channel

→ customer_segments table
   Segments: Champions, Loyal, Promising,
   At Risk customers
```

### Step 3 — Dashboard Refresh (Automatic)

```
Looker Studio reads from BigQuery directly:
→ Page 1: Revenue Trends (daily_revenue)
→ Page 2: Product Rankings (product_performance)
→ Page 3: Channel Mix (channel_performance)
→ Page 4: Customer Segments (customer_segments)

Dashboard refreshes automatically every morning!
```

### Step 4 — AI Monitor (8 AM Daily) — Option A

GitHub Actions triggers `monitor/monitor.py`:

```
STEP 1: Connect to BigQuery
STEP 2: Collect key metrics
        → today_orders
        → yesterday_orders
        → total_revenue
        → data freshness
        → report table status

STEP 3: Send metrics to Gemini AI
STEP 4: Gemini analyzes and writes report
STEP 5: Save clean report to GitHub artifact
```

### Step 5 — AI Auto-Fix Agent (8 AM Daily) — Option B

GitHub Actions triggers `monitor/agent.py`:

```
STEP 1: Collect BigQuery pipeline metrics

STEP 2: Gemini AI decides action
        → today_orders = 0    → generate_orders
        → tables stale        → refresh_reports
        → revenue anomaly     → alert_only
        → everything healthy  → do_nothing

STEP 3: Execute fix automatically
        → Runs generate_today.py if needed
        → Runs refresh_reports.py if needed

STEP 4: Verify fix worked
        → Re-queries BigQuery to confirm

STEP 5: Generate clean report
        → No raw data shown
        → Business-readable format

STEP 6: Save report as GitHub artifact
        → Available for 30 days
        → Downloadable as ZIP
```

---

## 🤖 AI Monitor — Sample Report

```
============================================================
ECOMMERCE PIPELINE AI MONITOR
Generated : 2026-05-27 08:00:00
Project   : ecommerce-dashboard-497321
============================================================

1. OVERALL HEALTH STATUS
   Status  : HEALTHY
   Summary : All systems operating normally

2. PIPELINE FINDINGS
   Today orders     : 87 (Up 12% vs yesterday)
   Yesterday orders : 78
   Total revenue    : $5,342,112.72
   Products tracked : 15
   Sales channels   : 5
   Data current to  : 2026-05-27

3. ISSUES DETECTED
   No issues found

4. RECOMMENDATIONS
   No action needed

5. PLAIN ENGLISH SUMMARY
   The ecommerce pipeline is running smoothly today
   with 87 orders processed. Revenue is up 12%
   versus yesterday. All report tables are current
   and the dashboard shows fresh live data.

============================================================
END OF REPORT
============================================================
```

---

## 🚨 Real Anomaly Detection Example

```
============================================================
ECOMMERCE PIPELINE AI MONITOR
Generated : 2026-05-26 08:00:00
============================================================

1. OVERALL HEALTH STATUS
   Status  : CRITICAL
   Summary : No orders recorded for today

2. PIPELINE FINDINGS
   Today orders     : 0 (Down 100% vs yesterday)
   Yesterday orders : 151
   Total revenue    : $5,342,112.72

3. ISSUES DETECTED
   No orders recorded for 2026-05-26
   Pipeline appears to have failed overnight

4. RECOMMENDATIONS
   Run generate_today.py immediately

5. PLAIN ENGLISH SUMMARY
   Critical issue detected — no new orders
   processed today. The AI agent automatically
   ran the fix script and added 72 new orders.
   Pipeline restored without human intervention.

============================================================
END OF REPORT
============================================================
```

---

## 📁 Project Structure

```
ecommerce-dashboard/
│
├── scripts/
│   ├── generate_today.py        # Generates daily orders
│   └── refresh_reports.py       # Refreshes BigQuery tables
│
├── monitor/
│   ├── monitor.py               # Option A: AI health monitor
│   ├── agent.py                 # Option B: AI auto-fix agent
│   └── reports/                 # Local report storage
│
├── dags/
│   └── ecommerce_pipeline.py    # Apache Airflow DAG
│
├── .github/
│   └── workflows/
│       ├── daily_pipeline.yml   # 11 PM: generate + refresh
│       └── daily_monitor.yml    # 8 AM: monitor + auto-fix
│
└── README.md
```

---

## 🗄️ BigQuery Data Model

```
ecommerce_raw.raw_orders
├── order_id          STRING       # Unique order identifier
├── customer_id       STRING       # Customer identifier
├── product_name      STRING       # Product name
├── category          STRING       # Product category
├── quantity          INT64        # Units ordered
├── unit_price        FLOAT64      # Price per unit
├── total_amount      FLOAT64      # Total order value
├── profit            FLOAT64      # Profit on order
├── status            STRING       # Order status
├── sales_channel     STRING       # Sales channel
└── order_date        TIMESTAMP    # Order timestamp

ecommerce_reports.daily_revenue
├── report_date        DATE        # Reporting date
├── total_orders       INT64       # Orders count
├── total_revenue      FLOAT64     # Total revenue
├── total_profit       FLOAT64     # Total profit
├── profit_margin_pct  FLOAT64     # Margin %
├── avg_order_value    FLOAT64     # Average order
└── cancellation_rate  FLOAT64     # Cancellation %

ecommerce_reports.product_performance
├── product_name       STRING      # Product name
├── category           STRING      # Category
├── units_sold         INT64       # Units sold
├── total_revenue      FLOAT64     # Revenue
├── total_profit       FLOAT64     # Profit
└── revenue_rank       INT64       # Revenue rank

ecommerce_reports.channel_performance
├── sales_channel      STRING      # Channel name
├── total_orders       INT64       # Orders count
├── total_revenue      FLOAT64     # Revenue
└── revenue_pct        FLOAT64     # Revenue share %

ecommerce_reports.customer_segments
├── customer_segment   STRING      # Segment name
├── total_customers    INT64       # Customer count
├── total_revenue      FLOAT64     # Segment revenue
└── avg_order_value    FLOAT64     # Avg order value
```

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Total orders processed | 5,700+ |
| Total revenue tracked | $5.3M+ |
| Days of data | 875+ |
| Products tracked | 15 |
| Sales channels | 5 |
| Customer segments | 4 |
| Daily orders generated | 50-100 |
| Automation level | 100% |
| Manual work required | 0 minutes |
| Report retention | 30 days |
| Real anomaly detected | 55% order drop |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cloud platform | Google Cloud Platform | Infrastructure |
| Data warehouse | BigQuery | Storage + queries |
| AI monitoring | Google Gemini API | Analysis + reports |
| Orchestration | GitHub Actions | Daily automation |
| Local scheduler | Apache Airflow | Development DAGs |
| Dashboard | Looker Studio | Visualization |
| Language | Python 3.10 | All scripts |
| CI/CD | GitHub Actions | Deployment |
| Version control | GitHub | Code management |

---

## ⚙️ Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/Jeevan1122/ecommerce-dashboard.git
cd ecommerce-dashboard

# 2. Install dependencies
pip install google-cloud-bigquery
pip install python-dotenv
pip install requests
pip install pandas
pip install faker
pip install db-dtypes
pip install pyarrow

# 3. Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service_account_key.json"
export GEMINI_API_KEY="your_gemini_api_key_here"
export GCP_PROJECT_ID="your_gcp_project_id"

# 4. Generate today's data
python scripts/generate_today.py

# 5. Refresh all report tables
python scripts/refresh_reports.py

# 6. Run AI pipeline monitor
python monitor/monitor.py

# 7. Run AI auto-fix agent
python monitor/agent.py
```

---

## 🔐 GitHub Actions Setup

```
Step 1: Go to repository Settings → Secrets → Actions

Step 2: Add these two secrets:
   GCP_KEY        → Your GCP service account JSON (plain text)
   GEMINI_API_KEY → Your Google Gemini API key

Step 3: Push code to main branch

Step 4: Workflows run automatically:
   daily_pipeline.yml → 11 PM UTC every day
   daily_monitor.yml  → 8 AM UTC every day
```

---

## 🔄 Daily Automation Flow

```
11:00 PM UTC
   GitHub Actions wakes up automatically
        ↓
   generate_today.py runs (2 min)
   → 50-100 new orders created
   → Loaded to BigQuery
        ↓
   refresh_reports.py runs (3 min)
   → 4 report tables updated
   → Dashboard ready for morning
        ↓
08:00 AM UTC
   GitHub Actions wakes up automatically
        ↓
   agent.py runs (2 min)
   → Collects BigQuery metrics
   → Gemini AI analyzes pipeline
   → Auto-fix runs if needed
   → Report saved as artifact
        ↓
   You wake up to one of:
   ✅ "Pipeline healthy — 87 orders today!"
   🔧 "Issue detected and fixed automatically!"
```

---

## 🏆 Skills Demonstrated

**Data Engineering**
- BigQuery data warehousing and optimization
- Star schema data modeling
- ETL and ELT pipeline design
- SQL aggregation and window functions
- Partitioned and clustered tables

**Agentic AI and LLM Integration**
- Google Gemini API integration in production
- Agentic AI system with tool calling
- LLM-powered anomaly detection
- Autonomous decision making loop
- Intelligent fallback and error handling

**DevOps and Cloud**
- GitHub Actions CI/CD pipelines
- Scheduled workflow automation
- GCP IAM and service account management
- Apache Airflow DAG orchestration
- Secrets and credentials management

**Python Development**
- BigQuery Python client library
- REST API integration
- Subprocess automation
- Environment configuration
- Automated report generation

---

## 👨‍💻 Author

**Kodamati Jeevan Sai**
Senior Data Engineer and Team Lead
GCP Certified Associate Cloud Engineer
AWS Certified Data Engineer Associate

- LinkedIn: https://www.linkedin.com/in/kodamati-jeevan-sai-4b5390195
- GitHub: https://github.com/Jeevan1122

---

*Built with GCP · BigQuery · Gemini AI · GitHub Actions · Python · Looker Studio*
