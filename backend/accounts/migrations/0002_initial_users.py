from django.db import migrations
from django.utils import timezone
from django.contrib.auth.hashers import make_password


def create_initial_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    if not User.objects.filter(username='test_user').exists():
        User.objects.create(
            username='test_user',
            password=make_password('TestUser123!'),
            email='user@test.com',
            is_staff=False,
            is_active=True,
            date_joined=timezone.now(),
            last_login=timezone.now(),
            ip_address='127.0.0.1',
        )
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('Admin123!'),
            email='admin@test.com',
            is_staff=True,
            is_superuser=True,
            is_active=True,
            date_joined=timezone.now(),
            last_login=timezone.now(),
            ip_address='127.0.0.1',
        )


def remove_initial_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(username__in=['test_user', 'admin']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_users, remove_initial_users),
    ]
