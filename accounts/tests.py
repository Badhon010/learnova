"""
Tests for account routes: dashboard, profile edit (with avatar upload),
profile detail, contributor hub, and topic/chapter/lesson management routes.
"""
from io import BytesIO
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.models import UserProfile
from learning.models import Topic, Chapter, Lesson


class AccountRouteTests(TestCase):
    """Unauthenticated route access."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='alice', email='alice@test.com', password='testpass123',
        )

    # ── auth-gated routes redirect ──────────────────────────────────────

    def test_dashboard_redirects_when_anon(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url)

    def test_profile_edit_redirects_when_anon(self):
        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url)

    def test_my_lessons_redirects_when_anon(self):
        resp = self.client.get(reverse('my_lessons'))
        self.assertEqual(resp.status_code, 302)

    def test_saved_lessons_redirects_when_anon(self):
        resp = self.client.get(reverse('saved_lessons'))
        self.assertEqual(resp.status_code, 302)

    # ── public route: profile detail ────────────────────────────────────

    def test_profile_detail_200(self):
        resp = self.client.get(reverse('profile_detail', args=['alice']))
        self.assertEqual(resp.status_code, 200)

    def test_profile_detail_404(self):
        resp = self.client.get(reverse('profile_detail', args=['nobody']))
        self.assertEqual(resp.status_code, 404)


class DashboardViewTests(TestCase):
    """Authenticated dashboard."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='bob', email='bob@test.com', password='testpass123',
        )
        self.client.login(username='bob', password='testpass123')

    def test_dashboard_200(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'bob')


class ProfileEditTests(TestCase):
    """Profile edit form — GET and POST, with and without avatar upload."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='carol', email='carol@test.com', password='testpass123',
            first_name='Carol',
        )
        self.client.login(username='carol', password='testpass123')
        self.profile = self.user.profile

    def test_get_profile_edit_200(self):
        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'carol')

    def test_post_update_name(self):
        resp = self.client.post(reverse('profile_edit'), {
            'first_name': 'Carolina',
            'last_name': 'Doe',
            'email': 'carol@test.com',
            'bio': 'Hello world',
        })
        self.assertEqual(resp.status_code, 302)  # redirect to dashboard
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Carolina')

    def test_post_update_bio(self):
        resp = self.client.post(reverse('profile_edit'), {
            'first_name': 'Carol',
            'last_name': '',
            'email': 'carol@test.com',
            'bio': 'Updated bio text',
        })
        self.assertEqual(resp.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio text')

    def test_post_with_avatar_upload(self):
        """Upload a tiny PNG as avatar."""
        # Use Pillow to generate a valid PNG
        from PIL import Image
        from io import BytesIO
        buf = BytesIO()
        Image.new('RGB', (10, 10), 'red').save(buf, 'PNG')
        buf.seek(0)
        avatar_file = SimpleUploadedFile('avatar.png', buf.read(), content_type='image/png')
        resp = self.client.post(reverse('profile_edit'), {
            'first_name': 'Carol',
            'last_name': '',
            'email': 'carol@test.com',
            'bio': '',
            'avatar': avatar_file,
        })
        if resp.status_code != 302:
            # Debug: extract form errors
            import re
            content = resp.content.decode()
            errors = re.findall(r'<ul class="errorlist">(.*?)</ul>', content, re.DOTALL)
            for e in errors:
                print(f'  FORM ERROR: {e[:500]}')
        self.assertEqual(resp.status_code, 302)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar, 'Avatar should be saved after upload')

    def test_post_without_avatar_keeps_existing(self):
        """Posting without avatar field should not clear it."""
        # Manually set an avatar path
        self.profile.avatar = 'avatars/existing.png'
        self.profile.save()

        resp = self.client.post(reverse('profile_edit'), {
            'first_name': 'Carol',
            'last_name': '',
            'email': 'carol@test.com',
            'bio': 'no avatar',
        })
        self.assertEqual(resp.status_code, 302)
        self.profile.refresh_from_db()
        # avatar still set (ClearableFileInput without file keeps existing)
        self.assertTrue(self.profile.avatar)

    def test_post_invalid_email_shows_error(self):
        resp = self.client.post(reverse('profile_edit'), {
            'first_name': 'Carol',
            'last_name': '',
            'email': 'not-an-email',
            'bio': '',
        })
        self.assertEqual(resp.status_code, 200)  # re-renders form
        self.assertContains(resp, 'Enter a valid')


class ProfileEditFormUnitTests(TestCase):
    """Unit tests for ProfileEditForm itself."""

    def test_form_fields(self):
        from accounts.forms import ProfileEditForm
        user = User.objects.create_user(
            username='testu', email='t@t.com', password='testpass123',
        )
        form = ProfileEditForm(instance=user.profile, user=user)
        self.assertIn('avatar', form.fields)
        self.assertIn('bio', form.fields)
        self.assertIn('first_name', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('github_url', form.fields)

    def test_avatar_widget_has_accept_attr(self):
        from accounts.forms import ProfileEditForm
        user = User.objects.create_user(
            username='testu2', email='t2@t.com', password='testpass123',
        )
        form = ProfileEditForm(instance=user.profile, user=user)
        widget = form.fields['avatar'].widget
        self.assertIn('image/png', widget.attrs.get('accept', ''))

    def test_save_updates_user_fields(self):
        from accounts.forms import ProfileEditForm
        user = User.objects.create_user(
            username='testu3', email='t3@t.com', password='testpass123',
        )
        profile = user.profile
        form = ProfileEditForm(
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'new@test.com',
                'bio': 'new bio',
            },
            instance=profile,
            user=user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.email, 'new@test.com')


class ContributorRouteTests(TestCase):
    """Contributor-gated routes."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dave', email='dave@test.com', password='testpass123',
        )
        self.client.login(username='dave', password='testpass123')

    def test_my_lessons_redirects_for_reader(self):
        """Non-contributors should be redirected."""
        self.user.profile.role = 'reader'
        self.user.profile.save()
        resp = self.client.get(reverse('my_lessons'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('dashboard', resp.url)

    def test_my_lessons_200_for_contributor(self):
        self.user.profile.role = 'contributor'
        self.user.profile.save()
        resp = self.client.get(reverse('my_lessons'))
        self.assertEqual(resp.status_code, 200)

    def test_create_topic_chapter_requires_contributor(self):
        """The create_chapter view checks ownership, not contributor role.
        Verify a non-owner is redirected away."""
        other = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123',
        )
        topic = Topic.objects.create(
            title='Other Topic', slug='other-topic',
            description='Owned by other', is_published=False,
            status='draft', owner=other,
        )
        self.user.profile.role = 'reader'
        self.user.profile.save()
        resp = self.client.get(
            reverse('create_chapter', args=[topic.slug]),
        )
        self.assertEqual(resp.status_code, 302)

    def test_create_chapter_200_for_owner(self):
        self.user.profile.role = 'contributor'
        self.user.profile.save()
        topic = Topic.objects.create(
            title='My Topic', slug='my-topic',
            description='A topic', is_published=False,
            status='draft', owner=self.user,
        )
        resp = self.client.get(
            reverse('create_chapter', args=[topic.slug]),
        )
        self.assertEqual(resp.status_code, 200)

    def test_manage_topic_requires_ownership(self):
        other = User.objects.create_user(
            username='eve', email='eve@test.com', password='testpass123',
        )
        topic = Topic.objects.create(
            title='Eve Topic', slug='eve-topic',
            description='Eve owns this', is_published=False,
            status='draft', owner=other,
        )
        resp = self.client.get(
            reverse('manage_topic', args=[topic.slug]),
        )
        self.assertEqual(resp.status_code, 302)  # redirected away


class EditTopicTests(TestCase):
    """Topic edit with image upload."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='fay', email='fay@test.com', password='testpass123',
        )
        self.client.login(username='fay', password='testpass123')
        self.topic = Topic.objects.create(
            title='Edit Topic', slug='edit-topic',
            description='Editable', is_published=False,
            status='draft', owner=self.user,
        )

    def test_edit_topic_get(self):
        resp = self.client.get(
            reverse('edit_topic', args=[self.topic.slug]),
        )
        self.assertEqual(resp.status_code, 200)

    def test_edit_topic_update_title(self):
        resp = self.client.post(
            reverse('edit_topic', args=[self.topic.slug]),
            {
                'title': 'Updated Topic Title',
                'description': 'Updated desc',
                'meta_title': '',
                'meta_description': '',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.title, 'Updated Topic Title')

    def test_edit_topic_upload_image(self):
        from PIL import Image
        from io import BytesIO
        buf = BytesIO()
        Image.new('RGB', (10, 10), 'blue').save(buf, 'PNG')
        buf.seek(0)
        img_file = SimpleUploadedFile('cover.png', buf.read(), content_type='image/png')
        resp = self.client.post(
            reverse('edit_topic', args=[self.topic.slug]),
            {
                'title': 'Edit Topic',
                'description': 'Editable',
                'meta_title': 'SEO Title',
                'meta_description': 'SEO Desc',
                'image': img_file,
                'image_alt': 'Cover image description',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.image, 'Image should be saved')
        self.assertEqual(self.topic.image_alt, 'Cover image description')
        self.assertEqual(self.topic.meta_title, 'SEO Title')
