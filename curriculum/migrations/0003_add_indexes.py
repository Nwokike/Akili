from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0002_add_curriculum_fk_to_enrolment'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='subjectcurriculum',
            index=models.Index(fields=['school_level', 'subject', 'term'], name='curriculum_level_subj_term_idx'),
        ),
        migrations.AddIndex(
            model_name='topic',
            index=models.Index(fields=['curriculum', 'week'], name='curriculum_topic_curr_week_idx'),
        ),
        migrations.AddIndex(
            model_name='studentprogramme',
            index=models.Index(fields=['user', 'is_active'], name='curriculum_prog_user_active_idx'),
        ),
        migrations.AddIndex(
            model_name='subjectenrolment',
            index=models.Index(fields=['programme', 'subject'], name='curriculum_enrol_prog_subj_idx'),
        ),
        migrations.AddIndex(
            model_name='legacyexammapping',
            index=models.Index(fields=['exam_type', 'subject_name'], name='curriculum_legacy_exam_subj_idx'),
        ),
    ]
