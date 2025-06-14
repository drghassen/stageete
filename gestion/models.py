from django.db import models
from django.core.validators import RegexValidator


class Beneficiaire(models.Model):
    """
    Modèle représentant un bénéficiaire du projet.
    """
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=1)
    code_postal = models.CharField(max_length=10)
    email = models.EmailField()
    telephone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Aidant(models.Model):
    """
    Modèle représentant un aidant d’un bénéficiaire.
    """
    beneficiaire = models.ForeignKey(Beneficiaire, related_name='aidants', on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telephone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")]
    )
    lien_parente = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.lien_parente})"


class Experimentation(models.Model):
    """
    Modèle représentant une expérimentation liée à un bénéficiaire.
    """

    TYPE_CHOICES = [
        ('TelegrafiK', 'TelegrafiK'),
        ('Presage', 'Presage'),
    ]

    STATUT_CHOICES = [
        ('noninitie', 'Non initié'),
        ('visite', 'Visite programmée'),
        ('consentement', 'Consentement signé'),
        ('consentementTGK', 'Consentement signé (TelegrafiK)'),
        ('installation', 'Installation programmée'),
        ('actif', 'Actif'),
        ('interrompu', 'Interrompu'),
        ('fini', 'Fini'),
        ('desinstalle', 'Désinstallé'),
    ]

    METHODE_RECRUTEMENT_CHOICES = [
        ('evenement', 'Événement'),
        ('partenaire', 'Partenaire'),
        ('usager', 'Usager pro'),
    ]

    beneficiaire = models.ForeignKey(Beneficiaire, related_name='experimentations', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    coordinateur = models.CharField(max_length=100)
    cohorte = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    adresse_domicile = models.TextField(blank=True)
    methode_recrutement = models.CharField(max_length=20, choices=METHODE_RECRUTEMENT_CHOICES, blank=True)
    detail_recrutement = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.type} - {self.get_statut_display()}"


class Fichier(models.Model):
    """
    Fichiers liés à une expérimentation (formulaires, consentements, etc.).
    """

    TYPE_CHOICES = [
        ('formulaire_ri2s', 'Formulaire RI2S'),
        ('consentement_telegrafik', 'Consentement TELEGRAFIK'),
        ('bon_installation', "Bon d'installation"),
        ('consentement_ri2s', 'Consentement RI2S'),
    ]

    experimentation = models.ForeignKey(Experimentation, related_name='fichiers', on_delete=models.CASCADE)
    fichier = models.FileField(upload_to='uploads/%Y/%m/%d/')
    type_fichier = models.CharField(max_length=50, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.get_type_fichier_display()} - {self.experimentation}"
    
    


class ContactReferent(models.Model):
    """
    Contact du référent pour une expérimentation générale.
    """
    nom = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=10)

    def __str__(self):
        return self.nom


class ExperimentationGenerale(models.Model):
    """
    Modèle principal d'expérimentation générale (non liée à un bénéficiaire spécifique).
    """
    nom = models.CharField(max_length=255)
    entreprise = models.CharField(max_length=255)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    remarques = models.TextField(blank=True)
    contact = models.OneToOneField(ContactReferent, on_delete=models.CASCADE, related_name='experimentation_generale')

    def __str__(self):
        return self.nom


class Cohorte(models.Model):
    """
    Cohortes associées à une expérimentation générale.
    """
    experimentation = models.ForeignKey(ExperimentationGenerale, on_delete=models.CASCADE, related_name='cohortes')
    nom = models.CharField(max_length=255)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.experimentation.nom})"


class ChampPersonnalise(models.Model):
    """
    Champs personnalisés pour les expérimentations générales.
    """
    TYPE_CHOIX = [
        ('text', 'Texte'),
        ('date', 'Date'),
        ('number', 'Nombre'),
        ('file', 'Fichier'),
        ('select', 'Liste déroulante'),
    ]

    experimentation = models.ForeignKey(ExperimentationGenerale, on_delete=models.CASCADE, related_name='champs_perso')
    nom_champ = models.CharField(max_length=255)
    type_champ = models.CharField(max_length=20, choices=TYPE_CHOIX)
    valeurs_possibles = models.TextField(blank=True, help_text="Séparer les valeurs par des virgules si 'select'")

    def __str__(self):
        return f"{self.nom_champ} ({self.type_champ})"