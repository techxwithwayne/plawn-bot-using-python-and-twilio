from django.db import models
from django.utils import timezone

# models.py
from django.db import models
from django.utils import timezone

from django.db import models

class UserSession(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    whatsapp_username = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.whatsapp_username if self.whatsapp_username else 'No WhatsApp Username'}"

class Session(models.Model):
    id = models.AutoField(primary_key=True)  # Unique ID for each session
    user = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='sessions')
    step = models.CharField(max_length=15, default='0')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default='active')  # Status of the session

    def __str__(self):
        return f"Session ID {self.id} for {self.user.phone_number} started at {self.start_time}"




class InventoryOrders(models.Model):
    id = models.AutoField(primary_key=True)  # Unique ID for each inventory order
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='inventory_orders')  # Foreign key to Session
    category = models.TextField() 
    part_name = models.TextField() 
    vehicle_make = models.TextField() 
    vehicle_model = models.TextField() 
    manufacturer_year = models.TextField() 
    delivery = models.TextField() 
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.part_name} for {self.vehicle_make} {self.vehicle_model} in Session {self.session.id}"
