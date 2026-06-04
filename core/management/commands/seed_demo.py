"""Seed the portal with demo LGU accounts, sensors, incidents, and a warning.

    python manage.py seed_demo            # seed only if empty
    python manage.py seed_demo --force    # wipe domain data and reseed
"""
import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from core.models import HazardImage, Incident, Reading, Sensor, Warning


DEMO_USERS = [
    ('admin', 'Admin@2024', 'Maria Santos', User.Role.ADMIN, 'Sawang'),
    ('dispatcher', 'Dispatcher@2024', 'Juan Dela Cruz', User.Role.DISPATCHER, 'Jugaban'),
    ('viewer', 'Viewer@2024', 'Ana Reyes', User.Role.VIEWER, 'Barugohay Central'),
]


def make_sample_image(label, color):
    """Generate a small labelled JPEG in memory (so the seed needs no assets)."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (640, 480), color)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), label, fill='white')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return ContentFile(buf.getvalue(), name=f'{label.lower().replace(" ", "_")}.jpg')

SENSORS = [
    ('Canomantag River Gauge', 'river_level', 'Barugohay Central', 'Sitio Riverside', 11.2950, 124.6790, 'm', 2.1, 'advisory'),
    ('Carigara Bay Tide Station', 'storm_surge', 'Baybay', 'Coastal Rd', 11.3052, 124.6838, 'm', 0.8, 'normal'),
    ('Sawang Rain Gauge', 'rainfall', 'Sawang', 'Poblacion', 11.3008, 124.6821, 'mm/hr', 14.5, 'watch'),
    ('Canlampay Creek Sensor', 'flood', 'Canlampay', 'Lower Purok', 11.2701, 124.6602, 'm', 3.4, 'warning'),
    ('Guindapunan Coastal Buoy', 'storm_surge', 'Guindapunan East', 'Shoreline', 11.3081, 124.6904, 'm', 1.2, 'advisory'),
    ('Macalpi Slope Monitor', 'landslide', 'Macalpi', 'Upland', 11.2553, 124.7048, 'deg', 3.1, 'normal'),
    ('Jugaban River Gauge', 'river_level', 'Jugaban', 'Poblacion', 11.2992, 124.6772, 'm', 2.7, 'watch'),
    ('Tinaguban Seismic Node', 'seismic', 'Tinaguban', 'Hillside', 11.2604, 124.7152, 'PGA', 0.02, 'normal'),
]

INCIDENTS = [
    ('flooding', 'Canlampay', 'Lower Purok', 'high', 'in_progress',
     'Knee-deep floodwater on access road; 12 families pre-emptively evacuated.',
     'Pedro Mabini', '+639171234567',
     'Disp. Rosa Lim', '+639170001111', 'rlim@carigara.mdrrmo.gov.ph'),
    ('landslide', 'Macalpi', 'Upland', 'medium', 'in_progress',
     'Soil slip blocking one lane of the mountain road.',
     'Lita Gomez', '+639281112233',
     'Disp. Mark Yu', '+639170002222', 'myu@carigara.mdrrmo.gov.ph'),
    ('power_outage', 'Sawang', 'Poblacion', 'low', 'reported',
     'Brownout affecting two sitios after heavy rain.',
     'Anonymous', '', '', '', ''),
    ('road_blockage', 'Jugaban', 'Poblacion', 'medium', 'resolved',
     'Fallen tree cleared by barangay response team.',
     'Brgy. Tanod J. Ramos', '+639395556677',
     'Disp. Ben Tan', '+639170003333', 'btan@carigara.mdrrmo.gov.ph'),
]


class Command(BaseCommand):
    help = 'Seed demo data for the Carigara DEWS portal.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Wipe domain data and reseed.')

    def handle(self, *args, **options):
        force = options['force']
        if User.objects.filter(is_superuser=False).exists() and not force:
            self.stdout.write(self.style.WARNING(
                'Data already present. Use --force to wipe and reseed.'))
            return

        if force:
            HazardImage.objects.all().delete()
            Reading.objects.all().delete()
            Sensor.objects.all().delete()
            Incident.objects.all().delete()
            Warning.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        now = timezone.now()

        admin_user = None
        for username, pw, full, role, muni in DEMO_USERS:
            first, _, last = full.partition(' ')
            user = User.objects.create_user(
                username=username, password=pw, first_name=first, last_name=last,
                role=role, municipality=muni,
            )
            if role == User.Role.ADMIN:
                admin_user = user
                user.is_staff = True
                user.save(update_fields=['is_staff'])

        for name, htype, muni, brgy, lat, lng, unit, val, st in SENSORS:
            sensor = Sensor.objects.create(
                device_id=f'CAR-{htype[:3].upper()}-{random.randint(1000, 9999)}',
                name=name, hazard_type=htype, municipality=muni, barangay=brgy,
                lat=lat, lng=lng, status=st,
                installed_at=now - timedelta(days=200),
            )
            for i in range(6):
                Reading.objects.create(
                    sensor=sensor,
                    value=round(val + random.uniform(-0.5, 0.5), 2),
                    unit=unit,
                    recorded_at=now - timedelta(minutes=30 * (i + 1)),
                )
            Reading.objects.create(sensor=sensor, value=val, unit=unit,
                                   recorded_at=now - timedelta(minutes=random.randint(1, 20)))

        first_incident = None
        for row in INCIDENTS:
            (itype, muni, brgy, sev, st, summary, reporter, contact,
             disp_name, disp_phone, disp_email) = row
            incident = Incident.objects.create(
                type=itype, municipality=muni, barangay=brgy, severity=sev, status=st,
                summary=summary, public_summary=summary,
                reporter_name=reporter, reporter_contact=contact,
                dispatcher_name=disp_name, dispatcher_phone=disp_phone, dispatcher_email=disp_email,
                logged_by=admin_user,
                reported_at=now - timedelta(minutes=random.randint(20, 300)),
            )
            first_incident = first_incident or incident

        for label, color in [('Flooded Road', (37, 99, 235)), ('Evacuation Site', (5, 150, 105))]:
            HazardImage.objects.create(
                incident=first_incident,
                image=make_sample_image(label, color),
                caption=label,
            )

        Warning.objects.create(
            title='Orange Rainfall Warning — Carigara',
            level='orange', hazard_type='rainfall',
            message=('Heavy rains expected within 2 hours. Residents in low-lying and '
                     'riverside barangays of Canlampay, Sawang, and Barugohay Central '
                     'should prepare to evacuate. Monitor official LGU channels.'),
            municipalities=['Canlampay', 'Sawang', 'Barugohay Central'],
            effective_from=now - timedelta(minutes=30),
            effective_until=now + timedelta(hours=3),
            issuing_office='MDRRMO Carigara', issued_by=admin_user,
        )

        call_command('setup_roles')

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
        self.stdout.write('  admin      / Admin@2024       (LGU Admin, Django admin access)')
        self.stdout.write('  dispatcher / Dispatcher@2024  (Dispatcher)')
        self.stdout.write('  viewer     / Viewer@2024      (Public Viewer)')
