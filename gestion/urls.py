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
    path('usager_pro_form/', views.usePro_Form_View, name='usePro_Form'),
    path("add-usager-pro/", views.add_usager_pro, name="add_usager_pro"),

    path('api/beneficiaire/<int:pk>/', views.BeneficiaireDetailView.as_view(), name='beneficiaire-detail'),
    path('api/beneficiaire/<int:pk>/update/', views.BeneficiaireUpdateView.as_view(), name='beneficiaire-update'),
    # New path for beneficiary details page
    path('beneficiaire/<int:pk>/', views.beneficiaire_detail_view, name='beneficiaire_detail'),
    
]