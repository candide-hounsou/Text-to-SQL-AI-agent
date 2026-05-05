import sqlite3

import pytest


@pytest.fixture(scope="session")
def sample_db_path(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("fixtures") / "sample.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE customers (customer_id TEXT, customer_city TEXT, customer_state TEXT)")
    conn.execute("INSERT INTO customers VALUES ('c1', 'sao paulo', 'SP')")
    conn.execute("INSERT INTO customers VALUES ('c2', 'rio de janeiro', 'RJ')")
    conn.execute("CREATE TABLE orders (order_id TEXT, customer_id TEXT, order_status TEXT)")
    conn.execute("INSERT INTO orders VALUES ('o1', 'c1', 'delivered')")
    conn.execute("INSERT INTO orders VALUES ('o2', 'c2', 'canceled')")
    conn.execute("CREATE TABLE products (product_id TEXT, product_category_name TEXT, product_weight_g REAL)")
    conn.execute("INSERT INTO products VALUES ('p1', 'beleza_saude', 500.0)")
    conn.commit()
    conn.close()
    return str(db_path)
