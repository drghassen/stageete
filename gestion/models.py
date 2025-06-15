from django.db import models
from django.core.validators import RegexValidator


class Beneficiaire(models.Model):
    """
    Modèle représentant un bénéficiaire du projet.
    """
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=1, choices=[('M', 'Homme'), ('F', 'Femme')])
    code_postal = models.CharField(max_length=5, validators=[RegexValidator(r'^\d{5}$', message="Le code postal doit contenir exactement 5 chiffres.")])
    email = models.EmailField(blank=True)
    telephone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")]
    )
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

    SITUATION_CHOICES = [
        ('couple', 'En couple'),
        ('seul', 'Seul'),
    ]

    HEBERGEMENT_PERSONNE_CHOICES = [
        ('oui', 'Oui'),
        ('non', 'Non'),
    ]

    ANIMAL_COMPAGNIE_CHOICES = [
        ('oui', 'Oui'),
        ('non', 'Non'),
    ]

    COUCHER_LEVER_AUTONOME_CHOICES = [
        ('oui', 'Oui'),
        ('non', 'Non'),
    ]

    TYPE_LOGEMENT_CHOICES = [
        ('maison', 'Maison'),
        ('appartement', 'Appartement'),
        ('residence_senior', 'Résidence sénior'),
        ('residence_autonomie', 'Résidence autonomie'),
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
    date_visite = models.DateField(null=True, blank=True)
    heure_visite = models.TimeField(null=True, blank=True)
    membre_ri2s = models.CharField(max_length=100, blank=True)  # For RI2S member selection
    causes_interruption = models.TextField(blank=True)  # For 'interrompu' status
    motif_desinstallation = models.TextField(blank=True)  # For 'desinstalle' status
    teleassistance = models.BooleanField(default=False)  # Oui/Non for tele-assistance
    teleassistance_detail = models.CharField(max_length=200, blank=True)  # Details if Oui
    capteurs_disposition = models.JSONField(default=list, blank=True)  # List of capteurs (e.g., ["Borne d’appel", "Médaillon"])
    capteurs_installer = models.JSONField(default=list, blank=True)  # List of capteurs to install
    medecin_traitant = models.CharField(max_length=200, blank=True)
    situation = models.CharField(max_length=20, choices=SITUATION_CHOICES, blank=True)
    hebergement_personne = models.CharField(max_length=3, choices=HEBERGEMENT_PERSONNE_CHOICES, blank=True)
    animal_compagnie = models.CharField(max_length=3, choices=ANIMAL_COMPAGNIE_CHOICES, blank=True)
    animal_compagnie_detail = models.CharField(max_length=200, blank=True)
    coucher_lever_autonome = models.CharField(max_length=3, choices=COUCHER_LEVER_AUTONOME_CHOICES, blank=True)
    frequence_lever_nuit = models.CharField(max_length=100, blank=True)
    type_logement = models.CharField(max_length=20, choices=TYPE_LOGEMENT_CHOICES, blank=True)
    nombre_etages = models.PositiveIntegerField(null=True, blank=True)
    nombre_pieces_vie = models.CharField(max_length=100, blank=True)
    nombre_sorties_definitives = models.PositiveIntegerField(null=True, blank=True)
    prises_proches = models.CharField(max_length=3, choices=[('oui', 'Oui'), ('non', 'Non')], blank=True)
    application_otono_me = models.CharField(max_length=3, choices=[('oui', 'Oui'), ('non', 'Non')], blank=True)
    gir = models.CharField(max_length=50, blank=True)
    boite_clefs = models.CharField(max_length=3, choices=[('oui', 'Oui'), ('non', 'Non')], blank=True)
    boite_clefs_detail = models.CharField(max_length=200, blank=True)
    commentaire_visite = models.TextField(blank=True)

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


class ProfessionnelSante(models.Model):
    """
    Modèle représentant un professionnel de santé lié à une expérimentation.
    """
    experimentation = models.ForeignKey(Experimentation, related_name='professionnels_sante', on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    etablissement_structure = models.CharField(max_length=200)
    profession = models.CharField(max_length=100)
    telephone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Le numéro doit contenir exactement 10 chiffres.")]
    )
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.profession})"
    
    

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
    

class UsagerPro(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=10, verbose_name="Téléphone")
    email = models.EmailField(max_length=254, blank=True, verbose_name="Email professionnel")
    profession = models.CharField(
        max_length=50,
        choices=[
            ('Infirmier', 'Infirmier'),
            ('Médecin', 'Médecin'),
            ('Ergothérapeute', 'Ergothérapeute'),
            ('Autre', 'Autre'),
        ],
        verbose_name="Profession"
    )
    structure = models.CharField(max_length=200, verbose_name="Structure / Établissement")
    remarques = models.TextField(blank=True, verbose_name="Remarques")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Usager professionnel"
        verbose_name_plural = "Usagers professionnels"

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.profession}"