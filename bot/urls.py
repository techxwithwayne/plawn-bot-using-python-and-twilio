from . import views
from django.urls import path

from .views import bot

urlpatterns = [
    path('', views.bot)
]