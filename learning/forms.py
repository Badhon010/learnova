from django import forms
from .models import TopicProposal


class TopicProposalForm(forms.ModelForm):
    class Meta:
        model = TopicProposal
        fields = ['title', 'description', 'icon_html']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Machine Learning with Python',
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': (
                    'Describe what this topic should cover. Who is the target audience? '
                    'What will learners be able to do after completing it?'
                ),
            }),
            'icon_html': forms.TextInput(attrs={
                'placeholder': '<i class="fa-solid fa-brain"></i>',
            }),
        }
        help_texts = {
            'icon_html': (
                'Optional HTML icon snippet. '
                'Example: <code>&lt;i class="fa-solid fa-brain"&gt;&lt;/i&gt;</code>'
            ),
        }
