from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone
from .models import Beneficiaire, Aidant, Experimentation, Fichier, ExperimentationGenerale, ContactReferent, Cohorte, ChampPersonnalise


class BeneficiaireForm(forms.ModelForm):
    telephone = forms.CharField(
        max_length=15,  # Match model max_length
        validators=[RegexValidator(r'^\+?\d{10,15}$', 'Le numéro de téléphone doit contenir entre 10 et 15 chiffres, avec un "+" optionnel pour le code pays.')],
        widget=forms.TextInput(attrs={'pattern': r'^\+?\d{10,15}$', 'id': 'id_telephone'}),
    )
    code_postal = forms.CharField(
        max_length=10,  # Match model max_length
        validators=[RegexValidator(r'^\d{5,10}$', 'Le code postal doit contenir entre 5 et 10 chiffres.')],
        widget=forms.TextInput(attrs={'pattern': r'^\d{5,10}$', 'id': 'id_code_postal'}),
    )

    class Meta:
        model = Beneficiaire
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'code_postal', 'email', 'telephone']
        widgets = {
            'nom': forms.TextInput(attrs={'id': 'id_nom'}),
            'prenom': forms.TextInput(attrs={'id': 'id_prenom'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'id': 'id_date_naissance'}),
            'sexe': forms.Select(choices=[('M', 'Masculin'), ('F', 'Féminin')], attrs={'id': 'id_sexe'}),
            'email': forms.EmailInput(attrs={'id': 'id_email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_naissance = cleaned_data.get('date_naissance')
        if date_naissance and date_naissance > timezone.now().date():
            raise forms.ValidationError("La date de naissance ne peut pas être dans le futur.")
        return cleaned_data


class AidantForm(forms.ModelForm):
    telephone = forms.CharField(
    max_length=10,
    validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")]
)

    class Meta:
        model = Aidant
        fields = ['nom', 'prenom', 'email', 'telephone', 'lien_parente']
        widgets = {
            'beneficiaire': forms.HiddenInput(),
        }


class ExperimentationForm(forms.ModelForm):
    methode_recrutement = forms.ChoiceField(
        choices=Experimentation.METHODE_RECRUTEMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'id': 'id_methode_recrutement'}),
    )
    detail_recrutement = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'id': 'id_detail_recrutement'}),
    )

    class Meta:
        model = Experimentation
        fields = [
            'type',
            'coordinateur',
            'cohorte',
            'statut',
            'date_debut',
            'date_fin',
            'adresse_domicile',
            'methode_recrutement',
            'detail_recrutement',
        ]
        widgets = {
            'beneficiaire': forms.HiddenInput(),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'id': 'id_date_debut'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'id': 'id_date_fin'}),
            'type': forms.Select(attrs={'id': 'id_type'}),
            'statut': forms.Select(attrs={'id': 'id_statut'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        statut = cleaned_data.get('statut')
        experiment_type = cleaned_data.get('type')
        methode_recrutement = cleaned_data.get('methode_recrutement')
        detail_recrutement = cleaned_data.get('detail_recrutement')

        # Validate date range
        if date_debut and date_fin and date_fin < date_debut:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")

        # Validate recruitment details
        if methode_recrutement and not detail_recrutement:
            raise forms.ValidationError(
                "Veuillez fournir des détails sur la méthode de recrutement."
            )

        # Status transition validation
        ordre_telegrafik = [
            "noninitie",
            "visite",
            "consentementTGK",
            "installation",
            "actif",
            "interrompu",
            "fini",
            "desinstalle",
        ]
        ordre_presage = ["noninitie", "visite", "consentement", "actif", "interrompu", "fini"]
        ordre = ordre_telegrafik if experiment_type == "TelegrafiK" else ordre_presage

        if self.instance.pk and statut:
            current_statut = self.instance.statut
            if current_statut in ordre:
                index_current = ordre.index(current_statut)
                index_new = ordre.index(statut)
                if index_new > index_current + 1:
                    raise forms.ValidationError(
                        f"Le statut doit suivre l'ordre : passer par '{ordre[index_current + 1]}' avant '{statut}'."
                    )

        return cleaned_data


class FichierForm(forms.ModelForm):
    class Meta:
        model = Fichier
        fields = ['fichier', 'type_fichier']
        widgets = {
            'type_fichier': forms.Select(attrs={'id': 'id_type_fichier'}),
            'experimentation': forms.HiddenInput(),
        }

    def clean_fichier(self):
        fichier = self.cleaned_data['fichier']
        max_size = 5 * 1024 * 1024  # 5 MB
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']

        if fichier.size > max_size:
            raise forms.ValidationError("Le fichier ne doit pas dépasser 5 Mo.")
        if fichier.content_type not in allowed_types:
            raise forms.ValidationError("Seuls les fichiers PDF, JPG et PNG sont autorisés.")
        return fichier


AidantFormSet = forms.inlineformset_factory(
    Beneficiaire,
    Aidant,
    form=AidantForm,
    extra=1,  # Allow adding one new aidant by default
    can_delete=True,
)

ExperimentationFormSet = forms.inlineformset_factory(
    Beneficiaire,
    Experimentation,
    form=ExperimentationForm,
    extra=1,  # Allow adding one new experimentation by default
    can_delete=True,
)

class ExperimentationGeneraleForm(forms.ModelForm):
    telephone_contact = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")],
        widget=forms.TextInput(attrs={'id': 'id_telephone_contact'}),
        label="Téléphone du contact"
    )
    
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_date_debut'}),
        label="Date de début"
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_date_fin'}),
        label="Date de fin (optionnelle)"
    )

    class Meta:
        model = ExperimentationGenerale
        fields = ['nom', 'entreprise', 'date_debut', 'date_fin', 'remarques']
        widgets = {
            'nom': forms.TextInput(attrs={'id': 'id_nom'}),
            'entreprise': forms.TextInput(attrs={'id': 'id_entreprise'}),
            'remarques': forms.Textarea(attrs={'rows': 3, 'id': 'id_remarques'}),
        }
        labels = {
            'nom': "Nom de l'expérimentation",
            'entreprise': "Entreprise partenaire",
            'remarques': "Remarques",
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_fin < date_debut:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")

        return cleaned_data


class ContactReferentForm(forms.ModelForm):
    telephone = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")],
        widget=forms.TextInput(attrs={'id': 'id_telephone'}),
    )

    class Meta:
        model = ContactReferent
        fields = ['nom', 'email', 'telephone']
        widgets = {
            'nom': forms.TextInput(attrs={'id': 'id_nom_contact'}),
            'email': forms.EmailInput(attrs={'id': 'id_email_contact'}),
        }
        labels = {
            'nom': "Nom du contact référent",
            'email': "Email du contact",
            'telephone': "Téléphone du contact",
        }


class CohorteForm(forms.ModelForm):
    class Meta:
        model = Cohorte
        fields = ['nom', 'date_debut', 'date_fin']
        widgets = {
            'experimentation': forms.HiddenInput(),
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_fin < date_debut:
            raise forms.ValidationError("La date de fin de la cohorte doit être postérieure à la date de début.")
        return cleaned_data


class ChampPersonnaliseForm(forms.ModelForm):
    class Meta:
        model = ChampPersonnalise
        fields = ['nom_champ', 'type_champ', 'valeurs_possibles']
        widgets = {
            'experimentation': forms.HiddenInput(),
            'valeurs_possibles': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'nom_champ': "Nom du champ",
            'type_champ': "Type de champ",
            'valeurs_possibles': "Valeurs possibles (séparées par des virgules)",
        }


CohorteFormSet = forms.inlineformset_factory(
    ExperimentationGenerale,
    Cohorte,
    form=CohorteForm,
    extra=1,
    can_delete=True,
)


ChampPersonnaliseFormSet = forms.inlineformset_factory(
    ExperimentationGenerale,
    ChampPersonnalise,
    form=ChampPersonnaliseForm,
    extra=1,
    can_delete=True,
)