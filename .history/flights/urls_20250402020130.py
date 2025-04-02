from django.urls import path
from . import views

urlpatterns = [
    path('liste/', views.HomeView.as_view(), name='home'),
]