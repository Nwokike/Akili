from django import forms
from .models import Course
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus

class CourseCreationForm(forms.ModelForm):
    """
    Form for creating a new personalized Course.
    The user selects the exam type and the subject.
    """
    
    # Define a custom subject field as ChoiceField
    subject = forms.ChoiceField(
        choices=[('', 'Select an exam type first')],
        label="Select Subject",
        help_text="Only subjects with available syllabuses are shown",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Course
        # We only need the user to input exam_type and subject
        fields = ['exam_type', 'subject']
        
        # Define the widgets to make the form look cleaner
        widgets = {
            # Use a Select widget for the exam_type choices defined in the Course model
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
        }
        
        # Override the default label for exam_type
        labels = {
            'exam_type': 'Target Examination Type',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If exam_type is provided (e.g., on form errors), populate subject choices
        if 'exam_type' in self.data:
            exam_type = self.data.get('exam_type')
            self.fields['subject'].choices = self._get_subject_choices(exam_type)
        elif self.initial.get('exam_type'):
            exam_type = self.initial.get('exam_type')
            self.fields['subject'].choices = self._get_subject_choices(exam_type)
    
    def _get_subject_choices(self, exam_type):
        """Get available subjects for the given exam type"""
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
        """Validate that the selected subject has an available syllabus"""
        cleaned_data = super().clean()
        exam_type = cleaned_data.get('exam_type')
        subject = cleaned_data.get('subject')
        
        if exam_type and subject:
            # Check if syllabus exists for this exam_type and subject combination
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