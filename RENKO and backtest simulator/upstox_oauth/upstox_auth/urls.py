from django.contrib import admin
from django.urls import path, include
from upstox_auth import views
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('redirect/', views.redirect, name='redirect'),
    path('readaccesstoken', views.readaccesstoken, name='readaccesstoken'),
    path('get_log', views.get_log, name='get_log'),
    path('Startalgo', views.get_started, name='get_started'),
    path('Stopalgo_s', views.get_started, name='get_started'),
    path('updatemarketwatchstrike', views.updatemarketwatchstrike, name = 'updatemarketwatchstrike'),
    path('get_stocklistmkt', views.get_stocklistmkt, name='get_stocklistmkt'),
    path('scrip_master_updation', views.scrip_master_updation, name = 'scrip_master_updation'),
    path('MarketWatch', views.MarketWatch, name='MarketWatch'),
    path('screener_only', views.screener_only, name='screener_only'),
    path('removeStock_maindatabase', views.removeStock_maindatabase, name='removeStock_maindatabase'),
    path('update_maindatabase', views.update_maindatabase, name='update_maindatabase')
]
