FEW_SHOT_EXAMPLES = """
--- FEW-SHOT EXAMPLES ---
Example 1 (Basic Aggregation & Filtering):
User: "Combien y a-t-il de clients dans la ville de sao paulo ?"
SQL: SELECT COUNT(customer_id) FROM customers WHERE customer_city = 'sao paulo';

Example 2 (Complex Joins & Language Translation):
User: "Quel est le top 3 des catégories avec le plus grand nombre d'articles vendus ?"
SQL: SELECT ct.product_category_name_english, COUNT(oi.order_item_id) AS total_items FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN category_translation ct ON p.product_category_name = ct.product_category_name GROUP BY ct.product_category_name_english ORDER BY total_items DESC LIMIT 3;

Example 3 (Date Handling in SQLite):
User: "Combien de commandes ont été livrées en 2018 ?"
SQL: SELECT COUNT(order_id) FROM orders WHERE order_status = 'delivered' AND strftime('%Y', order_delivered_customer_date) = '2018';
-------------------------
"""
