from django.urls import path
from ssq import views

app_name = 'ssq'
urlpatterns = [
    path('', views.ssq_list, name='ssq_list'),
    path('create/', views.ssq_create, name='ssq_create'),
    path('update/<int:pk>/', views.ssq_update, name='ssq_update'),
    path('delete/<int:pk>/', views.ssq_delete, name='ssq_delete'),
    path('detail/<int:pk>/', views.ssq_detail, name='ssq_detail'),
]