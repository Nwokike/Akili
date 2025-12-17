from django import forms
from .models import Course
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
