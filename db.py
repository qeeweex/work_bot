import sqlite3

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        role TEXT, -- 'customer' или 'worker'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица заказов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        worker_id INTEGER,
        platform TEXT,
        quantity INTEGER,
        deadline TEXT,
        status TEXT, -- например: 'new', 'in_progress', 'done'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES users(id),
        FOREIGN KEY (worker_id) REFERENCES users(id)
    )
    """)

    # Таблица статусов (опционально, если нужны отдельные статусы)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()

def add_user(telegram_id, username, role):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, role) VALUES (?, ?, ?)",
        (telegram_id, username, role)
    )
    conn.commit()
    conn.close()

def get_user_by_telegram_id(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def add_order(customer_id, platform, quantity, deadline, status="new"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (customer_id, platform, quantity, deadline, status) VALUES (?, ?, ?, ?, ?)",
        (customer_id, platform, quantity, deadline, status)
    )
    conn.commit()
    conn.close()

def get_orders_by_customer(customer_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE customer_id = ?",
        (customer_id,)
    )
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_all_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return orders

def assign_order_to_worker(order_id, worker_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET worker_id = ?, status = 'in_progress' WHERE id = ? AND status = 'new'",
        (worker_id, order_id)
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0

def get_free_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE status = 'new' AND worker_id IS NULL"
    )
    orders = cursor.fetchall()
    conn.close()
    return orders

if __name__ == "__main__":
    init_db()