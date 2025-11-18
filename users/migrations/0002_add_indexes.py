# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['email'], name='users_email_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['tutor_credits'], name='users_credits_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['last_daily_reset'], name='users_last_reset_idx'),
        ),
    ]
