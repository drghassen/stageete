from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import quote
from .models import Beneficiaire, Aidant, ChampPersonnalise, ContactReferent, Experimentation, ExperimentationGenerale, Fichier, Cohorte, UsagerPro
from .forms import ContactReferentForm, ExperimentationGeneraleForm, CohorteForm, ChampPersonnaliseForm, UsagerProForm
from .serializers import BeneficiaireSerializer

from django.forms import inlineformset_factory
from django.views.decorators.csrf import csrf_exempt
import json

def beneficiaire_detail_view(request, pk):
    return render(request, 'beneficiaire_detail.html', {'beneficiary_id': pk})


class BeneficiaireUpdateView(APIView):
    def post(self, request, pk):
        try:
            beneficiaire = Beneficiaire.objects.get(pk=pk)
            experimentation = beneficiaire.experimentations.first()
            if 'remarques' in request.data:
                experimentation.remarques = request.data['remarques']
                experimentation.save()
            if 'fichier' in request.FILES:
                Fichier.objects.create(
                    experimentation=experimentation,
                    fichier=request.FILES['fichier'],
                    type_fichier='formulaire_ri2s'
                )
            return Response({"message": "Données enregistrées"}, status=status.HTTP_200_OK)
        except Beneficiaire.DoesNotExist:
            return Response({"error": "Bénéficiaire non trouvé"}, status=status.HTTP_404_NOT_FOUND)

def menu_view(request):
    return render(request, 'menu.html')

def form_view(request):
    return render(request, 'Formulaire_Coordinatrice.html')

def experimentation_form_view(request):
    return render(request, 'Formulaire_Expérimentation.html')

def usePro_Form_View(request):
    return render(request, 'Formulaire_Usager_Pro.html')

def confirmation_view(request):
    message = request.GET.get('message', 'Opération réussie')
    return render(request, 'confirmation.html', {'message': message})

def save_beneficiaire(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        # Print submitted data for debugging
        print("POST Data:", dict(request.POST))
        print("Files:", dict(request.FILES))

        # Validate and extract beneficiary data
        required_fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'code_postal', 'telephone']
        for field in required_fields:
            if field not in request.POST or not request.POST[field].strip():
                return JsonResponse({'success': False, 'error': f'Le champ {field} est requis'})

        if not request.POST['telephone'].isdigit() or len(request.POST['telephone']) != 10:
            return JsonResponse({'success': False, 'error': 'Numéro de téléphone du bénéficiaire invalide (10 chiffres requis)'})

        beneficiaire_data = {
            'nom': request.POST['nom'],
            'prenom': request.POST['prenom'],
            'date_naissance': request.POST['date_naissance'],
            'sexe': request.POST['sexe'],
            'code_postal': request.POST['code_postal'],
            'email': request.POST.get('email', '').strip(),
            'telephone': request.POST['telephone'],
        }
        beneficiaire = Beneficiaire.objects.create(**beneficiaire_data)

        # Process aidants
        tiers_noms = request.POST.getlist('tiers_nom[]')
        tiers_prenoms = request.POST.getlist('tiers_prenom[]')
        tiers_emails = request.POST.getlist('tiers_email[]')
        tiers_tels = request.POST.getlist('tiers_tel[]')
        tiers_liens = request.POST.getlist('tiers_lien[]')

        if tiers_noms:  # Only proceed if there are aidants
            if not (len(tiers_noms) == len(tiers_prenoms) == len(tiers_tels) == len(tiers_liens)):
                return JsonResponse({'success': False, 'error': 'Données des aidants incomplètes'})
            for i in range(len(tiers_noms)):
                if not tiers_tels[i].isdigit() or len(tiers_tels[i]) != 10:
                    return JsonResponse({'success': False, 'error': f'Numéro de téléphone invalide pour l\'aidant {i+1}'})
                Aidant.objects.create(
                    beneficiaire=beneficiaire,
                    nom=tiers_noms[i],
                    prenom=tiers_prenoms[i],
                    email=tiers_emails[i] if tiers_emails[i] else '',
                    telephone=tiers_tels[i],
                    lien_parente=tiers_liens[i]
                )

        # Process experimentations
        exp_types = request.POST.getlist('exp_type[]')
        exp_coordinateurs = request.POST.getlist('exp_coordinateur[]')
        exp_cohortes = request.POST.getlist('exp_cohorte[]')
        exp_statuts = request.POST.getlist('exp_statut[]')
        exp_date_debuts = request.POST.getlist('exp_date_debut[]')
        exp_date_fins = request.POST.getlist('exp_date_fin[]')
        exp_methode_recrutements = request.POST.getlist('exp_methode re[]')
        exp_detail_recrutements = request.POST.getlist('exp_detail_recrutement[]')

        if exp_types:  # Only proceed if there are experiments
            # Ensure all required lists have the same length
            required_exp_fields = [exp_types, exp_coordinateurs, exp_cohortes, exp_statuts]
            if not all(len(lst) == len(exp_types) for lst in required_exp_fields):
                return JsonResponse({'success': False, 'error': 'Données des expérimentations incomplètes'})

            for i in range(len(exp_types)):
                if exp_types[i]:  # Verify if the experimentation exists
                    # Handle optional date fields
                    date_debut = exp_date_debuts[i] if i < len(exp_date_debuts) and exp_date_debuts[i] else None
                    date_fin = exp_date_fins[i] if i < len(exp_date_fins) and exp_date_fins[i] else None
                    methode_recrutement = exp_methode_recrutements[i] if i < len(exp_methode_recrutements) and exp_methode_recrutements[i] else ''
                    detail_recrutement = exp_detail_recrutements[i] if i < len(exp_detail_recrutements) and exp_detail_recrutements[i] else ''

                    exp_data = {
                        'beneficiaire': beneficiaire,
                        'type': exp_types[i],
                        'coordinateur': exp_coordinateurs[i],
                        'cohorte': exp_cohortes[i],
                        'statut': exp_statuts[i],
                        'date_debut': date_debut,
                        'date_fin': date_fin,
                        'methode_recrutement': methode_recrutement,
                        'detail_recrutement': detail_recrutement,
                    }
                    experimentation = Experimentation.objects.create(**exp_data)

                    # Handle file uploads for TelegrafiK or Presage based on context
                    file_types = []
                    if exp_types[i] == 'TelegrafiK' and exp_statuts[i] in ['consentementTGK', 'installation', 'actif', 'interrompu', 'fini', 'desinstalle']:
                        file_types = ['formulaire_ri2s', 'consentement_telegrafik', 'bon_installation']
                    elif exp_types[i] == 'Presage' and exp_statuts[i] in ['consentement', 'actif', 'fini', 'interrompu']:
                        file_types = ['consentement_ri2s']

                    for file_type in file_types:
                        # Handle multiple file uploads correctly
                        if f"{file_type}_{i}" in request.FILES:
                            fichier = Fichier(
                                experimentation=experimentation,
                                type_fichier=file_type,
                                fichier=request.FILES[f"{file_type}_{i}"]
                            )
                            fichier.save()

        # Redirect to confirmation page with message as query parameter
        return redirect(f"{reverse('gestion:confirmation')}?message={quote('Données enregistrées avec succès')}")
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur lors de l\'enregistrement : {str(e)}'})

@csrf_exempt
def create_experimentation(request):
    
    if request.method == 'POST':
        try:
            # Create ContactReferent
            contact = ContactReferent.objects.create(
                nom=request.POST.get('contactNom'),
                email=request.POST.get('contactEmail'),
                telephone=request.POST.get('contactTel')
            )
            
            # Create ExperimentationGenerale
            experimentation = ExperimentationGenerale.objects.create(
                nom=request.POST.get('nom'),
                entreprise=request.POST.get('entreprise'),
                date_debut=request.POST.get('date_debut'),
                date_fin=request.POST.get('date_fin') or None,
                remarques=request.POST.get('remarques', ''),
                contact=contact
            )
            
            # Process Cohortes
            cohorte_names = request.POST.getlist('cohorte[]')
            date_debuts = request.POST.getlist('cohorte_date_debut[]')
            date_fins = request.POST.getlist('cohorte_date_fin[]')
            
            if len(cohorte_names) != len(date_debuts) or len(cohorte_names) != len(date_fins):
                return JsonResponse({'success': False, 'error': 'Données des cohortes incomplètes'}, status=400)
            
            for name, debut, fin in zip(cohorte_names, date_debuts, date_fins):
                Cohorte.objects.create(
                    experimentation=experimentation,
                    nom=name,
                    date_debut=debut,
                    date_fin=fin if fin else None
                )
            
            # Process Custom Fields
            custom_fields = json.loads(request.POST.get('custom_fields', '[]'))
            for field in custom_fields:
                if not field.get('name') or not field.get('type'):
                    continue
                ChampPersonnalise.objects.create(
                    experimentation=experimentation,
                    nom_champ=field['name'],
                    type_champ=field['type'],
                    valeurs_possibles=','.join(field.get('options', [])) if field['type'] == 'select' else ''
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Expérimentation créée avec succès',
                'redirect_url': f"{reverse('gestion:confirmation')}?message={quote('Expérimentation créée avec succès')}"
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return render(request, 'Formulaire_Expérimentation.html')

    # GET request: Render empty forms
    contact_form = ContactReferentForm()
    experimentation_form = ExperimentationGeneraleForm()
    cohorte_formset = CohorteFormSet()
    champ_formset = ChampPersonnaliseFormSet()
    return render(request, 'Formulaire_Expérimentation.html', {
        'contact_form': contact_form,
        'experimentation_form': experimentation_form,
        'cohorte_formset': cohorte_formset,
        'champ_formset': champ_formset,
    })

@csrf_exempt
@csrf_exempt
def add_usager_pro(request):
    if request.method == 'POST':
        try:
            # Exemple d'enregistrement
            usager = UsagerPro.objects.create(
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                telephone=request.POST.get('telephone'),
                email=request.POST.get('email'),
                profession=request.POST.get('profession'),
                structure=request.POST.get('structure'),
                remarques=request.POST.get('remarques', '')
            )
            return JsonResponse({
                "success": True,
                "message": "Usager professionnel ajouté avec succès.",
                "redirect_url": "/confirmation/"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": "Erreur lors de l’enregistrement.",
                "details": str(e)
            }, status=400)
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

class BeneficiaireDetailView(APIView):
    def get(self, request, pk):
        try:
            beneficiaire = Beneficiaire.objects.get(pk=pk)
            serializer = BeneficiaireSerializer(beneficiaire)
            return Response(serializer.data)
        except Beneficiaire.DoesNotExist:
            return Response({"error": "Bénéficiaire non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        