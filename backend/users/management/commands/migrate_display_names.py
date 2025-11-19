"""
Management command to migrate existing bio values to display_name field.
"""
from django.core.management.base import BaseCommand
from users.models import UserMeta


class Command(BaseCommand):
    help = 'Migrate existing bio values to display_name field'

    def handle(self, *args, **options):
        """Migrate bio to display_name for existing records."""
        updated = 0
        for meta in UserMeta.objects.filter(bio__isnull=False).exclude(bio=''):
            if not meta.display_name:
                meta.display_name = meta.bio
                meta.save()
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {updated} records')
        )

