import uuid
from datetime import datetime, timedelta

from django.db import models


class CaptchaType(models.Model):
    type_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    config_json = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '验证码类型'
        verbose_name_plural = '验证码类型'

    def __str__(self) -> str:
        return self.type_name


class CaptchaChallenge(models.Model):
    type = models.CharField(max_length=50)
    token = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    payload = models.TextField()
    answer = models.TextField()
    client_ip = models.CharField(max_length=64)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    validated = models.BooleanField(default=False)

    class Meta:
        verbose_name = '验证码挑战'
        verbose_name_plural = '验证码挑战'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['type']),
        ]

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    @classmethod
    def create(cls, type_name: str, payload: str, answer: str, client_ip: str, user_agent: str, ttl_seconds: int = 120):
        return cls.objects.create(
            type=type_name,
            payload=payload,
            answer=answer,
            client_ip=client_ip,
            user_agent=user_agent[:255],
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
        )
