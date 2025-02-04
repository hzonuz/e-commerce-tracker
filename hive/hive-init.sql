CREATE EXTERNAL TABLE user_clicks (
    user_id STRING,
    session_id STRING,
    event_type STRING,
    product_id STRING,
    category STRING,
    timestamp TIMESTAMP,
    referrer STRING
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:9000/data/user_clicks/';

CREATE EXTERNAL TABLE product_sales (
    product_id STRING,
    category STRING,
    sales INT,
    trend FLOAT,
    timestamp TIMESTAMP
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:9000/data/product_sales/';

CREATE EXTERNAL TABLE purchase_predictions (
    product_id STRING,
    probability FLOAT,
    timestamp TIMESTAMP
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:9000/data/purchase_predictions/';