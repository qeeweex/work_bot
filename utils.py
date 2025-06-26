from datetime import datetime

def format_order(order):
    """
    order — кортеж или словарь с полями:
    id, customer_id, platform, quantity, deadline, status
    """
    return (
        f"📝 <b>Новый заказ!</b>\n\n"
        f"<b>Площадка:</b> {order[2]}\n"
        f"<b>Кол-во:</b> {order[3]}\n"
        f"<b>Дедлайн:</b> {order[4]}\n\n"
        f"⏳ <i>Ожидает исполнителя</i>"
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