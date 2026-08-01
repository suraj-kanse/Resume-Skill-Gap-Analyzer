from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Resume, Job
import re


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(
        choices=[('USER', 'Candidate'), ('HR', 'HR/Recruiter')],
        widget=forms.RadioSelect,
        initial='USER'
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                raise ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password):
                raise ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'\d', password):
                raise ValidationError("Password must contain at least one digit.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("Password must contain at least one special character.")
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['resume_file']
        widgets = {
            'resume_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx'
            })
        }
    
    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file')
        if file:
            if file.size > 2 * 1024 * 1024:  # 2MB
                raise ValidationError("File size must be less than 2MB.")
            if not file.name.lower().endswith(('.pdf', '.docx')):
                raise ValidationError("Only PDF and DOCX files are allowed.")
            
            # Verify file signature
            validate_file_signature(file)
        return file


def validate_file_signature(file):
    """Check magic bytes/signatures to verify file type"""
    try:
        header = file.read(4)
        file.seek(0)  # Reset pointer
        
        # Check PDF signature
        if file.name.lower().endswith('.pdf'):
            if header != b'%PDF':
                raise ValidationError(f"Invalid PDF file signature for {file.name}. Uploaded file does not appear to be a real PDF.")
                
        # Check DOCX signature (standard zip PK signature)
        elif file.name.lower().endswith('.docx'):
            if header != b'PK\x03\x04':
                raise ValidationError(f"Invalid DOCX file signature for {file.name}. Uploaded file does not appear to be a real DOCX.")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Could not read file signature for {file.name}.")


class JobCreationForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'required_skills']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'required_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter skills separated by commas (e.g., Python, Django, MySQL, JavaScript)'
            })
        }


class BulkResumeUploadForm(forms.Form):
    resumes = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx'
        }),
        help_text='Select multiple PDF or DOCX files (max 2MB each)'
    )
    
    def clean_resumes(self):
        files = self.cleaned_data.get('resumes', [])
        if not files:
            raise ValidationError("Please select at least one file.")
        
        # Handle single file case
        if not isinstance(files, list):
            files = [files]
        
        for file in files:
            if file.size > 2 * 1024 * 1024:  # 2MB
                raise ValidationError(f"File {file.name} is too large. Maximum size is 2MB.")
            if not file.name.lower().endswith(('.pdf', '.docx')):
                raise ValidationError(f"File {file.name} is not a valid format. Only PDF and DOCX are allowed.")
            
            # Verify file signature
            validate_file_signature(file)
        
        return files


class FilterForm(forms.Form):
    min_match_score = forms.IntegerField(
        min_value=0, max_value=100, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Match Score'})
    )
    max_gap_percentage = forms.IntegerField(
        min_value=0, max_value=100, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Gap %'})
    )
    readiness_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + [
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('JOB_READY', 'Job Ready'),
            ('HIGHLY_COMPATIBLE', 'Highly Compatible'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    job = forms.ModelChoiceField(
        queryset=Job.objects.none(),
        required=False,
        empty_label="All Jobs",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['job'].queryset = Job.objects.filter(hr=user)