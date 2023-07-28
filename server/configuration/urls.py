"""
URL configuration for configuration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from controller.control import views
from controller.control import pusher_controller
from controller.control import user_controller
from controller.control import encapsulation_controller
from controller.control import entity_controller

urlpatterns = [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls, name='admin'),

    # api calls
    # admin
    path('users/all/', user_controller.user_all),
    path('user/delete/', user_controller.user_delete),

    # user control
    path('user/register/', user_controller.user_register),
    path('user/details/', user_controller.user_info),
    path('user/modify/', user_controller.user_info),

    # pusher and pusher access
    path('pusher/all/', pusher_controller.pusher_all),
    path('pusher/new/', pusher_controller.pusher_new),
    path('pusher/', pusher_controller.pusher_func),
    path('pusher/access/new', pusher_controller.pusher_access_new),
    path('pusher/access/all/', pusher_controller.pusher_access_all),
    path('pusher/access/', pusher_controller.pusher_access_func),

    # Budgets, Funds, Accounts
    path('encapsulation/new/', encapsulation_controller.encapsulation_new),
    path('encapsulation/', encapsulation_controller.encapsulation_func),
    path('encapsulation/value/new/', encapsulation_controller.encapsulation_value_new),
    path('encapsulation/value/', encapsulation_controller.encapsulation_value_func),

    # Net Worth
    path('net_worth/', encapsulation_controller.net_worth_history),

    # Entities
    path('entity/new/', entity_controller.entity_new),
    path('entity/', entity_controller.entity_func),
]

urlpatterns = format_suffix_patterns(urlpatterns)