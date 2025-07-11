# Generated by Django 5.2.3 on 2025-06-23 07:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_customuser_status_pembayaran'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='status_pembayaran',
        ),
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_pembayaran', models.BooleanField(default=False)),
                ('bukti_pembayaran', models.ImageField(upload_to='bukti_pembayaran/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
