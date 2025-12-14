from django import forms
from .models import Course
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
from curriculum.models import SchoolLevel, Subject, Term, SubjectCurriculum
from core.services.curriculum import CurriculumService


class CourseCreationForm(forms.Form):
    school_level = forms.ChoiceField(
        choices=[],
        label="Class Level",
        help_text="Select your class level",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_school_level'})
    )
    
    term = forms.ChoiceField(
        choices=[],
        label="Term",
        help_text="Select the academic term",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_term'})
    )
    
    subject = forms.ChoiceField(
        choices=[('', 'Select a class level first')],
        label="Subject",
        help_text="Available subjects for your class level",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subject'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        school_levels = CurriculumService.get_school_levels()
        self.fields['school_level'].choices = [('', 'Select your class level')] + [
            (str(level.id), level.name) for level in school_levels
        ]
        
        terms = CurriculumService.get_terms()
        self.fields['term'].choices = [('', 'Select a term')] + [
            (str(term.id), term.name) for term in terms
        ]
        
        if 'school_level' in self.data:
            try:
                level_id = int(self.data.get('school_level'))
                subjects = CurriculumService.get_subjects_for_level_by_id(level_id)
                self.fields['subject'].choices = [('', 'Select a subject')] + [
                    (str(s.id), s.name) for s in subjects
                ]
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        school_level_id = cleaned_data.get('school_level')
        term_id = cleaned_data.get('term')
        subject_id = cleaned_data.get('subject')
        
        if school_level_id and term_id and subject_id:
            try:
                school_level = CurriculumService.get_school_level_by_id(int(school_level_id))
                term = CurriculumService.get_term_by_id(int(term_id))
                subject = CurriculumService.get_subject_by_id(int(subject_id))
                
                if not school_level:
                    raise forms.ValidationError("Invalid class level selected.")
                if not term:
                    raise forms.ValidationError("Invalid term selected.")
                if not subject:
                    raise forms.ValidationError("Invalid subject selected.")
                
                if not subject.school_levels.filter(id=school_level.id).exists():
                    raise forms.ValidationError(
                        f"{subject.name} is not available for {school_level.name}."
                    )
                
                curriculum = CurriculumService.get_curriculum(school_level, subject, term)
                if not curriculum:
                    raise forms.ValidationError(
                        f"No curriculum available for {subject.name} in {school_level.name} {term.name}. "
                        "Please select a different combination."
                    )
                
                cleaned_data['school_level_obj'] = school_level
                cleaned_data['term_obj'] = term
                cleaned_data['subject_obj'] = subject
                cleaned_data['curriculum_obj'] = curriculum
                
            except ValueError:
                raise forms.ValidationError("Invalid selection. Please try again.")
        
        return cleaned_data


class LegacyCourseCreationForm(forms.ModelForm):
    subject = forms.ChoiceField(
        choices=[('', 'Select an exam type first')],
        label="Select Subject",
        help_text="Only subjects with available syllabuses are shown",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Course
        fields = ['exam_type', 'subject']
        widgets = {
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'exam_type': 'Target Examination Type',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'exam_type' in self.data:
            exam_type = self.data.get('exam_type')
            self.fields['subject'].choices = self._get_subject_choices(exam_type)
        elif self.initial.get('exam_type'):
            exam_type = self.initial.get('exam_type')
            self.fields['subject'].choices = self._get_subject_choices(exam_type)
    
    def _get_subject_choices(self, exam_type):
        choices = [('', 'Select a subject')]
        
        if exam_type == 'JAMB':
            subjects = JAMBSyllabus.objects.all().values_list('subject', 'subject')
            choices.extend(subjects)
        elif exam_type == 'SSCE':
            subjects = SSCESyllabus.objects.all().values_list('subject', 'subject')
            choices.extend(subjects)
        elif exam_type == 'JSS':
            subjects = JSSSyllabus.objects.all().values_list('subject', 'subject')
            choices.extend(subjects)
        
        return choices
    
    def clean(self):
        cleaned_data = super().clean()
        exam_type = cleaned_data.get('exam_type')
        subject = cleaned_data.get('subject')
        
        if exam_type and subject:
            syllabus_exists = False
            
            if exam_type == 'JAMB':
                syllabus_exists = JAMBSyllabus.objects.filter(subject=subject).exists()
            elif exam_type == 'SSCE':
                syllabus_exists = SSCESyllabus.objects.filter(subject=subject).exists()
            elif exam_type == 'JSS':
                syllabus_exists = JSSSyllabus.objects.filter(subject=subject).exists()
            
            if not syllabus_exists:
                raise forms.ValidationError(
                    f"No syllabus available for {subject} in {exam_type}. "
                    "Please select a different subject or contact support."
                )
        
        return cleaned_data
