from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.menu_view, name='menu_view'),
    path('form/', views.form_view, name='form'),
    path('confirmation/', views.confirmation_view, name='confirmation'),
    path('save-beneficiaire/', views.save_beneficiaire, name='save_beneficiaire'),
    # Nouveaux chemins
    path('experimentation_form/', views.experimentation_form_view, name='experimentation_form'),
    path('create-experimentation/', views.create_experimentation, name='create_experimentation'),
]