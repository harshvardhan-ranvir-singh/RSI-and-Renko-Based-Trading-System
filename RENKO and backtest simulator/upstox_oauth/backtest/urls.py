from django.urls import path, include
from django.contrib import admin
from backtest import views

app_name ='backtest'
urlpatterns = [
    path('backtesting/', views.indexfunc, name='indexfunc'),
]