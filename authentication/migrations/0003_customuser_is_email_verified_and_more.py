# Generated by Django 5.1.7 on 2025-03-30 21:10

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_customuser_photos_historicalcustomuser_photos"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicalcustomuser",
            name="is_email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="OTPCode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("code", models.CharField(max_length=6)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("register", "Registration"),
                            ("login", "Login"),
                            ("reset", "Password Reset"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_used", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otp_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
