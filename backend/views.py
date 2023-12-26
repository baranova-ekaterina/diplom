
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from django.core.exceptions import ValidationError
from django.db import IntegrityError

#import yaml
from yaml import load, Loader

from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from .handlers import response, total_sum, is_auth_shop
from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact
from .serializers import UserSerializer, ProductSerializer, ProductInfoSerializer, OrderSerializer,\
    OrderItemSerializer, ShopSerializer, CategorySerializer, ContactSerializer


class ShopUpdateView(APIView):
    def post(self, request, *args, **kwargs):
        if is_auth_shop(request):
            update_file = request.data.get('update_file')
            if update_file:
                data = load(update_file.file, Loader=Loader)
                if data:
                    if {'shop', 'categories', 'goods'}.issubset(data):
                        shop, created = Shop.objects.get_or_create(name=data['shop'])
                        for category in data['categories']:
                            if {'id', 'name'}.issubset(category):
                                category, created = Category.objects.get_or_create(
                                    id=category['id'],
                                    name=category['name']
                                )
                                category.shops.add(shop.id)
                                category.save()
                        ProductInfo.objects.filter(shop_id=shop.id).delete()
                        for good in data['goods']:
                            if {'id', 'category', 'model', 'name', 'quantity', 'price', 'price_rrc', 'parameters'} \
                                    .issubset(good):
                                product, created = Product.objects.get_or_create(
                                    name=good['name'],
                                    category_id=good['category']
                                )
                                product_info = ProductInfo.objects.create(
                                    item_id=good['id'],
                                    model=good['model'],
                                    name=good['name'],
                                    quantity=good['quantity'],
                                    price=good['price'],
                                    price_rrc=good['price_rrc'],
                                    product_id=product.id,
                                    shop_id=shop.id,
                                )
                                for name, value in good['parameters'].items():
                                    parameter, created = Parameter.objects.get_or_create(name=name)
                                    ProductParameter.objects.create(
                                        parameter_id=parameter.id,
                                        product_info_id=product_info.id,
                                        value=value,
                                    )
                        return response(True, 'data loaded successfully')
                    return response(False, 'insufficient arguments')
            return response(False, 'update file is required')
        return response(False, 'shop authentication is required')


class SignUpView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        if {'first_name', 'middle_name', 'last_name', 'username', 'email', 'password', 'company', 'position'} \
                .issubset(data):
            try:
                validate_password(data['password'])
            except ValidationError as error:
                return response(False, str(error))
            else:
                user_serializer = UserSerializer(data=data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(data['password'])
                    user.save()
                    # send confirmation email???
                    return response(True, 'user registered successfully')
                else:
                    return response(False, user_serializer.errors)
        return response(False, 'insufficient arguments')


class LogInView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        if {'username', 'password'}.issubset(data):
            user = authenticate(request, username=data['username'], password=data['password'])
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return response(True, 'login successful', token=token.key)
            return response(False, 'login failed')
        else:
            return response(False, 'insufficient arguments')


class ShopListView(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductInfoView(APIView):
    def get(self, request, *args, **kwargs):
        shop_id = request.GET.get('shop_id')
        shop = Shop.objects.filter(id=shop_id).first()
        if shop:
            category_id = request.GET.get('category_id')
            category = Category.objects.filter(id=category_id).first()
            if category:
                queryset = ProductInfo.objects.filter(shop_id=shop.id, product__category_id=category.id) \
                    .select_related('shop', 'product__category').prefetch_related('product_parameters__parameter') \
                    .distinct()
                serializer = ProductInfoSerializer(queryset, many=True)
                return Response(serializer.data)
            return response(False, 'category not found')
        return response(False, 'shop not found')


class BasketView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        order = Order.objects.filter(user_id=request.user.id, status='basket')\
            .prefetch_related(
            'order_items__product_info__product__category',
            'order_items__product_info__product_parameters__parameter'
        ).first()
        if order:
            order = total_sum(order)
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data)
        return response(False, 'orders not found')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        order_items = request.data.get('order_items')
        if order_items:
            order_items_count = 0
            order, created = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            for order_item in order_items:
                order_item.update({'order': order.id})
                order_serializer = OrderItemSerializer(data=order_item)
                if order_serializer.is_valid():
                    try:
                        order_serializer.save()
                    except IntegrityError as error:
                        return response(False, str(error))
                    else:
                        order_items_count += 1
                else:
                    return response(False, order_serializer.errors)
            return response(True, f'{order_items_count} order item(s) added successfully')
        return response(False, 'insufficient arguments')

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        delete_item_id = request.GET.get('delete_item_id')
        order = Order.objects.filter(user_id=request.user.id, status='basket').prefetch_related('order_items').first()
        if order:
            delete_item = order.order_items.filter(id=delete_item_id).first()
            if delete_item:
                delete_item.delete()
                if len(order.order_items.all()) == 1:
                    Order.objects.filter(user_id=request.user.id, id=order.id).delete()
                return response(True, 'order item deleted successfully')
            return response(False, 'order item not found')
        return response(False, 'order does not exist')

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        update_item_id = request.GET.get('update_item_id')
        data = request.data.get('update_data')
        if data:
            order = Order.objects.filter(user_id=request.user.id, status='basket').prefetch_related(
                'order_items').first()
            for update_data in data:
                OrderItem.objects.filter(order_id=order.id, id=update_item_id).update(quantity=update_data['quantity'])
            return response(True, 'order item quantity updated')
        return response(False, 'insufficient arguments')


class OrderView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        orders = Order.objects.filter(user_id=request.user.id).exclude(status='basket').prefetch_related(
            'order_items__product_info__product__category',
            'order_items__product_info__product_parameters__parameter') \
            .select_related('contact').all().distinct()
        if orders:
            orders_list = list()
            for order in orders:
                order = total_sum(order)
                orders_list.append(order)
            order_serializer = OrderSerializer(orders_list, many=True)
            return Response(order_serializer.data)
        return response(False, 'orders not found')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        data = request.data
        if {'order_id', 'contact_id'}.issubset(data):
            try:
                order = Order.objects.filter(user_id=request.user.id, id=data['order_id']) \
                    .update(contact=data['contact_id'], status='new')
            except IntegrityError as error:
                return response(False, str(error))
            else:
                if order:
                    return response(True, 'order added successfully')
                # else:
                # send confirmation email???
        return response(False, 'insufficient arguments')


class ContactView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        contact = Contact.objects.filter(user_id=request.user.id).all()
        contact_serializer = ContactSerializer(contact, many=True)
        return Response(contact_serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        data = request.data
        if {'phone', 'country', 'city', 'street', 'building'}.issubset(data):
            data._mutable = True
            data.update({'user': request.user.id})
            contact_serializer = ContactSerializer(data=data)
            if contact_serializer.is_valid():
                contact_serializer.save()
                return response(True, 'contact added successfully')
            return response(False, contact_serializer.errors)
        return response(False, 'insufficient arguments')

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        contact_id = request.GET.get('id')
        contact = Contact.objects.filter(id=contact_id).first()
        if contact:
            contact.delete()
            return response(True, 'contact deleted successfully')
        return response(False, 'contact does not exist')

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        contact_id = request.GET.get('id')
        contact = Contact.objects.filter(id=contact_id).first()
        if contact:
            contact_serializer = ContactSerializer(contact, data=request.data, partial=True)
            if contact_serializer.is_valid():
                contact_serializer.save()
                return response(True, 'contact updated successfully')
            return response(False, contact_serializer.errors)
        return response(False, 'insufficient arguments')


class UserView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        user = request.user
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return response(False, 'authentication is required', status=403)
        data = request.data
        if 'password' in data:
            try:
                validate_password(data['password'])
            except ValidationError as error:
                return response(False, str(error))
            else:
                request.user.set_password(data['password'])
                return response(True, 'password updated successfully')
        user_serializer = UserSerializer(request.user, data=data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return response(True, 'user data updated successfully')
        else:
            return response(False, user_serializer.errors)


class ShopOrdersView(APIView):
    def get(self, request, *args, **kwargs):
        if is_auth_shop(request):
            shop_id = request.GET.get('shop_id')
            shop = Shop.objects.filter(id=shop_id).first()
            if shop.user_id == request.user.id:
                orders = Order.objects.filter(order_items__product_info__shop=shop) \
                    .exclude(status='basket').prefetch_related(
                    'order_items__product_info__product__category',
                    'order_items__product_info__product_parameters__parameter') \
                    .select_related('contact').all().distinct()
                if orders:
                    orders_list = list()
                    for order in orders:
                        order = total_sum(order)
                        orders_list.append(order)
                    order_serializer = OrderSerializer(orders_list, many=True)
                    return Response(order_serializer.data)
                return response(False, 'orders not found')
            return response(False, 'you are not the manager of this shop')
        return response(False, 'shop authentication is required')


class ShopStatusView(APIView):
    def get(self, request, *args, **kwargs):
        if is_auth_shop(request):
            shops = request.user.shops
            shop_serializer = ShopSerializer(shops, many=True)
            return Response(shop_serializer.data)
        return response(False, 'shop authentication is required')

    def post(self, request, *args, **kwargs):
        if is_auth_shop(request):
            shop_id = request.GET.get('shop_id')
            shop = Shop.objects.filter(id=shop_id).first()
            status = request.data.get('status')
            if shop.user_id == request.user.id:
                if status:
                    Shop.objects.filter(id=shop.id).update(status=status)
                    return response(True, 'shop status updated successfully')
            return response(False, 'you are not the manager of this shop')
        return response(False, 'shop authentication is required')