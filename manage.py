#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    # Importer la connexion APRES avoir défini DJANGO_SETTINGS_MODULE
    from django.db import connection
    print("[✓] Connexion à la base PostgreSQL : ", connection.settings_dict['NAME'])

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
