"""Create or update a superuser from DJANGO_SUPERUSER_* env vars.

Idempotent and safe to run on every deploy. Does nothing unless both
DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set, so it is
a no-op in environments that don't define them.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create/update a superuser from DJANGO_SUPERUSER_* environment variables.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write('Skipping ensure_superuser: username/password env vars not set.')
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username, defaults={'email': email}
        )
        if email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        verb = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {verb}."))
