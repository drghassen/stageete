from rest_framework import serializers
from .models import Beneficiaire, Aidant, Experimentation, UsagerPro

class AidantSerializer(serializers.ModelSerializer):
      class Meta:
          model = Aidant
          fields = ['nom', 'prenom', 'email', 'telephone', 'lien_parente']

class ExperimentationSerializer(serializers.ModelSerializer):
      class Meta:
          model = Experimentation
          fields = ['type', 'cohorte', 'date_debut', 'date_fin', 'statut']

class UsagerProSerializer(serializers.ModelSerializer):
      class Meta:
          model = UsagerPro
          fields = ['nom', 'prenom', 'telephone', 'email', 'profession', 'structure']

class BeneficiaireSerializer(serializers.ModelSerializer):
      aidants = AidantSerializer(many=True, read_only=True)
      experimentations = ExperimentationSerializer(many=True, read_only=True)
      usagers_pro = UsagerProSerializer(many=True, read_only=True, source='experimentations__usagerpro_set')

      class Meta:
          model = Beneficiaire
          fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'email', 'telephone', 'aidants', 'experimentations', 'usagers_pro']