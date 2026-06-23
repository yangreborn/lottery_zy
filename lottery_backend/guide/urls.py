from django.urls import path
from guide import views

urlpatterns = [
    path("list", views.GuideListView.as_view(), name="openapi-guide-list"),
    path("detail", views.GuideDetailView.as_view(), name="openapi-guide-detail"),
]
