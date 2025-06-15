from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from gestion.models import Beneficiaire, Aidant, Experimentation, ExperimentationFile, CapteurDisposition, CapteurInstallation, ProfessionnelSante
import random
from datetime import date, timedelta
from django.core.files.base import ContentFile

fake = Faker('fr_FR')

class Command(BaseCommand):
    help = 'Remplit la base avec des données factices pour les modèles principaux'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **kwargs):
        clear_data = kwargs.get('clear', False)
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        if clear_data:
            self.stdout.write('Clearing existing data...')
            ExperimentationFile.objects.all().delete()
            CapteurDisposition.objects.all().delete()
            CapteurInstallation.objects.all().delete()
            ProfessionnelSante.objects.all().delete()
            Experimentation.objects.all().delete()
            Aidant.objects.all().delete()
            Beneficiaire.objects.all().delete()

        # Seed Beneficiaire, Aidant, Experimentation, ExperimentationFile, Capteurs, ProfessionnelSante
        for _ in range(10):  # Create 10 beneficiaries
            beneficiaire = Beneficiaire.objects.create(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                date_naissance=fake.date_of_birth(minimum_age=60, maximum_age=90),
                sexe=random.choice(['M', 'F']),
                code_postal=fake.postcode(),
                email=fake.email(),
                telephone=fake.msisdn()[:10]
            )
            self.stdout.write(f'Créé bénéficiaire : {beneficiaire}')

            # Create 1 to 3 aidants per beneficiary
            for _ in range(random.randint(1, 3)):
                aidant = Aidant.objects.create(
                    beneficiaire=beneficiaire,
                    nom=fake.last_name(),
                    prenom=fake.first_name(),
                    email=fake.email(),
                    telephone=fake.msisdn()[:10],
                    lien_parente=random.choice(['Parent', 'Frère', 'Sœur', 'Conjoint', 'Enfant'])
                )
                self.stdout.write(f'  Créé aidant : {aidant}')

            # Create 1 to 2 experimentations
            for _ in range(random.randint(1, 2)):
                type_exp = random.choice(['TelegrafiK', 'Presage'])
                statut_choices = [choice[0] for choice in Experimentation.STATUT_CHOICES]
                statut = random.choice(statut_choices)
                date_debut = fake.date_between(start_date='-2y', end_date='today')
                date_fin = date_debut + timedelta(days=random.randint(30, 365)) if random.choice([True, False]) else None
                
                experimentation = Experimentation.objects.create(
                    beneficiaire=beneficiaire,
                    type=type_exp,
                    coordinateur=fake.name(),
                    cohorte=fake.word().capitalize(),
                    statut=statut,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    adresse_domicile=fake.address(),
                    methode_recrutement=random.choice([choice[0] for choice in Experimentation.METHODE_RECRUTEMENT_CHOICES]),
                    detail_recrutement=fake.sentence(nb_words=6)
                )
                self.stdout.write(f'  Créé expérimentation de type {type_exp} avec statut {statut}')

                # Create files only if file_types is not empty
                file_types = []
                if type_exp == 'TelegrafiK' and statut in ['consentementTGK', 'installation', 'actif', 'interrompu', 'fini', 'desinstalle']:
                    file_types = ['formulaire_ri2s', 'consentement_telegrafik', 'bon_installation']
                elif type_exp == 'Presage' and statut in ['consentement', 'actif', 'fini', 'interrompu']:
                    file_types = ['consentement_ri2s']

                if file_types:
                    for file_type in random.sample(file_types, k=random.randint(1, len(file_types))):
                        file_name = f"{fake.file_name(extension='pdf')}"
                        file_content = b'%PDF-1.4\n%% Dummy PDF for testing\n'
                        ExperimentationFile.objects.create(
                            experimentation=experimentation,
                            file_type=file_type,
                            file=ContentFile(file_content, name=file_name)
                        )
                        self.stdout.write(f'    Créé fichier : {file_name} ({file_type})')

                # Create capteurs for TelegrafiK
                if type_exp == 'TelegrafiK':
                    capteur_types = [choice[0] for choice in CapteurDisposition.CAPTEUR_TYPE_CHOICES]
                    for capteur_type in random.sample(capteur_types, k=random.randint(1, len(capteur_types))):
                        CapteurDisposition.objects.create(
                            experimentation=experimentation,
                            type=capteur_type,
                            is_installed=False
                        )
                        self.stdout.write(f'    Créé capteur disposition : {capteur_type}')

                    for capteur_type in random.sample(capteur_types, k=random.randint(1, len(capteur_types))):
                        CapteurInstallation.objects.create(
                            experimentation=experimentation,
                            type=capteur_type,
                            is_installed=True
                        )
                        self.stdout.write(f'    Créé capteur installation : {capteur_type}')

                # Create professionnels de santé for TelegrafiK
                if type_exp == 'TelegrafiK':
                    for _ in range(random.randint(1, 3)):
                        ProfessionnelSante.objects.create(
                            experimentation=experimentation,
                            nom=fake.last_name(),
                            prenom=fake.first_name(),
                            etablissement=fake.company(),
                            profession=random.choice(['Médecin', 'Infirmier', 'Aide-soignant']),
                            telephone=fake.msisdn()[:10],
                            email=fake.email()
                        )
                        self.stdout.write(f'    Créé professionnel de santé')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))