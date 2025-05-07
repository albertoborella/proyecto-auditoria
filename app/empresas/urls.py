from django.urls import path
from .views import home_empresa

urlpatterns = [
    path('', home_empresa, name='home' ),
    
]