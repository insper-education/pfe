from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('usuario/<str:pk>/', views.Usuario.as_view(), name='usuario'),
    path('show/<str:pk>/', views.show_profile, name='show'),
    path('update/', views.update_profile, name='updatep'),
]
