# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['user', 'created_at'], name='courses_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='module',
            index=models.Index(fields=['course', 'order'], name='courses_module_order_idx'),
        ),
        migrations.AddIndex(
            model_name='cachedlesson',
            index=models.Index(fields=['topic', 'syllabus_version'], name='courses_lesson_topic_idx'),
        ),
    ]
