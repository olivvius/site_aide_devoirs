# myapp/models.py
from django.db import models
from django.contrib.auth.models import User

CLASS_CHOICES = [
    ('6e', '6e'),
    ('5e', '5e'),
    ('4e', '4e'),
    ('3e', '3e'),
    ('2de', '2de'),
    ('1ere', '1ere'),
    ('term', 'Terminale'),
    ('post_bac', 'Post Bac'),
    ('autre', 'Autre'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    parent_first_name = models.CharField(max_length=30, blank=True, null=True)
    parent_last_name = models.CharField(max_length=30, blank=True, null=True)
    current_class = models.CharField(max_length=20, choices=CLASS_CHOICES, blank=True, null=True)
    credits = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
class Exercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='sans titre')
    text = models.TextField()
    photo_statement = models.ImageField(upload_to='exercises/statements/',default='path/to/default/image.jpg')
    photo_answer = models.ImageField(upload_to='exercises/answers/', blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True) 
    corrected = models.BooleanField(default=False)
    text_correction = models.CharField(max_length=500, default='pas de correction texte')
    photo_correction = models.ImageField(upload_to='exercises/answers/', blank=True, null=True)
    correction_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"
    