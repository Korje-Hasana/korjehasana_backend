# Generated by Django 4.2.3 on 2024-10-17 15:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_remove_thana_district_delete_district_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
