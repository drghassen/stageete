import datetime
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import quote
from .models import Beneficiaire, Aidant, ChampPersonnalise, ContactReferent, Experimentation, ExperimentationGenerale, Fichier, Cohorte, UsagerPro, ProfessionnelSante
from .forms import ContactReferentForm, ExperimentationGeneraleForm
from .serializers import BeneficiaireSerializer

from django.forms import inlineformset_factory
from django.views.decorators.csrf import csrf_exempt , csrf_protect
import json


@csrf_exempt
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


@csrf_exempt
def save_beneficiaire(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        # Debug: Log POST and FILES
        print("POST Data:", dict(request.POST))
        print("Files:", {k: v.name for k, v in request.FILES.items()})

        # Validate beneficiary data
        required_fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'code_postal', 'telephone']
        for field in required_fields:
            if field not in request.POST or not request.POST[field].strip():
                return JsonResponse({'success': False, 'error': f'Le champ {field} est requis'}, status=400)

        # Validate telephone
        if not request.POST['telephone'].isdigit() or len(request.POST['telephone']) != 10:
            return JsonResponse({'success': False, 'error': 'Numéro de téléphone du bénéficiaire invalide (10 chiffres requis)'}, status=400)

        # Validate code postal
        if not request.POST['code_postal'].isdigit() or len(request.POST['code_postal']) != 5:
            return JsonResponse({'success': False, 'error': 'Code postal invalide (5 chiffres requis)'}, status=400)

        # Validate email (if provided)
        email = request.POST.get('email', '').strip()
        if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return JsonResponse({'success': False, 'error': 'Adresse email du bénéficiaire invalide'}, status=400)

        # Validate date_naissance
        date_naissance = request.POST['date_naissance']
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_naissance):
            return JsonResponse({'success': False, 'error': 'Format de date de naissance invalide (AAAA-MM-JJ)'}, status=400)

        # Create beneficiary
        beneficiaire_data = {
            'nom': request.POST['nom'],
            'prenom': request.POST['prenom'],
            'date_naissance': date_naissance,
            'sexe': request.POST['sexe'],
            'code_postal': request.POST['code_postal'],
            'email': email,
            'telephone': request.POST['telephone'],
        }
        beneficiaire = Beneficiaire.objects.create(**beneficiaire_data)

        # Process aidants
        tiers_noms = request.POST.getlist('tiers_nom[]')
        tiers_prenoms = request.POST.getlist('tiers_prenom[]')
        tiers_emails = request.POST.getlist('tiers_email[]')
        tiers_tels = request.POST.getlist('tiers_tel[]')
        tiers_liens = request.POST.getlist('tiers_lien[]')

        if tiers_noms:
            if not (len(tiers_noms) == len(tiers_prenoms) == len(tiers_tels) == len(tiers_liens)):
                return JsonResponse({'success': False, 'error': 'Données des aidants incomplètes'}, status=400)
            for i in range(len(tiers_noms)):
                if not tiers_tels[i].isdigit() or len(tiers_tels[i]) != 10:
                    return JsonResponse({'success': False, 'error': f'Numéro de téléphone invalide pour l\'aidant {i+1}'}, status=400)
                if tiers_emails[i] and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', tiers_emails[i]):
                    return JsonResponse({'success': False, 'error': f'Adresse email invalide pour l\'aidant {i+1}'}, status=400)
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
        exp_dates_debut = request.POST.getlist('exp_date_debut[]')
        exp_dates_fin = request.POST.getlist('exp_date_fin[]')
        exp_adresses_domicile = request.POST.getlist('adresse_domicile[]')
        exp_methodes_recrutement = request.POST.getlist('exp_methode_recrutement[]')
        exp_details_recrutement = request.POST.getlist('exp_detail_recrutement[]')
        exp_dates_visite = request.POST.getlist('date_visite[]')
        exp_heures_visite = request.POST.getlist('heure_visite[]')
        exp_membres_ri2s = request.POST.getlist('membre_ri2s[]')
        exp_causes_interruption = request.POST.getlist('causes_interruption[]')
        exp_motifs_desinstallation = request.POST.getlist('motif_desinstallation[]')
        exp_teleassistances = request.POST.getlist('teleassistance[]')
        exp_teleassistance_details = request.POST.getlist('teleassistance_detail[]')
        exp_medecins_traitants = request.POST.getlist('medecin_traitant[]')
        exp_situations = request.POST.getlist('situation[]')
        exp_hebergements_personne = request.POST.getlist('hebergement_personne[]')
        exp_animals_compagnie = request.POST.getlist('animal_compagnie[]')
        exp_animals_compagnie_details = request.POST.getlist('animal_compagnie_detail[]')
        exp_coucher_lever_autonomes = request.POST.getlist('coucher_lever_autonome[]')
        exp_frequences_lever_nuit = request.POST.getlist('frequence_lever_nuit[]')
        exp_types_logement = request.POST.getlist('type_logement[]')
        exp_nombres_etages = request.POST.getlist('nombre_etages[]')
        exp_nombres_pieces_vie = request.POST.getlist('nombre_pieces_vie[]')
        exp_nombres_sorties_definitives = request.POST.getlist('nombre_sorties_definitives[]')
        exp_prises_proches = request.POST.getlist('prises_proches[]')
        exp_applications_otono_me = request.POST.getlist('application_otono_me[]')
        exp_girs = request.POST.getlist('gir[]')
        exp_boites_clefs = request.POST.getlist('boite_clefs[]')
        exp_boites_clefs_details = request.POST.getlist('boite_clefs_detail[]')
        exp_commentaires_visite = request.POST.getlist('commentaire_visite[]')

        # Process capteurs (checkboxes)
        capteurs_disposition = []
        capteurs_installer = []
        for i in range(len(exp_types)):
            capteurs_disposition.append(
                request.POST.getlist(f'capteurs_disposition_{i}[]') if f'capteurs_disposition_{i}[]' in request.POST else []
            )
            capteurs_installer.append(
                request.POST.getlist(f'capteurs_installer_{i}[]') if f'capteurs_installer_{i}[]' in request.POST else []
            )

        # Validate experimentation data
        if exp_types:
            required_exp_fields = [exp_types, exp_coordinateurs, exp_cohortes, exp_statuts, exp_methodes_recrutement]
            if not all(len(lst) == len(exp_types) for lst in required_exp_fields):
                return JsonResponse({'success': False, 'error': 'Données des expérimentations incomplètes'}, status=400)

            for i in range(len(exp_types)):
                # Validate required fields based on statut
                statut = exp_statuts[i]
                if statut in ['visite', 'installation', 'interrompu', 'fini']:
                    if i >= len(exp_dates_visite) or not exp_dates_visite[i] or i >= len(exp_heures_visite) or not exp_heures_visite[i]:
                        return JsonResponse({'success': False, 'error': f'Date et heure requises pour le statut {statut}'}, status=400)
                    if i >= len(exp_membres_ri2s) or not exp_membres_ri2s[i]:
                        return JsonResponse({'success': False, 'error': f'Membre RI2S requis pour le statut {statut}'}, status=400)
                    if i >= len(exp_adresses_domicile) or not exp_adresses_domicile[i]:
                        return JsonResponse({'success': False, 'error': f'Adresse domicile requise pour le statut {statut}'}, status=400)
                if statut == 'interrompu' and (i >= len(exp_causes_interruption) or not exp_causes_interruption[i]):
                    return JsonResponse({'success': False, 'error': 'Causes d\'interruption requises pour le statut interrompu'}, status=400)
                if statut == 'desinstalle' and (i >= len(exp_motifs_desinstallation) or not exp_motifs_desinstallation[i]):
                    return JsonResponse({'success': False, 'error': 'Motif de désinstallation requis pour le statut désinstallé'}, status=400)
                if statut in ['consentement', 'consentementTGK', 'actif', 'interrompu', 'fini', 'desinstalle'] and (
                    i >= len(exp_dates_debut) or not exp_dates_debut[i] or i >= len(exp_dates_fin) or not exp_dates_fin[i]
                ):
                    return JsonResponse({'success': False, 'error': f'Dates de début et fin requises pour le statut {statut}'}, status=400)

                # Create experimentation
                exp_data = {
                    'beneficiaire': beneficiaire,
                    'type': exp_types[i],
                    'coordinateur': exp_coordinateurs[i],
                    'cohorte': exp_cohortes[i],
                    'statut': exp_statuts[i],
                    'date_debut': exp_dates_debut[i] if i < len(exp_dates_debut) and exp_dates_debut[i] else None,
                    'date_fin': exp_dates_fin[i] if i < len(exp_dates_fin) and exp_dates_fin[i] else None,
                    'adresse_domicile': exp_adresses_domicile[i] if i < len(exp_adresses_domicile) and exp_adresses_domicile[i] else '',
                    'methode_recrutement': exp_methodes_recrutement[i],
                    'detail_recrutement': exp_details_recrutement[i] if i < len(exp_details_recrutement) else '',
                    'date_visite': exp_dates_visite[i] if i < len(exp_dates_visite) and exp_dates_visite[i] else None,
                    'heure_visite': exp_heures_visite[i] if i < len(exp_heures_visite) and exp_heures_visite[i] else None,
                    'membre_ri2s': exp_membres_ri2s[i] if i < len(exp_membres_ri2s) and exp_membres_ri2s[i] else '',
                    'causes_interruption': exp_causes_interruption[i] if i < len(exp_causes_interruption) else '',
                    'motif_desinstallation': exp_motifs_desinstallation[i] if i < len(exp_motifs_desinstallation) else '',
                    'teleassistance': exp_teleassistances[i] == 'oui' if i < len(exp_teleassistances) else False,
                    'teleassistance_detail': exp_teleassistance_details[i] if i < len(exp_teleassistance_details) else '',
                    'capteurs_disposition': capteurs_disposition[i],
                    'capteurs_installer': capteurs_installer[i],
                    'medecin_traitant': exp_medecins_traitants[i] if i < len(exp_medecins_traitants) else '',
                    'situation': exp_situations[i] if i < len(exp_situations) else '',
                    'hebergement_personne': exp_hebergements_personne[i] if i < len(exp_hebergements_personne) else '',
                    'animal_compagnie': exp_animals_compagnie[i] if i < len(exp_animals_compagnie) else '',
                    'animal_compagnie_detail': exp_animals_compagnie_details[i] if i < len(exp_animals_compagnie_details) else '',
                    'coucher_lever_autonome': exp_coucher_lever_autonomes[i] if i < len(exp_coucher_lever_autonomes) else '',
                    'frequence_lever_nuit': exp_frequences_lever_nuit[i] if i < len(exp_frequences_lever_nuit) else '',
                    'type_logement': exp_types_logement[i] if i < len(exp_types_logement) else '',
                    'nombre_etages': int(exp_nombres_etages[i]) if i < len(exp_nombres_etages) and exp_nombres_etages[i] else None,
                    'nombre_pieces_vie': exp_nombres_pieces_vie[i] if i < len(exp_nombres_pieces_vie) else '',
                    'nombre_sorties_definitives': int(exp_nombres_sorties_definitives[i]) if i < len(exp_nombres_sorties_definitives) and exp_nombres_sorties_definitives[i] else None,
                    'prises_proches': exp_prises_proches[i] if i < len(exp_prises_proches) else '',
                    'application_otono_me': exp_applications_otono_me[i] if i < len(exp_applications_otono_me) else '',
                    'gir': exp_girs[i] if i < len(exp_girs) else '',
                    'boite_clefs': exp_boites_clefs[i] if i < len(exp_boites_clefs) else '',
                    'boite_clefs_detail': exp_boites_clefs_details[i] if i < len(exp_boites_clefs_details) else '',
                    'commentaire_visite': exp_commentaires_visite[i] if i < len(exp_commentaires_visite) else '',
                }
                experimentation = Experimentation.objects.create(**exp_data)

                # Process files for this experimentation
                file_types = ['formulaire_ri2s', 'consentement_telegrafik', 'bon_installation', 'consentement_ri2s']
                for file_type in file_types:
                    file_key = f'{file_type}_{i}'
                    if file_key in request.FILES:
                        Fichier.objects.create(
                            experimentation=experimentation,
                            fichier=request.FILES[file_key],
                            type_fichier=file_type
                        )

                # Process health professionals (Réseau de santé)
                pro_sante_noms = request.POST.getlist(f'pro_sante_nom_{i}[]')
                pro_sante_prenoms = request.POST.getlist(f'pro_sante_prenom_{i}[]')
                pro_sante_etablissements = request.POST.getlist(f'pro_sante_etablissement_{i}[]')
                pro_sante_professions = request.POST.getlist(f'pro_sante_profession_{i}[]')
                pro_sante_telephones = request.POST.getlist(f'pro_sante_telephone_{i}[]')
                pro_sante_emails = request.POST.getlist(f'pro_sante_email_{i}[]')

                if pro_sante_noms:
                    if not all(len(lst) == len(pro_sante_noms) for lst in [pro_sante_prenoms, pro_sante_etablissements, pro_sante_professions, pro_sante_telephones]):
                        return JsonResponse({'success': False, 'error': f'Données des professionnels de santé incomplètes pour l\'expérimentation {i+1}'}, status=400)
                    for j in range(len(pro_sante_noms)):
                        if not pro_sante_telephones[j].isdigit() or len(pro_sante_telephones[j]) != 10:
                            return JsonResponse({'success': False, 'error': f'Numéro de téléphone invalide pour le professionnel de santé {j+1} (expérimentation {i+1})'}, status=400)
                        if pro_sante_emails[j] and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', pro_sante_emails[j]):
                            return JsonResponse({'success': False, 'error': f'Adresse email invalide pour le professionnel de santé {j+1} (expérimentation {i+1})'}, status=400)
                        ProfessionnelSante.objects.create(
                            experimentation=experimentation,
                            nom=pro_sante_noms[j],
                            prenom=pro_sante_prenoms[j],
                            etablissement_structure=pro_sante_etablissements[j],
                            profession=pro_sante_professions[j],
                            telephone=pro_sante_telephones[j],
                            email=pro_sante_emails[j] if pro_sante_emails[j] else ''
                        )

        # Redirect to confirmation page with message
        return redirect(f"{reverse('gestion:confirmation')}?message={quote('Données enregistrées avec succès')}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erreur lors de l\'enregistrement : {str(e)}'}, status=500)


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
        
        