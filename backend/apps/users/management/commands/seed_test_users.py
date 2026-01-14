"""
Management command to seed test users for Playwright E2E tests.

Usage:
    python manage.py seed_test_users

Creates (or updates) three test users:
    customer@test.com  / Pass1234!  (CUSTOMER)
    barber@test.com    / Pass1234!  (BARBER)
    owner@test.com     / Pass1234!  (SHOP_OWNER)

All users are created with is_active=True and is_email_verified=True
so they can log in immediately without email verification.
"""

from django.core.management.base import BaseCommand

from apps.users.models import CustomUser


TEST_USERS = [
    {
        "email": "customer@test.com",
        "password": "Pass1234!",
        "full_name": "Test Customer",
        "role": CustomUser.Role.CUSTOMER,
    },
    {
        "email": "barber@test.com",
        "password": "Pass1234!",
        "full_name": "Test Barber",
        "role": CustomUser.Role.BARBER,
    },
    {
        "email": "owner@test.com",
        "password": "Pass1234!",
        "full_name": "Test Owner",
        "role": CustomUser.Role.SHOP_OWNER,
    },
]


class Command(BaseCommand):
    help = "Seed test users for Playwright E2E tests"

    def handle(self, *args, **options):
        for user_data in TEST_USERS:
            email = user_data["email"]
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "role": user_data["role"],
                    "is_active": True,
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password(user_data["password"])
                # Set first/last name from full_name
                parts = user_data["full_name"].split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ""
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Created: {email} ({user_data['role']})"))
            else:
                # Update password and ensure active + verified
                user.set_password(user_data["password"])
                user.is_active = True
                user.is_email_verified = True
                user.role = user_data["role"]
                user.save()
                self.stdout.write(f"  Updated: {email} ({user_data['role']})")

        self.stdout.write(self.style.SUCCESS("\nDone — 3 test users ready."))
