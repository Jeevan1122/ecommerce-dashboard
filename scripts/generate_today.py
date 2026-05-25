from datetime import date, timedelta
import random
import pandas as pd
from faker import Faker
from google.cloud import bigquery

fake = Faker()
random.seed()

PROJECT_ID = "ecommerce-dashboard-497321"

PRODUCTS = [
    ("PRD001", "iPhone 15 Pro",      "Electronics", "Apple",        999.99),
    ("PRD002", "Samsung Galaxy S24", "Electronics", "Samsung",      849.99),
    ("PRD003", "Sony Headphones",    "Electronics", "Sony",         299.99),
    ("PRD004", "Dell Laptop",        "Electronics", "Dell",        1199.99),
    ("PRD005", "Nike Air Max",       "Clothing",    "Nike",         189.99),
    ("PRD006", "Adidas Ultraboost",  "Clothing",    "Adidas",       179.99),
    ("PRD007", "Zara Jacket",        "Clothing",    "Zara",          89.99),
    ("PRD008", "IKEA Desk",          "Home",        "IKEA",         249.99),
    ("PRD009", "Philips Smart Bulb", "Home",        "Philips",       49.99),
    ("PRD010", "Bosch Blender",      "Home",        "Bosch",         79.99),
    ("PRD011", "Puma Running Shoes", "Sports",      "Puma",         129.99),
    ("PRD012", "Yoga Mat",           "Sports",      "Adidas",        39.99),
    ("PRD013", "Python Programming", "Books",       "Penguin",       49.99),
    ("PRD014", "Data Engineering",   "Books",       "HarperCollins", 59.99),
    ("PRD015", "LG Smart TV 55",     "Electronics", "LG",           699.99),
]

STATUSES = ["COMPLETED","COMPLETED","COMPLETED","SHIPPED","CANCELLED"]
CHANNELS = ["Website","Mobile App","Marketplace","Social Media","Email Campaign"]
PAYMENTS = ["Credit Card","Debit Card","PayPal","Apple Pay","Google Pay"]
STATES   = ["CA","NY","TX","FL","IL","WA","MA","CO"]

def generate_recent_orders():
    today  = date.today()
    orders = []
    for days_back in range(0, 3):
        order_date = today - timedelta(days=days_back)
        n = random.randint(40, 80)
        print(f"  → Generating {n} orders for {order_date}...")
        for i in range(n):
            prod     = random.choice(PRODUCTS)
            quantity = random.randint(1, 5)
            discount = random.choice([0, 5, 10, 15, 20])
            gross    = prod[4] * quantity
            disc_amt = gross * discount / 100
            total    = round(gross - disc_amt, 2)
            profit   = round(total * 0.4, 2)
            orders.append({
                "order_id"      : f"ORD-{order_date}-{str(i+1).zfill(4)}",
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
                "status"        : random.choice(STATUSES),
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
    table_ref  = f"{PROJECT_ID}.ecommerce_raw.raw_orders"
    job_config = bigquery.LoadJobConfig(
        write_disposition = bigquery.WriteDisposition.WRITE_APPEND,
        autodetect        = True,
    )
    df["order_date"] = pd.to_datetime(df["order_date"])
    job = client.load_table_from_dataframe(
        df, table_ref, job_config=job_config
    )
    job.result()
    print(f"✅ Loaded {len(df)} orders!")

if __name__ == "__main__":
    today = date.today()
    print(f"🚀 Generating orders for last 3 days...")
    df = generate_recent_orders()
    load_to_bigquery(df)
    print(f"""
═══════════════════════════════════
✅ Done! Data added for:
   {today}
   {today - timedelta(days=1)}
   {today - timedelta(days=2)}
   Total: {len(df)} orders
═══════════════════════════════════
    """)
