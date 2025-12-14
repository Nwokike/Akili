from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectenrolment',
            name='curriculum',
            field=models.ForeignKey(
                blank=True,
                help_text='Current curriculum the student is following',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='enrolments',
                to='curriculum.subjectcurriculum'
            ),
        ),
    ]
