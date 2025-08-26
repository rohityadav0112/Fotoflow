from django import forms
from django.contrib.auth.models import User
from .models_folder.user_models import  Profile
from .models_folder.post_models import  Post, Comment

from .models_folder.chat_models import  Group

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    
    
class ProfileUpdateForm(forms.ModelForm):
    is_private = forms.BooleanField(
        required=False,
        label="Make my account private"
    )

    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'gender', 'is_private']


class PostForm(forms.ModelForm):
    media = forms.FileField(
        widget=forms.ClearableFileInput(), required=False
    )

    class Meta:
        model = Post
        fields = ["caption", "media"]
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        # exclude 'owner' and 'created_at' because they’ll be set in the view
        fields = ['name', 'description', 'is_private', 'image']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
