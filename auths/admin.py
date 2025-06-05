from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

class NotificationAdmin(admin.ModelAdmin):
      list_display = ["user",'message', 'is_read', "timestamp"]
      fields = ("user", "message", "")
      admin.site.register(Notification,)
