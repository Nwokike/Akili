from django import forms
from .models import Course

class CourseCreationForm(forms.ModelForm):
    """
    Form for creating a new personalized Course.
    The user selects the exam type and the subject.
    """
    
    # Define a custom subject field, allowing text input
    subject = forms.CharField(
        max_length=200,
        label="Select Subject",
        help_text="e.g., Mathematics, Physics, Economics"
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