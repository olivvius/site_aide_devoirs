from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import UserProfile, Exercise
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages
from PIL import Image
import io

def get_image_file(name='test.jpg', ext='jpeg', size=(100, 100), color=(256, 0, 0)):
    # Créer une image factice avec PIL
    file = io.BytesIO()
    image = Image.new("RGB", size, color)
    image.save(file, ext)
    file.name = name
    file.seek(0)
    return file

class RegistrationTestCase(TestCase):
    def setUp(self):
        self.url = reverse('register')  # Assurez-vous que l'URL 'register' est définie dans vos urls.py
        User.objects.create_user(username='existinguser', email='existing@example.com', password='test1234')
        User.objects.create_user(username='existingemailuser', email='existingemail@example.com', password='test1234')

    def test_get_register_page(self):
        # Teste l'accès à la page d'inscription via une requête GET
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')  # Assurez-vous que le template est correctement nommé

    def test_successful_registration(self):
        data = {
            'username': 'newuser',
            'email': 'user@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'parent_first_name': 'Parent',
            'parent_last_name': 'Test',
            'current_class': '5e',  # Assurez-vous que cette classe existe dans votre modèle
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('registration_pending'))  # Ou toute autre URL de redirection que vous avez configurée
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)  # Vérifiez si l'utilisateur n'est pas actif par défaut comme spécifié dans votre save()

    # Ajout du test pour un nom d'utilisateur déjà existant
    def test_registration_with_existing_username(self):
        # Données avec un nom d'utilisateur qui existe déjà
        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',  # Un nouvel email pour éviter des conflits d'email
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'newcomplexpassword123',
            'password2': 'newcomplexpassword123',
            'parent_first_name': 'Parent',
            'parent_last_name': 'Test',
            'current_class': '5e',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        
        # Vérifiez si le formulaire est passé dans le contexte et a des erreurs
        if 'form' in response.context:
            form = response.context['form']
            # Vérification que le champ username a une erreur spécifique
            self.assertTrue(form.has_error('username'))
            self.assertIn('Un utilisateur avec ce nom existe déjà.', form.errors['username'])
        else:
            self.fail("Le formulaire n'est pas disponible dans le context de la réponse.")

    def test_registration_with_existing_email(self):
            # Données avec un email qui existe déjà
            data = {
                'username': 'newuser',
                'email': 'existingemail@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password1': 'newcomplexpassword123',
                'password2': 'newcomplexpassword123',
                'parent_first_name': 'Parent',
                'parent_last_name': 'Test',
                'current_class': '5e',
            }
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 200)
            
            # Vérifiez si le formulaire est passé dans le contexte et a des erreurs
            if 'form' in response.context:
                form = response.context['form']
                # Vérification que le champ email a une erreur spécifique
                self.assertTrue(form.has_error('email'))
                self.assertIn('Un utilisateur avec cette adresse e-mail existe déjà.', form.errors['email'])
            else:
                self.fail("Le formulaire n'est pas disponible dans le contexte de la réponse.")

    def test_failed_registration_due_to_invalid_data(self):
        # Test d'une soumission avec données invalides (ex: mots de passe non concordants)
        data = {
            'username': 'testuser',
            'email': 'email@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'anotherpassword',
            'parent_first_name': 'Parent',
            'parent_last_name': 'Test',
            'current_class': '5',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Les deux mots de passe ne correspondent pas.' in response.context['form'].errors['password2'])  # Exemple, adaptez selon votre validation

    def test_form_display_with_initial_values_on_GET_request(self):
        # Vérifie que le formulaire est correctement initialisé avec des valeurs par défaut vides
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIsNone(form['username'].value())
        self.assertIsNone(form['email'].value())

class LoginTestCase(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'testuser',
            'password': 'secret123'
        }
        User.objects.create_user(**self.credentials)
        print("Setup de LoginTestCase terminée.")

    def test_login_page_status_code(self):
        response = self.client.get(reverse('login'))
        print(f"Status code pour la page de login : {response.status_code}.")
        self.assertEqual(response.status_code, 200)

    def test_login_form(self):
        response = self.client.post(reverse('login'), self.credentials, follow=True)
        print(f"Utilisateur authentifié après POST ? {response.context['user'].is_authenticated}.")
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, expected_url=reverse('dashboard'), status_code=302, target_status_code=200)

    def test_login_form_with_wrong_password(self):
        wrong_credentials = {'username': 'testuser', 'password': 'wrong'}
        response = self.client.post(reverse('login'), wrong_credentials)
        print(f"Utilisateur authentifié avec mauvais mot de passe ? {response.context['user'].is_authenticated}.")
        self.assertFalse(response.context['user'].is_authenticated)
        if 'form' in response.context:
            print(f"Erreurs du formulaire avec mauvais mot de passe : {response.context['form'].errors}.")

    def test_login_form_with_invalid_user(self):
        wrong_credentials = {'username': 'nouser', 'password': 'nopass'}
        response = self.client.post(reverse('login'), wrong_credentials)
        if 'form' in response.context:
            print(f"Erreurs du formulaire avec utilisateur non existant : {response.context['form'].errors}.")
        self.assertTrue('form' in response.context)  # Assurez-vous que le formulaire est bien passé dans le contexte.

class DashboardTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = UserProfile.objects.create(user=self.user, credits=5)
        Exercise.objects.create(user=self.user, title='Math Exercise', text='A simple math problem', submission_date='2023-01-01', corrected=False)
        self.client.login(username='testuser', password='testpass123')
        print("Setup de DashboardTestCase terminée.")

    def test_dashboard_access(self):
        response = self.client.get(reverse('dashboard'))
        print(f"Status code pour dashboard avec utilisateur connecté : {response.status_code}.")
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        print(f"Status code pour dashboard sans utilisateur connecté : {response.status_code}.")
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_contents(self):
        response = self.client.get(reverse('dashboard'))
        #print(f"Réponse du contenu du dashboard : {response.content}.")
        self.assertContains(response, '5 crédits')
        self.assertContains(response, 'Math Exercise')
        self.assertContains(response, 'Demander la correction d\'un exercice')

    def test_dashboard_no_credits(self):
        self.profile.credits = 0
        self.profile.save()
        response = self.client.get(reverse('dashboard'))
        #print(f"Contenu du dashboard quand l'utilisateur n'a pas de crédits : {response.content}.")
        self.assertContains(response, 'Pas assez de crédit pour déposer une demande')

class ExerciseUploadTestCase(TestCase):
    def setUp(self):
        # Création d'un utilisateur pour les tests avec des crédits ou sans crédits selon le test
        self.user_with_credits = User.objects.create_user(username='user_with_credits', password='pass123')
        self.user_without_credits = User.objects.create_user(username='user_without_credits', password='pass123')
        self.profile_with_credits = UserProfile.objects.create(user=self.user_with_credits, credits=5)
        self.profile_without_credits = UserProfile.objects.create(user=self.user_without_credits, credits=0)
        self.url = reverse('upload_exercise')  # Assurez-vous que l'URL est correctement nommée

    def test_access_page_with_credits(self):
        # Teste l'accès à la page avec des crédits
        self.client.login(username='user_with_credits', password='pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Uploader un exercice")

    def test_access_page_without_credits(self):
        # Teste l'accès à la page sans crédits
        self.client.login(username='user_without_credits', password='pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Vous n'avez pas assez de crédits pour accéder à cette page.")

    @override_settings(MEDIA_ROOT='test_media')
    def test_form_submission(self):
        self.client.login(username='user_with_credits', password='pass123')
        form_data = {
            'title': 'Test Exercise',
            'text': 'Solve the equation',
        }
        form_files = {
            'photo_statement': SimpleUploadedFile("file.jpg", get_image_file().read(), content_type="image/jpeg"),
            'photo_answer': SimpleUploadedFile("file2.jpg", get_image_file().read(), content_type="image/jpeg")
        }
        response = self.client.post(self.url, data={**form_data, **form_files}, follow=True)
        
        print(response.content)
        if not Exercise.objects.filter(title='Test Exercise').exists():
            if hasattr(response, 'context') and 'form' in response.context:
                print("Form Errors:", response.context['form'].errors.as_text())
        self.assertTrue(Exercise.objects.filter(title='Test Exercise').exists())

if __name__ == "__main__":
    TestCase.main()
