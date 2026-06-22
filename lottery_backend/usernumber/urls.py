from django.urls import path
from usernumber import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="user-login"),
    path("number/create", views.NumberCreateView.as_view(), name="user-number-create"),
]
