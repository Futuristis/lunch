from django.contrib import admin

# Register your models here.

from .models import Dish,Menu,MenuDish,Order,OrderItem

admin.site.register(Dish)
admin.site.register(Menu)
admin.site.register(MenuDish)
admin.site.register(Order)
admin.site.register(OrderItem)