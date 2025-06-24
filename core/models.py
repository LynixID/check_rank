from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class RankResult(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255)
    rank = models.PositiveIntegerField()
    url_result = models.URLField()
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.domain} - {self.keyword} (Rank: {self.rank})"

class Billing(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    status_pembayaran = models.BooleanField(default=False)
    bukti_pembayaran = models.ImageField(upload_to='bukti_pembayaran/')

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return f"Billing for {self.username} - {'Lunas' if self.status_pembayaran else 'Belum Lunas'}"
