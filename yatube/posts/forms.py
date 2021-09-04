from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.strip() == '1':
            error_explanation = 'Вы должны ввести какой-нибудь умный мысль!!!'
            raise forms.ValidationError(error_explanation)
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
