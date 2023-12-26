from django.db import models
from django.contrib.auth.models import AbstractUser

ORDER_STATUS = (
    ('basket', 'В корзине'),
    ('cancelled', 'Отменён'),
    ('new', 'Новый'),
    ('confirmed', 'Подтверждён'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
)

USER_TYPE = (
    ('customer', 'Покупатель'),
    ('shop', 'Магазин'),
)


class User(AbstractUser):
    type = models.CharField(max_length=30, verbose_name='Тип пользователя', choices=USER_TYPE, default='customer')
    middle_name = models.CharField(max_length=60, verbose_name='Отчество', blank=True)
    company = models.CharField(max_length=60, verbose_name='Компания', blank=True)
    position = models.CharField(max_length=100, verbose_name='Должность', blank=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Shop(models.Model):
    user = models.ForeignKey(User, verbose_name='Менеджер', related_name='shops', blank=True, null=True,
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=60, verbose_name='Название', null=False, blank=False)
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    status = models.BooleanField(verbose_name='Получение заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=60, verbose_name='Название', null=False, blank=False)
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=60, verbose_name='Название', null=False, blank=False)
    category = models.ForeignKey(Category, verbose_name='Категории', related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    item_id = models.PositiveIntegerField(verbose_name='Идентификатор', null=True, blank=True)
    model = models.CharField(max_length=60, verbose_name='Модель', blank=True)
    name = models.CharField(max_length=60, verbose_name='Название', blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_info', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_info', blank=True,
                             on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информация о продуктах'
        constraints = [models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info')]


class Parameter(models.Model):
    name = models.CharField(max_length=60, verbose_name='Название', null=False, blank=False)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters',
                                  blank=True, on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', blank=True,
                                     related_name='product_parameters', on_delete=models.CASCADE)
    value = models.CharField(max_length=60, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        constraints = [models.UniqueConstraint(fields=['parameter', 'product_info'], name='unique_product_parameter')]


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, verbose_name='Статус заказа', choices=ORDER_STATUS)
    contact = models.ForeignKey('Contact', verbose_name='Контакты', related_name='orders', blank=True,
                                null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('status',)

    def __str__(self):
        return self.status


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='order_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='order_items',
                                     blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='order_items', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Информация о заказе'
        verbose_name_plural = 'Информация о заказах'
        constraints = [models.UniqueConstraint(fields=['order', 'product_info'], name='unique_order_item')]


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    phone = models.CharField(max_length=11, verbose_name='Телефон', blank=True)
    country = models.CharField(max_length=60, verbose_name='Страна', blank=True)
    city = models.CharField(max_length=60, verbose_name='Город', blank=True)
    street = models.CharField(max_length=60, verbose_name='Улица', blank=True)
    building = models.CharField(max_length=10, verbose_name='Номер дома', blank=True)

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Контакты пользователей"

    def __str__(self):
        return self.phone