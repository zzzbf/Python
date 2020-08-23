app_name="account"

from django.urls import path
from . import views

urlpatterns=[
    path('',views.user_login,name='login'),
    path('logout/',views.logout_view,name='logout'),
]
