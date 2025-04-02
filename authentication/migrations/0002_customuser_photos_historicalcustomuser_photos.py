# Generated by Django 5.1.7 on 2025-03-30 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="photos",
            field=models.ImageField(
                blank=True, null=True, upload_to="user_photos/", verbose_name="Photo"
            ),
        ),
        migrations.AddField(
            model_name="historicalcustomuser",
            name="photos",
            field=models.TextField(
                blank=True, max_length=100, null=True, verbose_name="Photo"
            ),
        ),
    ]
