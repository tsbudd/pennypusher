"""configuration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from server.controller import views

urlpatterns = [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls, name='admin'),

    # api calls
    # admin
    path('allUsers/', views.user_all),
    path('user/delete/', views.user_delete),

    # regular
    path('connection_test/', views.connect_stat),
    path('register/', views.user_register),
    path('user/details/', views.user_info),
    path('pusher/', views.pusher_func),
    path('pusher/new/', views.pusher_new),
    path('pusher/all/', views.pusher_all),
    path('pusher/access/new', views.pusher_access_new),
    path('pusher/access/all/', views.pusher_access_all),
    path('pusher/access/', views.pusher_access_func),
    path('budget/new/', views.budget_new),
    path('budget/', views.budget_func),
    path('budget/value/new/', views.budget_value_new),
    path('budget/value/all/', views.budget_value_all),
    path('fund/new/', views.fund_new),
    path('fund/', views.fund_func),
    path('fund/value/new/', views.fund_value_new),
    path('fund/value/all/', views.fund_value_all),
    path('income/new/', views.income_new),
    path('income/', views.income_func),
    path('expense/new/', views.expense_new),
    path('expense/', views.expense_func),
    path('paycheck/new/', views.paycheck_new),
    path('paycheck/', views.paycheck_func),
    path('profit/new/', views.profit_new),
    path('profit/all/', views.profit_all),
    path('account/new/', views.account_new),
    path('account/', views.account_func),
    path('account/value/new/', views.account_value_new),
    path('account/value/all/', views.account_value_all),
    path('net_worth/new/', views.exp_net_worth_new),
    path('net_worth/all/', views.exp_net_worth_all)
]

urlpatterns = format_suffix_patterns(urlpatterns)