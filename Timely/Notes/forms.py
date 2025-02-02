from django import forms
from .models import Notebook,Page, SharedNotebook, StickyNotes,Remainder,SubPage
from ckeditor.widgets import CKEditorWidget

class NotebookForm(forms.ModelForm):
    class Meta:
        model = Notebook
        fields = ['title', 'priority','is_password_protected','password','body']
        widgets = {
            'body': CKEditorWidget(),
        }

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'body']
        widgets = {
            'body': CKEditorWidget(),
        }

class SubPageForm(forms.ModelForm):
    class Meta:
        model = SubPage
        fields = ['title', 'body']
        widgets = {
            'body': CKEditorWidget(),
        }

class StickyNotesForm(forms.ModelForm):
    class Meta:
        model = StickyNotes
        fields = ['title', 'body']
        

class RemainderForm(forms.ModelForm):
    class Meta:
        model = Remainder
        fields = ['title', 'alert_time', 'body']
        widgets = {
            'alert_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'body': CKEditorWidget(),
        }

class SharedNotebookForm(forms.ModelForm):
    class Meta:
        model = SharedNotebook
        fields = ['can_edit','sharedTo']