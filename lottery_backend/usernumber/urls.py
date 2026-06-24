from django.urls import path
from usernumber import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="user-login"),
    path("number/create", views.NumberCreateView.as_view(), name="user-number-create"),
    path("number/list", views.NumberListView.as_view(), name="user-number-list"),
    path("number/check", views.NumberCheckView.as_view(), name="user-number-check"),
    path("number/generate", views.NumberGenerateView.as_view(), name="user-number-generate"),
    path("number/group", views.NumberGroupView.as_view(), name="user-number-group"),
    path("number/<int:pk>", views.NumberDeleteView.as_view(), name="user-number-delete"),
]
