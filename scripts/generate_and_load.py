"""
Generates e-commerce data and loads directly into BigQuery
No GCS needed — straight to BigQuery!
"""
import random
from datetime import datetime, timedelta, date
import pandas as pd
from faker import Faker
from google.cloud import bigquery

fake = Faker()
Faker.seed(42)
random.seed(42)

PROJECT_ID = "ecommerce-dashboard-497321"
DATASET    = "ecommerce_raw"
TABLE      = "raw_orders"

CATEGORIES = {
    "Electronics" : ["Apple", "Samsung", "Sony", "Dell"],
    "Clothing"    : ["Nike", "Adidas", "Zara", "H&M"],
    "Home"        : ["IKEA", "Philips", "Bosch", "LG"],
    "Sports"      : ["Nike", "Adidas", "Puma", "Reebok"],
    "Books"       : ["Penguin", "HarperCollins", "Random House"],
}

PRODUCTS = [
    ("PRD001", "iPhone 15 Pro",      "Electronics", "Apple",         999.99),
    ("PRD002", "Samsung Galaxy S24", "Electronics", "Samsung",       849.99),
    ("PRD003", "Sony Headphones",    "Electronics", "Sony",          299.99),
    ("PRD004", "Dell Laptop",        "Electronics", "Dell",         1199.99),
    ("PRD005", "Nike Air Max",       "Clothing",    "Nike",          189.99),
    ("PRD006", "Adidas Ultraboost",  "Clothing",    "Adidas",        179.99),
    ("PRD007", "Zara Jacket",        "Clothing",    "Zara",           89.99),
    ("PRD008", "IKEA Desk",          "Home",        "IKEA",          249.99),
    ("PRD009", "Philips Smart Bulb", "Home",        "Philips",        49.99),
    ("PRD010", "Bosch Blender",      "Home",        "Bosch",          79.99),
    ("PRD011", "Puma Running Shoes", "Sports",      "Puma",          129.99),
    ("PRD012", "Yoga Mat",           "Sports",      "Adidas",         39.99),
    ("PRD013", "Python Programming", "Books",       "Penguin",        49.99),
    ("PRD014", "Data Engineering",   "Books",       "HarperCollins",  59.99),
    ("PRD015", "LG Smart TV 55",     "Electronics", "LG",            699.99),
]

SEGMENTS   = ["Champions", "Loyal Customers", "Promising",
               "Needs Attention", "At Risk"]
STATUSES   = ["COMPLETED", "COMPLETED", "COMPLETED",
               "SHIPPED", "PENDING", "CANCELLED"]
CHANNELS   = ["Website", "Mobile App", "Marketplace",
               "Social Media", "Email Campaign"]
PAYMENTS   = ["Credit Card", "Debit Card", "PayPal",
               "Apple Pay", "Google Pay"]
STATES     = ["CA", "NY", "TX", "FL", "IL", "WA", "MA", "CO"]

def generate_orders(n=5000):
    print(f"🚀 Generating {n} orders...")
    orders = []
    for i in range(n):
        prod         = random.choice(PRODUCTS)
        quantity     = random.randint(1, 5)
        discount     = random.choice([0, 5, 10, 15, 20])
        gross        = prod[4] * quantity
        disc_amt     = gross * discount / 100
        total        = round(gross - disc_amt, 2)
        cost         = round(total * 0.6, 2)
        profit       = round(total - cost, 2)
        order_date   = fake.date_between(
            start_date=date(2024, 1, 1),
            end_date=date(2026, 5, 23)
        )
        status       = random.choice(STATUSES)
        segment      = random.choice(SEGMENTS)

        orders.append({
            "order_id"      : f"ORD-{str(i+1).zfill(6)}",
            "customer_id"   : f"CST-{random.randint(1,500):06d}",
            "customer_name" : fake.name(),
            "product_id"    : prod[0],
            "product_name"  : prod[1],
            "category"      : prod[2],
            "brand"         : prod[3],
            "quantity"      : quantity,
            "unit_price"    : prod[4],
            "discount_pct"  : discount,
            "total_amount"  : total,
            "profit"        : profit,
            "status"        : status,
            "payment_method": random.choice(PAYMENTS),
            "sales_channel" : random.choice(CHANNELS),
            "order_date"    : order_date.isoformat(),
            "city"          : fake.city(),
            "state"         : random.choice(STATES),
            "country"       : "US",
        })
    return pd.DataFrame(orders)

def load_to_bigquery(df):
    print("📤 Loading to BigQuery...")
    client     = bigquery.Client(project=PROJECT_ID)
    table_ref  = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    job_config = bigquery.LoadJobConfig(
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect        = True,
    )
    df["order_date"] = pd.to_datetime(df["order_date"])
    job = client.load_table_from_dataframe(
        df, table_ref, job_config=job_config
    )
    job.result()
    print(f"✅ Loaded {len(df):,} rows into {table_ref}")

def main():
    df = generate_orders(5000)
    load_to_bigquery(df)
    print("""
═══════════════════════════════════
✅ Data Generation Complete!
   Orders : 5,000
   Products: 15
   Date Range: Jan 2024 - May 2026
═══════════════════════════════════
    """)

if __name__ == "__main__":
    main()
