# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Exercise, UserProfile, CLASS_CHOICES
from django import forms
from django.contrib.auth.forms import AuthenticationForm
import uuid
from django.utils import timezone
from PIL import Image, ImageOps
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'nom utilisateur'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'mot de passe'}))

class CustomUserCreationForm(UserCreationForm):
    parent_first_name = forms.CharField(
        max_length=30,
        required=True,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Prénom du parent'})
    )
    parent_last_name = forms.CharField(
        max_length=30,
        required=True,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Nom du parent'})
    )
    current_class = forms.ChoiceField(
        choices=CLASS_CHOICES,
        label='Classe Actuelle',
        widget=forms.Select(attrs={'placeholder': 'Choisir une classe'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un utilisateur avec cette adresse e-mail existe déjà.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = 0  # Mettez à False si user.is_active est un BooleanField
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                credits=1,
                parent_first_name=self.cleaned_data['parent_first_name'],
                parent_last_name=self.cleaned_data['parent_last_name'],
                current_class=self.cleaned_data['current_class']
            )
        return user

def compress_image(image_field):
    try:
        image = Image.open(image_field)
        image = image.convert('RGB')  # Convert any format to RGB
        output_stream = io.BytesIO()
        
        max_size = 1 * 866 * 866  # 750 KB
        
        if image_field.size > max_size:
            # Resize image proportionally
            max_dim = 866  # resize max dimension to 866px
            image.thumbnail((max_dim, max_dim), Image.LANCZOS)
            image = ImageOps.exif_transpose(image)  # Fix images with EXIF orientation
        
        # Save the (potentially resized) image to the output stream
        image.save(output_stream, format='JPEG', quality=80)
        output_stream.seek(0)
        
        return InMemoryUploadedFile(
            output_stream,
            'ImageField',
            f"{uuid.uuid4()}.jpg",
            'image/jpeg',
            output_stream.tell(),
            None
        )
    except Exception as e:
        print(f"An error occurred during image compression: {e}")
        image = Image.open(image_field)
        image = image.convert('RGB')
        output_stream = io.BytesIO()
        image.save(output_stream, format='JPEG', quality=80)
        output_stream.seek(0)
        
        return InMemoryUploadedFile(
            output_stream,
            'ImageField',
            f"{uuid.uuid4()}.jpg",
            'image/jpeg',
            output_stream.tell(),
            None
        )

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['title', 'text', 'photo_statement', 'photo_answer']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
            'photo_statement': forms.ClearableFileInput(attrs={'multiple': False}),
            'photo_answer': forms.ClearableFileInput(attrs={'multiple': False}),
        }
        labels = {
            'title':'titre de l\'exercice',
            'text':'texte d\'accompagnement',
            'photo_statement': 'Photo de l\'énoncé',
            'photo_answer': 'Photo de la réponse',
        }

    def save(self, commit=True):
        instance = super(ExerciseForm, self).save(commit=False)

        if 'photo_statement' in self.files:
            compressed_image = compress_image(self.files['photo_statement'])
            instance.photo_statement.save(f"{uuid.uuid4()}.jpg", compressed_image, save=False)

        if 'photo_answer' in self.files:
            compressed_image = compress_image(self.files['photo_answer'])
            instance.photo_answer.save(f"{uuid.uuid4()}.jpg", compressed_image, save=False)

        instance.submission_date = timezone.now()

        if commit:
            instance.save()
        return instance

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=30, required=True, label='Nom utilisateur')
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')
    parent_first_name = forms.CharField(max_length=30, required=False, label='Prénom parent')
    parent_last_name = forms.CharField(max_length=30, required=False, label='Nom parent')
    current_class = forms.ChoiceField(choices=CLASS_CHOICES, label='Classe Actuelle')

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 'parent_first_name', 'parent_last_name', 'current_class']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user_id = self.instance.user.id if self.instance and self.instance.user else None
        
        existing_user = User.objects.filter(username=username).exclude(id=user_id).first()
        if existing_user:
            raise ValidationError("Ce nom d'utilisateur existe déjà. Veuillez en choisir un autre.")
        
        return username
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.instance.user = user

    def save(self, commit=True):
        profile = super(UserProfileForm, self).save(commit=False)
        user = self.instance.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            profile.save()
            
        return profile

class CorrectionForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['text_correction', 'photo_correction', 'audio_correction', 'corrected']
        labels = {
            'text_correction': 'Texte de correction',
            'photo_correction': 'Photo de correction',
            'audio_correction': 'Correction Audio',
            'corrected': 'Corrigé'
        }
        widgets = {
            'text_correction': forms.Textarea(attrs={'rows': 4}),
            'photo_correction': forms.ClearableFileInput(attrs={'multiple': False}),
            'audio_correction': forms.FileInput(),
            'corrected': forms.Select(choices=[(False, 'non'), (True, 'oui')])
        }

    def save(self, commit=True):
        instance = super(CorrectionForm, self).save(commit=False)
        
        if 'photo_correction' in self.files:
                compressed_image = compress_image(self.files['photo_correction'])
                instance.photo_correction.save(f"{uuid.uuid4()}.jpg", compressed_image, save=False)

        if 'audio_correction' in self.files:
            extension = self.files['audio_correction'].name.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{extension}"
            instance.audio_correction.name = unique_filename

        if instance.corrected and instance.correction_date is None:
            instance.correction_date = timezone.now()

        if commit:
            instance.save()
        return instance
    
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)