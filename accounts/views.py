from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, ExerciseForm, UserProfileForm, CustomAuthenticationForm, CorrectionForm, compress_image, ContactForm
from .models import Exercise, UserProfile
from django.contrib.auth.models import User
from django.db.models import Count, Q, Max
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from functools import wraps
from django.db import transaction
from django.views.decorators.http import require_POST
import uuid 
from django.core.mail import send_mail
from django.conf import settings
import base64
from django.core.files.base import ContentFile

###  PAGES UTILISATEURS ####

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registration_pending')
        else:
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = CustomUserCreationForm()
        return render(request, 'accounts/register.html', {'form': form})

def registration_pending(request):
    return render(request, 'accounts/registration_pending.html')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard(request):
    exercises = Exercise.objects.filter(user=request.user)
    return render(request, 'accounts/dashboard.html', {'exercises': exercises})

def register_success(request):
    return render(request, 'accounts/register_success.html')

def CGV(request):
    return render(request, 'accounts/CGV.html')

def welcome(request):
    return render(request, 'accounts/welcome.html')
def user_has_credits(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.credits > 0:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas assez de crédits pour accéder à cette page.")
            return redirect('dashboard')
    return _wrapped_view

@login_required
@user_has_credits
def upload_exercise(request):
    if request.method == 'POST':
        form = ExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.user = request.user
            exercise.save()
            user_profile = request.user.profile
            if user_profile.credits > 0:
                user_profile.credits -= 1
                user_profile.save()
            return render(request, 'accounts/upload_success.html', {'message': 'Exercice téléchargé!'})
    else:
        form = ExerciseForm()
    return render(request, 'accounts/upload_exercise.html', {'form': form})

@login_required
def personal_infos(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('personal_infos')
    else:
        form = UserProfileForm(instance=user_profile, user=request.user)
    return render(request, 'accounts/personal_infos.html', {'form': form})

@login_required
def exercise_detail(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id, user=request.user)
    return render(request, 'accounts/exercise_detail.html', {'exercise': exercise})

@login_required
@require_POST
def update_photos(request, exercise_id):
    exercise = get_object_or_404(Exercise, pk=exercise_id)
    if not (exercise.user == request.user or request.user.is_staff):
        return HttpResponse("Vous n'êtes pas autorisé à mettre à jour cet exercice.", status=403)

    photo_statement_uploaded = 'photo_statement' in request.FILES
    photo_answer_uploaded = 'photo_answer' in request.FILES

    try:
        if photo_statement_uploaded:
            compressed_image = compress_image(request.FILES['photo_statement'])
            exercise.photo_statement.save(f"{uuid.uuid4()}.jpg", compressed_image, save=True)
    
        if photo_answer_uploaded:
            compressed_image = compress_image(request.FILES['photo_answer'])
            exercise.photo_answer.save(f"{uuid.uuid4()}.jpg", compressed_image, save=True)

        return redirect('exercise_detail', exercise_id=exercise_id)
    except Exception as e:
        return HttpResponse(f"Erreur lors de la mise à jour des photos : {str(e)}", status=500)
    

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            send_mail(
                f'Message from {name}', 
                message, 
                email,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            return render(request, 'accounts/contact_success.html')
    else:
        form = ContactForm()

    return render(request, 'accounts/contact.html', {'form': form})

### PAGES ADMINS ###

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def admin_view(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    profiles = UserProfile.objects.select_related('user').annotate(
        exercise_count=Count('user__exercise'),
        corrected_exercise_count=Count('user__exercise', filter=Q(user__exercise__corrected=True))
    ).all()

    total_exercises = Exercise.objects.count()
    exercises_to_correct = Exercise.objects.filter(corrected='non').count()
    exercises_pending = Exercise.objects.filter(corrected='en attente de modification').count()
    exercises_corrected_today = Exercise.objects.filter(corrected=True, correction_date=today).count()
    exercises_corrected_this_week = Exercise.objects.filter(corrected=True, correction_date__gte=start_of_week).count()
    exercises_corrected_this_month = Exercise.objects.filter(corrected=True, correction_date__gte=start_of_month).count()
    corrected_exercises = Exercise.objects.filter(corrected=True).count()

    context = {
        'profiles': profiles,
        'exercises_to_correct': exercises_to_correct,
        'exercises_pending': exercises_pending,
        'exercises_corrected_today': exercises_corrected_today,
        'exercises_corrected_this_week': exercises_corrected_this_week,
        'exercises_corrected_this_month': exercises_corrected_this_month,
        'corrected_exercises': corrected_exercises,
        'total_exercises': total_exercises,
    }
    return render(request, 'accounts/admin_view.html', context)

@login_required
@user_passes_test(is_staff)
def exercises_to_correct(request):
    exercises_to_correct = Exercise.objects.filter(corrected__in=['non', 'en attente de modification'])
    return render(request, 'accounts/exercises_to_correct.html', {'exercises': exercises_to_correct})

@login_required
@user_passes_test(is_staff)
def corrected_exercises(request):
    corrected_exercises_ = Exercise.objects.filter(corrected='oui')
    return render(request, 'accounts/corrected_exercises.html', {'exercises': corrected_exercises_})

@login_required
@user_passes_test(is_staff)
def correct_exercise(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    if request.method == 'POST':
        form = CorrectionForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            form.save()
            return redirect('exercises_to_correct')
    else:
        form = CorrectionForm(instance=exercise)
    
    return render(request, 'accounts/correct_exercise.html', {'form': form, 'exercise': exercise})

@login_required
@user_passes_test(is_staff)
def user_profiles_list(request):
    profiles = UserProfile.objects.select_related('user').annotate(
        exercise_count=Count('user__exercise'),
        corrected_exercise_count=Count(
            'user__exercise', 
            filter=Q(user__exercise__corrected='oui')
        ),
        last_exercise_posted_date=Max('user__exercise__submission_date')
    ).all()

    profiles = profiles.order_by('-last_exercise_posted_date')

    return render(request, 'accounts/userprofiles_list.html', {'profiles': profiles})

@user_passes_test(is_staff)
def increment_credits(request, user_id):
    user_profile = User.objects.get(id=user_id).profile
    user_profile.credits += 1
    user_profile.save()
    return redirect('user_profiles_list')

@user_passes_test(is_staff)
def decrement_credits(request, user_id):
    user_profile = User.objects.get(id=user_id).profile
    if user_profile.credits > 0:
        user_profile.credits -= 1
    user_profile.save()
    return redirect('user_profiles_list')

@login_required
@require_POST
@user_passes_test(is_staff)
def toggle_active(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()

    return redirect('user_profiles_list')

def user_exercises(request, user_id):
    user = User.objects.get(pk=user_id)
    exercises = Exercise.objects.filter(user=user).order_by('-submission_date')
    context = {'exercises': exercises, 'user': user}
    return render(request, 'accounts/user_exercises.html', context)