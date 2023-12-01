from django.contrib import admin
from .models import Purchase,Wallet,UserModel

admin.site.register(UserModel)
admin.site.register(Wallet)
admin.site.register(Purchase)