from datetime import datetime

def format_order(order):
    status_map = {
        "new": "🆕 Новый",
        "in_progress": "⏳ В работе",
        "done": "✅ Выполнен"
    }
    return (
        f"📝 <b>ID:</b> <code>{order[0]}</code>\n"
        f"📱 <b>Площадка:</b> {order[3]}\n"
        f"🔢 <b>Кол-во:</b> {order[4]}\n"
        f"⏰ <b>Дедлайн:</b> {order[5]}\n"
        f"🏷 <b>Статус:</b> {status_map.get(order[6], order[6])}\n"
        "────────────"
    )

def is_valid_date(date_str):
    """
    Проверяет, что строка соответствует формату YYYY-MM-DD.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False