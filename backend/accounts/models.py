from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ip_address = models.CharField('最近登录IP', max_length=64, blank=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self) -> str:
        return self.username


class LoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_records')
    login_time = models.DateTimeField('登录时间', auto_now_add=True)
    ip_address = models.CharField('IP地址', max_length=64)
    success = models.BooleanField('是否成功', default=False)
    captcha_type = models.CharField('验证码类型', max_length=50)
    message = models.CharField('详情', max_length=255, blank=True)

    class Meta:
        verbose_name = '登录记录'
        verbose_name_plural = '登录记录'
        ordering = ['-login_time']

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.login_time}"
