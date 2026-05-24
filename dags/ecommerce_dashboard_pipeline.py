from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging

PROJECT_ID = "ecommerce-dashboard-497321"

def log_start(**context):
    logging.info(f"🚀 Dashboard pipeline started: {context['ds']}")

def log_end(**context):
    logging.info(f"✅ Dashboard pipeline completed: {context['ds']}")

default_args = {
    "owner"        : "jeevan.kodamati",
    "retries"      : 1,
    "retry_delay"  : timedelta(minutes=2),
}

with DAG(
    dag_id            = "ecommerce_dashboard_pipeline",
    default_args      = default_args,
    start_date        = days_ago(1),
    schedule_interval = "0 6 * * *",
    catchup           = False,
    tags              = ["ecommerce", "dashboard", "bigquery"],
) as dag:

    start = EmptyOperator(task_id="start")

    log_pipeline_start = PythonOperator(
        task_id         = "log_pipeline_start",
        python_callable = log_start,
    )

    refresh_daily_revenue = BigQueryInsertJobOperator(
        task_id     = "refresh_daily_revenue",
        gcp_conn_id = "google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                DELETE FROM `{PROJECT_ID}.ecommerce_reports.daily_revenue`
                WHERE report_date = CURRENT_DATE();

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
                WHERE DATE(order_date) = CURRENT_DATE()
                GROUP BY DATE(order_date);
                """,
                "useLegacySql": False,
            }
        },
    )

    refresh_product_performance = BigQueryInsertJobOperator(
        task_id     = "refresh_product_performance",
        gcp_conn_id = "google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                DELETE FROM `{PROJECT_ID}.ecommerce_reports.product_performance`
                WHERE report_date = CURRENT_DATE();

                INSERT INTO `{PROJECT_ID}.ecommerce_reports.product_performance`
                WITH stats AS (
                    SELECT
                        CURRENT_DATE()              AS report_date,
                        product_name,
                        category,
                        brand,
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
                """,
                "useLegacySql": False,
            }
        },
    )

    refresh_channel_performance = BigQueryInsertJobOperator(
        task_id     = "refresh_channel_performance",
        gcp_conn_id = "google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                DELETE FROM `{PROJECT_ID}.ecommerce_reports.channel_performance`
                WHERE report_date = CURRENT_DATE();

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
                    ) * 100, 2)                     AS revenue_pct
                FROM stats s, totals t;
                """,
                "useLegacySql": False,
            }
        },
    )

    log_pipeline_end = PythonOperator(
        task_id         = "log_pipeline_end",
        python_callable = log_end,
    )

    end = EmptyOperator(task_id="end")

    start >> log_pipeline_start
    log_pipeline_start >> [
        refresh_daily_revenue,
        refresh_product_performance,
        refresh_channel_performance
    ]
    [
        refresh_daily_revenue,
        refresh_product_performance,
        refresh_channel_performance
    ] >> log_pipeline_end >> end
