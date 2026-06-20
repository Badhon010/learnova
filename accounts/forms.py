from django_ckeditor_5.widgets import CKEditor5Widget
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))

    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'website', 'github_url', 'twitter_url', 'linkedin_url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yoursite.com'}),
            'github_url': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
            'twitter_url': forms.URLInput(attrs={'placeholder': 'https://twitter.com/yourusername'}),
            'linkedin_url': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourusername'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            self.user.save()
        if commit:
            profile.save()
        return profile


class ChapterCreateForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Chapter title'}),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description of what this chapter covers...'}),
    )
    estimated_hours = forms.DecimalField(
        min_value=0, max_value=999, initial=1.0,
        help_text='Estimated hours to complete this chapter.',
    )
    order = forms.IntegerField(
        min_value=0, initial=0,
        help_text='Display order (lower = shown first).',
    )



class LessonCreateForChapterForm(forms.Form):
    """Lesson creation scoped to a specific chapter — no global chapter selector."""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Lesson title'}),
    )
    summary = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief summary of what this lesson covers...'}),
        help_text='A short one-paragraph overview shown in listings.',
    )
    content = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        help_text='Full lesson content. Use the editor toolbar for headings, code, tables, etc.',
    )
    difficulty = forms.ChoiceField(choices=[])
    video_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'}),
        help_text='Optional YouTube or Vimeo link.',
    )
    reading_time = forms.IntegerField(
        min_value=1, max_value=240, initial=5,
        help_text='Estimated reading time in minutes.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from learning.models import DIFFICULTY_CHOICES
        self.fields['difficulty'].choices = DIFFICULTY_CHOICES


class TopicEditForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Topic title'}),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'What does this topic cover? Who is the audience?'}),
    )
    icon_html = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '<i class="fa-solid fa-brain"></i>'}),
        help_text='Optional Font Awesome icon snippet. Example: <code>&lt;i class="fa-solid fa-brain"&gt;&lt;/i&gt;</code>',
    )


class LessonEditForm(forms.ModelForm):
    class Meta:
        from learning.models import Lesson
        model = Lesson
        fields = ['title', 'summary', 'content', 'difficulty', 'video_url', 'reading_time']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': CKEditor5Widget(config_name='default'),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'}),
        }
