from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import increment_credits, decrement_credits, toggle_active, update_photos, user_exercises, contact

urlpatterns = [
    path('register/', views.register, name='register'),
    path('CGV/', views.CGV, name='CGV'),
    path('login/', views.login_view, name='login'),
    path('register_success/', views.register_success, name='register_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.welcome, name='welcome'),
    path('upload_exercise/', views.upload_exercise, name='upload_exercise'),
    path('personal_infos/', views.personal_infos, name='personal_infos'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin_view/', views.admin_view, name='admin_view'),
    path('exercises_to_correct/', views.exercises_to_correct, name='exercises_to_correct'),
    path('corrected_exercises/', views.corrected_exercises, name='corrected_exercises'),
    path('user_profiles/', views.user_profiles_list, name='user_profiles_list'),
    path('exercise/<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
    path('exercise/<int:exercise_id>/correct/', views.correct_exercise, name='correct_exercise'),
    path('increment_credits/<int:user_id>/', views.increment_credits, name='increment_credits'),
    path('decrement_credits/<int:user_id>/', views.decrement_credits, name='decrement_credits'),
    path('registration_pending/', views.registration_pending, name='registration_pending'),
    path('user/<int:user_id>/toggle-active/', toggle_active, name='toggle_active'),
    path('update-photos/<int:exercise_id>/', update_photos, name='update_photos'),
    path('user/<int:user_id>/exercises/', user_exercises, name='user_exercises'),
    path('contact/', contact, name='contact'),


]
