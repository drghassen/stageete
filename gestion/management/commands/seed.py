from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from gestion.models import Beneficiaire, Aidant, Experimentation, Fichier, ExperimentationNew, Cohorte, CustomField, CustomFieldValue, CustomFieldOption
import random
from datetime import date, timedelta
import os
from django.core.files.base import ContentFile

fake = Faker('fr_FR')

class Command(BaseCommand):
    help = 'Remplit la base avec des données factices pour tous les modèles'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Optional: Clear existing data for clean seeding
        CustomFieldValue.objects.all().delete()
        CustomFieldOption.objects.all().delete()
        CustomField.objects.all().delete()
        Cohorte.objects.all().delete()
        ExperimentationNew.objects.all().delete()
        Fichier.objects.all().delete()
        Experimentation.objects.all().delete()
        Aidant.objects.all().delete()
        Beneficiaire.objects.all().delete()

        # Part 1: Seed Beneficiaire, Aidant, Experimentation, and Fichier
        for _ in range(10):  # Create 10 beneficiaries
            beneficiaire = Beneficiaire.objects.create(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=90),
                sexe=random.choice(['M', 'F']),
                code_postal=fake.postcode(),
                email=fake.email(),
                telephone=fake.msisdn()[:10]  # Ensure exactly 10 digits
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
                    lien_parente=random.choice(['Parent', 'Frère', 'Sœur', 'Conjoint'])
                )
                self.stdout.write(f'  Créé aidant : {aidant}')

            # Create 1 to 2 experimentations
            for _ in range(random.randint(1, 2)):
                type_exp = random.choice(['TelegrafiK', 'Presage'])
                statut = random.choice([choice[0] for choice in Experimentation.STATUT_CHOICES])
                date_debut = fake.date_between(start_date='-2y', end_date='today')
                date_fin = date_debut + timedelta(days=random.randint(30, 365))
                experimentation = Experimentation.objects.create(
                    beneficiaire=beneficiaire,
                    type=type_exp,
                    coordinateur=fake.name(),
                    cohorte=fake.word(),
                    statut=statut,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    adresse_domicile=fake.address(),
                    methode_recrutement=random.choice([choice[0] for choice in Experimentation.METHODE_RECRUTEMENT_CHOICES]),
                    detail_recrutement=fake.sentence(nb_words=6)
                )
                self.stdout.write(f'  Créé expérimentation de type {type_exp}')

                # Create 1 to 2 files per experimentation
                for _ in range(random.randint(1, 2)):
                    file_name = f"{fake.file_name(extension='pdf')}"
                    # Create a dummy PDF file content
                    file_content = b'%PDF-1.4\n%% Dummy PDF for testing\n'
                    fichier = Fichier.objects.create(
                        experimentation=experimentation,
                        type_fichier=random.choice([choice[0] for choice in Fichier.TYPE_CHOICES]),
                        fichier=ContentFile(file_content, name=file_name)
                    )
                    self.stdout.write(f'    Créé fichier : {file_name}')

        # Part 2: Seed ExperimentationNew, Cohorte, CustomField, CustomFieldValue, CustomFieldOption
        # Create ExperimentationNew
        exp1 = ExperimentationNew.objects.create(
            nom="Smart Home Experiment",
            entreprise="Tech Innovations",
            date_debut=date(2025, 6, 1),
            date_fin=date(2025, 12, 31),
            remarques="Testing smart home technologies for seniors.",
            contact_nom="Alice Smith",
            contact_email="alice.smith@techinnovations.com",
            contact_telephone="0123456789",
            created_at=timezone.now()
        )

        exp2 = ExperimentationNew.objects.create(
            nom="Health Monitoring Trial",
            entreprise="HealthTech Solutions",
            date_debut=date(2025, 7, 1),
            date_fin=date(2026, 3, 31),
            remarques="Pilot study for wearable health monitors.",
            contact_nom="Bob Johnson",
            contact_email="bob.johnson@healthtech.com",
            contact_telephone="0987654321",
            created_at=timezone.now()
        )

        # Create Cohorts
        Cohorte.objects.create(
            experimentation=exp1,
            nom="Cohort A",
            date_debut=date(2025, 6, 1),
            date_fin=date(2025, 9, 30)
        )
        Cohorte.objects.create(
            experimentation=exp1,
            nom="Cohort B",
            date_debut=date(2025, 10, 1),
            date_fin=date(2025, 12, 31)
        )
        Cohorte.objects.create(
            experimentation=exp2,
            nom="Cohort X",
            date_debut=date(2025, 7, 1),
            date_fin=date(2026, 3, 31)
        )

        # Create Custom Fields and Values
        # Custom Field 1: Text field for exp1
        cf1 = CustomField.objects.create(
            experimentation=exp1,
            nom="Project Notes",
            type="text"
        )
        CustomFieldValue.objects.create(
            custom_field=cf1,
            value_text="Initial setup completed."
        )

        # Custom Field 2: Select field for exp1
        cf2 = CustomField.objects.create(
            experimentation=exp1,
            nom="Deployment Status",
            type="select"
        )
        CustomFieldValue.objects.create(
            custom_field=cf2,
            value_text="In Progress"
        )
        CustomFieldOption.objects.create(custom_field=cf2, option="In Progress")
        CustomFieldOption.objects.create(custom_field=cf2, option="Completed")
        CustomFieldOption.objects.create(custom_field=cf2, option="Pending")

        # Custom Field 3: Number field for exp2
        cf3 = CustomField.objects.create(
            experimentation=exp2,
            nom="Device Count",
            type="number"
        )
        CustomFieldValue.objects.create(
            custom_field=cf3,
            value_number=50
        )

        # Custom Field 4: Date field for exp2
        cf4 = CustomField.objects.create(
            experimentation=exp2,
            nom="Last Maintenance",
            type="date"
        )
        CustomFieldValue.objects.create(
            custom_field=cf4,
            value_date=date(2025, 6, 10)
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))