from django.urls import path
from ai_models.views import features
app_name = 'ai_models'

urlpatterns = [
    #模型特征
    path('features/', features.features_list, name = 'features_list'),
    path('features/create/',features.features_create, name = 'features_create'),
    path('features/<int:pk>/', features.features_detail, name = 'features_detail'),
    path('features/delete/<int:pk>/', features.features_delete, name = 'features_delete'),
]