# user_api/urls.py
# ZËVENDËSO — shton moderator-login/ dhe me/ endpoints

from django.urls import path
from .views import (
    registration_view,
    login_view,
    logout_view,
    change_password_view,
    moderator_login_view,
    me_view,
)

urlpatterns = [
    path('register/',          registration_view,       name='register'),
    path('login/',             login_view,              name='login'),
    path('moderator-login/',   moderator_login_view,    name='moderator-login'),
    path('me/',                me_view,                 name='me'),
    path('logout/',            logout_view,             name='logout'),
    path('change-password/',   change_password_view,    name='change-password'),
]