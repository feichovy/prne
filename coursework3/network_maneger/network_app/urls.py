from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # 首页视图
    path('config/', views.config_device, name='config_device'),  # 配置设备视图
]