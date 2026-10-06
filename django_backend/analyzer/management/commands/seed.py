from django.core.management.base import BaseCommand, CommandError

from analyzer.models import CommonPassword, User
from analyzer.models import hash_password


COMMON_PASSWORDS = [
    '123456', 'password', '123456789', '12345678', '12345',
    'qwerty', 'abc123', 'password1', '111111', '1234567',
    'iloveyou', 'admin', 'welcome', 'monkey', 'login',
    'dragon', 'master', 'letmein', 'hello', 'freedom',
    'whatever', 'trustno1', 'sunshine', 'qwerty123', '123123',
    'passw0rd', '654321', 'qazwsx', 'princess', 'football',
    'ashley', 'batman', 'superman', 'soccer', 'jordan',
    'michael', 'shadow', '1234', '000000', 'qwertyuiop',
    'p@ssw0rd', 'Pa55w0rd', 'password123', 'letmein123',
    'admin123', 'welcome123', 'qwerty12345', '1q2w3e4r',
    'q1w2e3r4t5y6u7i8o9p0', 'zaq12wsx', 'asdfgh', 'zxcvbn',
    'password1234', 'Password1', 'Passw0rd!', 'admin01',
]


class Command(BaseCommand):
    help = 'Seed admin user, demo user, and common passwords table.'

    def handle(self, *args, **options):
        import hashlib
        import os
        import secrets

        configured_admin_password = os.environ.get('PSA_ADMIN_PASSWORD')
        admin_password = configured_admin_password or secrets.token_urlsafe(6)
        demo_password = secrets.token_urlsafe(6)
        if len(admin_password) > 8:
            raise CommandError('PSA_ADMIN_PASSWORD must be no more than 8 characters.')

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults=dict(
                fullname='System Administrator',
                email='admin@localhost.local',
                password_hash=hash_password(admin_password),
                is_admin=True,
                is_active=True,
            ),
        )
        self.stdout.write(self.style.SUCCESS(
            f'admin user {"created" if created else "already exists"} (username: admin)'))
        if not created and configured_admin_password:
            admin.password_hash = hash_password(configured_admin_password)
            admin.save(update_fields=['password_hash'])
        if created or configured_admin_password:
            self.stdout.write(f'Initial admin password (save it now): {admin_password}')

        demo, created = User.objects.get_or_create(
            username='demo',
            defaults=dict(
                fullname='Demo User',
                email='demo@localhost.local',
                password_hash=hash_password(demo_password),
                is_admin=False,
                is_active=True,
            ),
        )
        self.stdout.write(self.style.SUCCESS(
            f'demo user {"created" if created else "already exists"} (username: demo)'))
        if created:
            self.stdout.write(f'Initial demo password (save it now): {demo_password}')

        count = 0
        for rank, plain in enumerate(COMMON_PASSWORDS, start=1):
            digest = hashlib.sha256(plain.encode('utf-8')).hexdigest()
            _, was_created = CommonPassword.objects.get_or_create(
                password_hash=digest,
                defaults=dict(
                    password_plaintext=plain,
                    appearance_rank=rank,
                ),
            )
            count += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f'common_passwords: {count} rows inserted '
            f'({CommonPassword.objects.count()} total)'))
