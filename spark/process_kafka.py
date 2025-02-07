from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, expr, avg, current_timestamp


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

kafka_stream = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:29092")
    .option("subscribe", "user_clicks")
    .load()
)

######################

clicks_df = kafka_stream.selectExpr("CAST(value AS STRING) as json").selectExpr(
    "get_json_object(json, '$.user_id') AS user_id",
    "get_json_object(json, '$.event_type') AS event_type",
    "get_json_object(json, '$.product_id') AS product_id",
    "get_json_object(json, '$.category') AS category",
    "get_json_object(json, '$.referrer') AS referrer",
    "CAST(get_json_object(json, '$.timestamp') AS TIMESTAMP) AS timestamp",
)

######################

click_to_purchase = (
    clicks_df.withWatermark("timestamp", "1 minutes")  # Add watermark
    .groupBy("product_id", "timestamp")  # Include timestamp for historical tracking
    .agg(
        count(expr("event_type = 'click' OR NULL")).alias("clicks"),
        count(expr("event_type = 'purchase' OR NULL")).alias("purchases"),
    )
    .withColumn("probability", col("purchases") / col("clicks"))
    .withColumn("processed_at", current_timestamp())  # Append processing timestamp
)


sales_trend = (
    clicks_df.withWatermark("timestamp", "1 minutes")  # Add watermark
    .filter(col("event_type") == "purchase")
    .groupBy("product_id", "timestamp")
    .agg(count("*").alias("sales"), avg("timestamp").alias("trend_score"))
    .withColumn("processed_at", current_timestamp())  # Append processing timestamp
)

######################


def write_to_jdbc_in_batches(df, batch_id, table_name):
    (
        df.write.format("jdbc")
        .option("url", "jdbc:clickhouse://clickhouse:8123")
        .option("dbtable", table_name)
        .option("user", "default")
        .option("password", "")
        .mode("append")
        .save()
    )


click_query = (
    clicks_df.writeStream.foreachBatch(
        lambda df, batch_id: write_to_jdbc_in_batches(df, batch_id, "user_clicks")
    )
    .option("checkpointLocation", "/tmp/spark-checkpoints/user_clicks")
    .outputMode("append")
    .start()
)


click_to_purchase_query = (
    click_to_purchase.writeStream.foreachBatch(
        lambda df, batch_id: write_to_jdbc_in_batches(
            df, batch_id, "purchase_predictions"
        )
    )
    .option("checkpointLocation", "/tmp/spark-checkpoints/purchase_predictions")
    .outputMode(
        "complete"
    )  # Consider using "append" if appropriate for your aggregation
    .start()
)


# Write the sales_trend streaming DataFrame using foreachBatch
sales_trend_query = (
    sales_trend.writeStream.foreachBatch(
        lambda df, batch_id: write_to_jdbc_in_batches(df, batch_id, "product_sales")
    )
    .option("checkpointLocation", "/tmp/spark-checkpoints/product_sales")
    .outputMode("complete")
    .start()
)

######################


def write_parquet_in_batches(df, batch_id, path):
    df.write.mode("append").parquet(path)


click_to_purchase.writeStream.foreachBatch(
    lambda df, batch_id: write_parquet_in_batches(
        df, batch_id, "hdfs://hdfs-namenode:9000/data/purchase_predictions/"
    )
).option("checkpointLocation", "/tmp/hive-checkpoints/purchase_predictions").start()


sales_trend.writeStream.foreachBatch(
    lambda df, batch_id: write_parquet_in_batches(
        df, batch_id, "hdfs://hdfs-namenode:9000/data/product_sales/"
    )
).option("checkpointLocation", "/tmp/hive-checkpoints/product_sales").start()

spark.streams.awaitAnyTermination()
