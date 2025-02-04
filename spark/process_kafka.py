from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg, expr
from pyspark.sql.types import StringType, IntegerType, FloatType, TimestampType

# Initialize Spark
spark = (
    SparkSession.builder.appName("PurchasePrediction")
    .config(
        "spark.sql.catalog.clickhouse",
        "org.apache.spark.sql.clickhouse.ClickHouseCatalog",
    )
    .config("spark.sql.catalog.clickhouse.uri", "jdbc:clickhouse://clickhouse:8123")
    .enableHiveSupport()
    .getOrCreate()
)

# Read Kafka DataStream
kafka_stream = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "user_clicks")
    .load()
)

# Parse Kafka messages
clicks_df = (
    kafka_stream.selectExpr("CAST(value AS STRING)")
    .alias("json")
    .selectExpr(
        "get_json_object(json, '$.user_id') AS user_id",
        "get_json_object(json, '$.event_type') AS event_type",
        "get_json_object(json, '$.product_id') AS product_id",
        "CAST(get_json_object(json, '$.timestamp') AS TIMESTAMP) AS timestamp",
    )
)

# Aggregate Click-to-Purchase Conversion Rate
click_to_purchase = (
    clicks_df.groupBy("product_id")
    .agg(
        count(expr("event_type = 'click' OR NULL")).alias("clicks"),
        count(expr("event_type = 'purchase' OR NULL")).alias("purchases"),
    )
    .withColumn("probability", col("purchases") / col("clicks"))
)

# Compute Sales Trend (Weighted Moving Average)
sales_trend = (
    clicks_df.filter(col("event_type") == "purchase")
    .groupBy("product_id")
    .agg(count("*").alias("sales"), avg("timestamp").alias("trend_score"))
)

# Write Predictions to ClickHouse
click_to_purchase.writeStream.format("jdbc").option(
    "url", "jdbc:clickhouse://clickhouse:8123"
).option("dbtable", "purchase_predictions").option("user", "default").option(
    "password", ""
).option(
    "checkpointLocation", "/tmp/spark-checkpoints/"
).outputMode(
    "complete"
).start()

# Write Trend Data to ClickHouse
sales_trend.writeStream.format("jdbc").option(
    "url", "jdbc:clickhouse://clickhouse:8123"
).option("dbtable", "product_sales").option("user", "default").option(
    "password", ""
).option(
    "checkpointLocation", "/tmp/spark-checkpoints/"
).outputMode(
    "complete"
).start()

# Write to Hive for Batch Processing
click_to_purchase.writeStream.format("parquet").option(
    "path", "hdfs://namenode:9000/data/purchase_predictions/"
).option("checkpointLocation", "/tmp/hive-checkpoints/").outputMode("complete").start()

sales_trend.writeStream.format("parquet").option(
    "path", "hdfs://namenode:9000/data/product_sales/"
).option("checkpointLocation", "/tmp/hive-checkpoints/").outputMode("complete").start()

spark.streams.awaitAnyTermination()
