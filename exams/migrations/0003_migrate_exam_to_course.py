# Generated migration for converting Exam from module-based to course-based

from django.db import migrations, models
import django.db.models.deletion


def migrate_exam_data_forward(apps, schema_editor):
    """Migrate existing exam data from module to course"""
    Exam = apps.get_model('exams', 'Exam')
    Module = apps.get_model('courses', 'Module')
    
    for exam in Exam.objects.all():
        if exam.module_id:
            module = Module.objects.get(id=exam.module_id)
            exam.course_id = module.course_id
            exam.save()


def migrate_exam_data_reverse(apps, schema_editor):
    """Reverse migration - not fully reversible as we lose module specificity"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0002_initial'),
        ('courses', '0002_initial'),
    ]

    operations = [
        # Step 1: Add course field as nullable
        migrations.AddField(
            model_name='exam',
            name='course',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exam_attempts',
                to='courses.course'
            ),
        ),
        
        # Step 2: Migrate data from module to course
        migrations.RunPython(
            migrate_exam_data_forward,
            migrate_exam_data_reverse
        ),
        
        # Step 3: Make course field non-nullable
        migrations.AlterField(
            model_name='exam',
            name='course',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exam_attempts',
                to='courses.course'
            ),
        ),
        
        # Step 4: Remove module field
        migrations.RemoveField(
            model_name='exam',
            name='module',
        ),
    ]
