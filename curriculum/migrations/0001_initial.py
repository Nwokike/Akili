from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='e.g., 2024/2025', max_length=20, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'academic_sessions',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='SchoolLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='JS1, JS2, JS3, SS1, SS2, SS3', max_length=10, unique=True)),
                ('level_order', models.IntegerField(help_text='1-6 for ordering', unique=True)),
                ('level_type', models.CharField(choices=[('JUNIOR', 'Junior Secondary'), ('SENIOR', 'Senior Secondary')], max_length=10)),
                ('description', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'db_table': 'school_levels',
                'ordering': ['level_order'],
            },
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='First Term, Second Term, Third Term', max_length=20, unique=True)),
                ('order', models.IntegerField(help_text='1, 2, or 3', unique=True)),
                ('total_weeks', models.IntegerField(default=14)),
                ('instructional_weeks', models.IntegerField(default=12)),
                ('exam_weeks', models.IntegerField(default=2)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'terms',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(help_text='e.g., ENG, MTH, PHY', max_length=10, unique=True)),
                ('is_science_subject', models.BooleanField(default=False, help_text='For LaTeX/formula handling')),
                ('description', models.TextField(blank=True)),
                ('school_levels', models.ManyToManyField(related_name='subjects', to='curriculum.schoollevel')),
            ],
            options={
                'db_table': 'subjects',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.IntegerField(help_text='1-14')),
                ('week_type', models.CharField(choices=[('INSTRUCTIONAL', 'Instructional'), ('REVISION', 'Revision'), ('EXAM', 'Examination')], default='INSTRUCTIONAL', max_length=15)),
                ('title', models.CharField(blank=True, help_text='e.g., Week 1: Introduction', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='curriculum.term')),
            ],
            options={
                'db_table': 'weeks',
                'ordering': ['term', 'week_number'],
                'unique_together': {('term', 'week_number')},
            },
        ),
        migrations.CreateModel(
            name='SubjectCurriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(default='2025', max_length=50)),
                ('overview', models.TextField(blank=True, help_text='Text description of curriculum')),
                ('learning_objectives', models.JSONField(blank=True, default=list, help_text='JSON array of objectives')),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('school_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curricula', to='curriculum.schoollevel')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curricula', to='curriculum.subject')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curricula', to='curriculum.term')),
            ],
            options={
                'db_table': 'subject_curricula',
                'unique_together': {('school_level', 'subject', 'term', 'version')},
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('order', models.IntegerField(default=1, help_text='Order within the week')),
                ('description', models.TextField(blank=True)),
                ('learning_objectives', models.JSONField(blank=True, default=list)),
                ('key_concepts', models.JSONField(blank=True, default=list, help_text='JSON array of key concepts')),
                ('difficulty_level', models.CharField(choices=[('BASIC', 'Basic'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced')], default='BASIC', max_length=15)),
                ('estimated_duration_minutes', models.IntegerField(default=45)),
                ('curriculum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='curriculum.subjectcurriculum')),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='curriculum.week')),
            ],
            options={
                'db_table': 'topics',
                'ordering': ['curriculum', 'week', 'order'],
            },
        ),
        migrations.CreateModel(
            name='StudentProgramme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('academic_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_programmes', to='curriculum.academicsession')),
                ('school_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_programmes', to='curriculum.schoollevel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programmes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'student_programmes',
                'unique_together': {('user', 'academic_session', 'school_level')},
            },
        ),
        migrations.CreateModel(
            name='SubjectEnrolment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress_percentage', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_accessed', models.DateTimeField(auto_now=True)),
                ('current_term', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrolments', to='curriculum.term')),
                ('current_week', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrolments', to='curriculum.week')),
                ('programme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolments', to='curriculum.studentprogramme')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolments', to='curriculum.subject')),
            ],
            options={
                'db_table': 'subject_enrolments',
                'unique_together': {('programme', 'subject')},
            },
        ),
        migrations.CreateModel(
            name='LegacyExamMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_type', models.CharField(choices=[('JAMB', 'JAMB'), ('SSCE', 'SSCE'), ('JSS', 'JSS')], max_length=10)),
                ('subject_name', models.CharField(help_text='Original subject name from old system', max_length=200)),
                ('notes', models.TextField(blank=True, help_text='Additional mapping notes')),
                ('curriculum', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='legacy_mappings', to='curriculum.subjectcurriculum')),
                ('school_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legacy_mappings', to='curriculum.schoollevel')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legacy_mappings', to='curriculum.subject')),
            ],
            options={
                'db_table': 'legacy_exam_mappings',
                'unique_together': {('exam_type', 'subject_name')},
            },
        ),
    ]
