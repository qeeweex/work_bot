from datetime import datetime

def format_order(order):
    return (
        f"📝 <b>Заказ #{order[0]}</b>\n\n"
        f"<b>Площадка:</b> {order[3]}\n"
        f"<b>Кол-во:</b> {order[4]}\n"
        f"<b>Дедлайн:</b> {order[5]}\n"
        f"<b>Статус:</b> {order[6]}"
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