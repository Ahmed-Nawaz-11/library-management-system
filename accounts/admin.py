from django.contrib import admin
from .models import User, UserRefreshToken

admin.site.register(User)
admin.site.register(UserRefreshToken)
