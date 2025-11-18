# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0004_alter_quizattempt_options_quizattempt_created_at_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(fields=['user', 'module', 'completed_at'], name='quizzes_user_module_idx'),
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(fields=['user', 'passed'], name='quizzes_user_passed_idx'),
        ),
    ]
