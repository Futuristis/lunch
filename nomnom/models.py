from django.conf import settings
from django.db import models, transaction

# Create your models here.

class Dish(models.Model):
    class DishType(models.TextChoices):
        SOUP = 'soup', 'Soup'
        MAIN_COURSE = 'main_course', 'Main course'
        DESSERT = 'dessert', 'Dessert'
        SALAD = 'salad', 'Salad'
        SIDE = 'side', 'Side dish'
        BEVERAGE = 'beverage', 'Beverage'
        
    item = models.PositiveIntegerField(
        unique = True,
        editable = False,
        verbose_name='item number',
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name = 'name',
    )
    
    description = models.TextField(
        blank=True,
        verbose_name = 'description',
    )
    
    type = models.CharField(
        max_length=20,
        choices = DishType.choices,
        verbose_name = 'dish type',
    )
    
    is_vegan = models.BooleanField(
        default=False,
        verbose_name = 'is vegan',
    )
    
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name = 'base price',
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name = 'is active',
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='dishes_created',
        verbose_name = 'created by',
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'dish'
        verbose_name_plural = 'dishes'
        
    def save(self, *args, **kwargs):
        if self.item is None:
            with transaction.atomic():
                last = (
                    Dish.objects.select_for_update()
                    .order_by('-item')
                    .first()
                )
                self.item = (last.item + 1) if last else 1000
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
class Menu(models.Model):
    date = models.DateField(
        unique=True,
        verbose_name='Date',
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Published',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='menus_created',
        verbose_name='Created by',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',  
    )
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Menu'
        verbose_name_plural = 'Menus'
        
    def __str__(self):
        return f"Menu for {self.date}"
    
class MenuDish(models.Model):
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='menu_dishes',
        verbose_name='Menu',
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        related_name="menu_dishes",
        verbose_name='Dish',
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Price',
        help_text='Day price for this dish on this menu',
    )
    
    class Meta:
        ordering = ['menu', 'dish']
        verbose_name = 'Menu dish'
        verbose_name_plural = 'Menu dishes'
        constraints = [
            models.UniqueConstraint(
                fields=['menu','dish'],
                name='unique_menu_dish',
            )
        ]
    
    def __str__(self):
        return f"{self.dish.name} on {self.menu.date}"
    
class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    ORDER_ID_START = 10000
    
    order_id = models.PositiveIntegerField(
        unique = True,
        editable = False,
        null = True,
        verbose_name = 'Order ID'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='User',
    )
    
    menu = models.ForeignKey(
        Menu,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Menu',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Status',
    )
    created_at=models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )
    updated_at=models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
    )
    
    class Meta:
        verbose_name='Order'
        verbose_name_plural='Orders'
        
    def __str__(self):
        return f'Order #{self.order_id}' if self.order_id else 'Order (unsaved)'
    
    def save(self, *args, **kwargs):
        if self.order_id is None:
            with transaction.atomic():
                super().save(*args, **kwargs)        
                self.order_id=self.ORDER_ID_START+self.pk-1
                super().save(update_fields=['order_id'])
        else:
            super().save(*args,**kwargs)
            
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name='Order',
    )
    menu_dish = models.ForeignKey(
        MenuDish,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Menu Dish',
    )
    quantity = models.PositiveBigIntegerField(
        verbose_name='Quantity',
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Price",
    )
    net_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Net Amount'
        
    )
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order items'
        
    def __str__(self):
        return f'{self.quantity} x {self.menu_dish} (Order #{self.order.order_id})'
    
    def save(self, *args, **kwargs):
        if self.price is None:
            self.price = self.menu_dish.price
        self.net_amount = self.quantity * self.price
        super().save(*args,**kwargs)