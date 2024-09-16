from django.contrib import admin
from .models import UserSession, Session, InventoryOrders

class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'whatsapp_username', 'created_at', 'updated_at')
    search_fields = ('phone_number', 'whatsapp_username')
    ordering = ('-created_at',)
    list_filter = ('created_at', 'updated_at')

class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'step', 'start_time', 'end_time', 'status')  # Include 'status' field
    search_fields = ('user__phone_number', 'step', 'status')  # Add 'status' to search fields
    ordering = ('-start_time',)
    list_filter = ('start_time', 'end_time', 'user', 'status')  # Add 'status' to list filters

class InventoryOrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'category', 'part_name', 'vehicle_make', 'vehicle_model', 'manufacturer_year', 'delivery', 'created_on')
    search_fields = ('part_name', 'vehicle_make', 'vehicle_model', 'category')
    ordering = ('-created_on',)
    list_filter = ('created_on', 'category', 'vehicle_make')

# Register the models with the admin site
admin.site.register(UserSession, UserSessionAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(InventoryOrders, InventoryOrdersAdmin)
