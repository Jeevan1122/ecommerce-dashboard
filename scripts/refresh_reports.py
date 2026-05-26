from google.cloud import bigquery

PROJECT_ID = "ecommerce-dashboard-497321"
client     = bigquery.Client(project=PROJECT_ID)

def run_query(sql, name):
    print(f"  → Refreshing {name}...")
    job = client.query(sql)
    job.result()
    print(f"  ✅ {name} done!")

run_query(f"""
    TRUNCATE TABLE `{PROJECT_ID}.ecommerce_reports.daily_revenue`;
    INSERT INTO `{PROJECT_ID}.ecommerce_reports.daily_revenue`
    SELECT
        DATE(order_date)                AS report_date,
        COUNT(DISTINCT order_id)        AS total_orders,
        ROUND(SUM(total_amount), 2)     AS total_revenue,
        ROUND(SUM(profit), 2)           AS total_profit,
        ROUND(SAFE_DIVIDE(
            SUM(profit), SUM(total_amount)
        ) * 100, 2)                     AS profit_margin_pct,
        ROUND(AVG(total_amount), 2)     AS avg_order_value,
        COUNTIF(status='COMPLETED')     AS completed_orders,
        COUNTIF(status='CANCELLED')     AS cancelled_orders,
        ROUND(SAFE_DIVIDE(
            COUNTIF(status='CANCELLED'),
            COUNT(order_id)
        ) * 100, 2)                     AS cancellation_rate
    FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
    GROUP BY DATE(order_date)
    ORDER BY report_date;
""", "daily_revenue")

run_query(f"""
    TRUNCATE TABLE `{PROJECT_ID}.ecommerce_reports.product_performance`;
    INSERT INTO `{PROJECT_ID}.ecommerce_reports.product_performance`
    WITH stats AS (
        SELECT
            CURRENT_DATE()              AS report_date,
            product_name, category, brand,
            COUNT(DISTINCT order_id)    AS total_orders,
            SUM(quantity)               AS units_sold,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(SUM(profit), 2)       AS total_profit
        FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
        WHERE status != 'CANCELLED'
        GROUP BY product_name, category, brand
    )
    SELECT *,
        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
    FROM stats;
""", "product_performance")

run_query(f"""
    TRUNCATE TABLE `{PROJECT_ID}.ecommerce_reports.channel_performance`;
    INSERT INTO `{PROJECT_ID}.ecommerce_reports.channel_performance`
    WITH stats AS (
        SELECT
            CURRENT_DATE()              AS report_date,
            sales_channel,
            COUNT(DISTINCT order_id)    AS total_orders,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(SUM(profit), 2)       AS total_profit
        FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
        GROUP BY sales_channel
    ),
    totals AS (SELECT SUM(total_revenue) AS grand FROM stats)
    SELECT s.*,
        ROUND(SAFE_DIVIDE(
            s.total_revenue, t.grand
        ) * 100, 2) AS revenue_pct
    FROM stats s, totals t;
""", "channel_performance")

run_query(f"""
    TRUNCATE TABLE `{PROJECT_ID}.ecommerce_reports.customer_segments`;
    INSERT INTO `{PROJECT_ID}.ecommerce_reports.customer_segments`
    WITH cust_stats AS (
        SELECT
            customer_id,
            COUNT(DISTINCT order_id)    AS total_orders,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM `{PROJECT_ID}.ecommerce_raw.raw_orders`
        WHERE status != 'CANCELLED'
        GROUP BY customer_id
    ),
    segmented AS (
        SELECT *,
            CASE
                WHEN total_revenue >= 5000
                 AND total_orders  >= 10 THEN 'Champions'
                WHEN total_revenue >= 2000
                 AND total_orders  >= 5  THEN 'Loyal Customers'
                WHEN total_orders  >= 3  THEN 'Promising'
                WHEN total_orders  = 2   THEN 'Needs Attention'
                ELSE 'At Risk'
            END AS customer_segment
        FROM cust_stats
    )
    SELECT
        CURRENT_DATE()                AS report_date,
        customer_segment,
        COUNT(customer_id)            AS total_customers,
        ROUND(SUM(total_revenue), 2)  AS total_revenue,
        ROUND(AVG(avg_order_value), 2) AS avg_order_value,
        SUM(total_orders)             AS total_orders
    FROM segmented
    GROUP BY customer_segment;
""", "customer_segments")

print("🎉 All reports refreshed successfully!")
