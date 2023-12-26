from django.urls import path
from backend.views import ShopUpdateView, SignUpView, LogInView, ProductListView, ProductInfoView, BasketView, \
    OrderView, ShopListView, CategoryListView, ContactView, UserView, ShopOrdersView, ShopStatusView

urlpatterns = [
    path('shop_update/', ShopUpdateView.as_view(), name='shop_update'),
    path('sign_up/', SignUpView.as_view(), name='sing_up'),
    path('login/', LogInView.as_view(), name='login'),
    path('products_info/', ProductInfoView.as_view(), name='product_info'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('orders/', OrderView.as_view(), name='orders'),
    path('shops/', ShopListView.as_view(), name='product_list'),
    path('categories/', CategoryListView.as_view(), name='product_list'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('user/', UserView.as_view(), name='user_details'),
    path('shop_orders/', ShopOrdersView.as_view(), name='shop_orders'),
    path('shop_status/', ShopStatusView.as_view(), name='shop_status'),
]