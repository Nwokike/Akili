# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0003_migrate_exam_to_course'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='exam',
            index=models.Index(fields=['user', 'course', 'completed_at'], name='exams_user_course_idx'),
        ),
        migrations.AddIndex(
            model_name='examquestion',
            index=models.Index(fields=['exam'], name='exams_question_exam_idx'),
        ),
    ]
