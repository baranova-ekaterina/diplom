from django.http import JsonResponse


def response(status, message, **kwargs):
    return JsonResponse({'status': status, 'message': message, **kwargs})


def is_auth_shop(request):
    if request.user.is_authenticated:
        if request.user.type == 'shop':
            return True
        else:
            return False
    else:
        return False


def total_sum(order):
    total_sum = 0
    order_items = order.order_items.all()
    for order_item in order_items:
        price = order_item.quantity * order_item.product_info.price
        total_sum += price
    order.total_sum = total_sum
    return order