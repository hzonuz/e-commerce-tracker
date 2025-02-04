CREATE TABLE user_clicks (
    user_id String,
    session_id String,
    event_type String,  -- 'click', 'view', 'add_to_cart', 'purchase'
    product_id String,
    category String,
    timestamp DateTime,
    referrer String
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id);

CREATE TABLE product_sales (
    product_id String,
    category String,
    sales Int32,
    trend Float32,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (timestamp, product_id);

CREATE TABLE purchase_predictions (
    product_id String,
    probability Float32,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (timestamp, product_id);