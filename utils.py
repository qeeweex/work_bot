from datetime import datetime

def format_order(order):
    """
    Преобразует кортеж заказа в красивую строку для вывода пользователю.
    order: (id, customer_id, worker_id, platform, quantity, deadline, status, created_at)
    """
    return (
        f"ID: {order[0]}, "
        f"Площадка: {order[3]}, "
        f"Кол-во: {order[4]}, "
        f"Дедлайн: {order[5]}, "
        f"Статус: {order[6]}"
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