from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path('photos/', views.PhotoListView.as_view(), name='photo-list'),
    path('photos/<int:pk>/', views.PhotoDetailView.as_view(), name='photo-detail'),
    path('photos/<int:pk>/result/', views.ResultView.as_view(), name='photo-result'),
]
