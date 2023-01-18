from django import forms
from django.forms import ModelForm
from motionlab.models import Video
from django import forms
from django.utils.safestring import mark_safe
from django.forms import ModelForm, FileInput

class VideoForm(ModelForm):
#    terms_confirmed = forms.BooleanField(label=mark_safe("I've read and accept <a href='#license'>the terms of use</a>."))
    
    class Meta:
        model = Video
        fields = ["file", "recordid"]
        widgets = {
#            'file': FileInput(attrs={'class': "dropzone"}),
        }

class ContactForm(forms.Form):
    your_email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea(attrs={'style': 'min-height: 7em;'}), required=True)

class ApplicationForm(forms.Form):
    your_name = forms.CharField(required=True)
    your_email = forms.EmailField(required=True)
    your_state = forms.CharField(required=True)
    how = forms.CharField(widget=forms.Textarea(attrs={'style': 'min-height: 7em;'}), required=True, label="How you heard about the study?")
