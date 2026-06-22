from django.urls import path
from lottery import views

urlpatterns = [
    path("lottery/list", views.LotteryListView.as_view(), name="openapi-lottery-list"),
    path("draw/latest", views.DrawLatestView.as_view(), name="openapi-draw-latest"),
    path("draw/history", views.DrawHistoryView.as_view(), name="openapi-draw-history"),
]
