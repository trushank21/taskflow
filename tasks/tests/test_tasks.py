from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from projects.models import Project
from tasks.models import Task, TaskHistory

from unittest.mock import patch


class BaseTaskTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Users
        self.admin = User.objects.create_user(username='admin', password='pass')
        self.manager = User.objects.create_user(username='manager', password='pass')
        self.developer = User.objects.create_user(username='dev', password='pass')
        self.other_dev = User.objects.create_user(username='dev2', password='pass')

        # Fake profiles (adjust if using signals)
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.manager.profile.role = 'manager'
        self.manager.profile.save()

        self.developer.profile.role = 'developer'
        self.developer.profile.save()

        self.other_dev.profile.role = 'developer'
        self.other_dev.profile.save()

        # Project
        self.project = Project.objects.create(
            title="Test Project",
            status="active",
            team_lead=self.manager,
            created_by=self.admin,
        )
        self.project.team_members.add(self.developer)

        # Task
        self.task = Task.objects.create(
            title="Test Task",
            project=self.project,
            assigned_to=self.developer,
            assigned_by=self.manager,
            status="todo",
            progress=0
        )

class DashboardTests(BaseTaskTestCase):

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('tasks:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_developer_sees_only_assigned_tasks(self):
        self.client.login(username='dev', password='pass')
        response = self.client.get(reverse('tasks:dashboard'))

        self.assertContains(response, "Test Task")

    def test_efficiency_calculation(self):
        self.task.status = "completed"
        self.task.progress = 100
        self.task.save()

        self.client.login(username='manager', password='pass')
        response = self.client.get(reverse('tasks:dashboard'))

        self.assertEqual(response.context['completed_tasks'], 1)

class StatusSyncTests(BaseTaskTestCase):

    def test_status_forces_progress_100(self):
        self.client.login(username='manager', password='pass')

        response = self.client.post(
            reverse('tasks:update_task_status', args=[self.task.pk]),
            {'status': 'completed'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.task.refresh_from_db()

        self.assertEqual(self.task.progress, 100)
        self.assertEqual(self.task.status, 'completed')

    def test_progress_100_sets_completed(self):
        self.client.login(username='manager', password='pass')

        response = self.client.post(
            reverse('tasks:update_progress', args=[self.task.pk]),
            {'progress': 100},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.task.refresh_from_db()

        self.assertEqual(self.task.status, 'completed')


class PermissionTests(BaseTaskTestCase):

    def test_developer_cannot_edit_others_task(self):
        self.client.login(username='dev2', password='pass')

        response = self.client.post(
            reverse('tasks:update_progress', args=[self.task.pk]),
            {'progress': 50}
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_any_task(self):
        self.client.login(username='admin', password='pass')

        response = self.client.post(
            reverse('tasks:update_progress', args=[self.task.pk]),
            {'progress': 50}
        )

        self.assertNotEqual(response.status_code, 403)


class HistoryTests(BaseTaskTestCase):

    def test_history_created_on_status_change(self):
        self.client.login(username='manager', password='pass')

        self.client.post(
            reverse('tasks:update_task_status', args=[self.task.pk]),
            {'status': 'in_progress'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(TaskHistory.objects.count(), 1)

from tasks.models import TaskComment

class CommentTests(BaseTaskTestCase):

    def test_only_author_can_edit_comment(self):
        comment = TaskComment.objects.create(
            task=self.task,
            commented_by=self.developer,
            comment="Original"
        )

        self.client.login(username='dev2', password='pass')

        response = self.client.post(
            reverse('tasks:edit_comment', args=[comment.pk]),
            {'comment': 'Hacked'}
        )

        self.assertEqual(response.status_code, 403)


from django.core.files.uploadedfile import SimpleUploadedFile
from tasks.models import TaskAttachment

class AttachmentTests(BaseTaskTestCase):

    def setUp(self):
        super().setUp()
        # prevent Cloudinary from attempting to upload during tests; return a
        # minimal dummy response so ``public_id`` is available.
        self._upload_patcher = patch('cloudinary.uploader.upload',
                                     return_value={
                                         'public_id': 'dummy',
                                         'url': 'http://example.com',
                                         'secure_url': 'https://example.com',
                                         'version': 1,
                                         'type': 'upload',
                                         'resource_type': 'auto',
                                     })
        self._upload_patcher.start()
        self.addCleanup(self._upload_patcher.stop)

    def test_only_uploader_can_delete(self):
        file = SimpleUploadedFile("test.txt", b"file content")

        attachment = TaskAttachment.objects.create(
            task=self.task,
            uploaded_by=self.developer,
            file=file,
            file_name="test.txt"
        )

        self.client.login(username='dev2', password='pass')

        response = self.client.post(
            reverse('tasks:delete_attachment', args=[attachment.pk])
        )

        # response may redirect before enforcing permission; ensure attachment
        # still exists afterwards as an authoritative check.
        self.assertTrue(TaskAttachment.objects.filter(pk=attachment.pk).exists())
        self.assertIn(response.status_code, (301, 302, 403))

    def test_download_uses_signed_url_when_available(self):
        file = SimpleUploadedFile("foo.txt", b"content")
        attachment = TaskAttachment.objects.create(
            task=self.task,
            uploaded_by=self.developer,
            file=file,
            file_name="foo.txt",
        )

        self.client.login(username='dev', password='pass')

        with patch('tasks.views.cloudinary_url') as mock_url:
            mock_url.return_value = ("https://example.com/download", None)
            resp = self.client.get(reverse('tasks:download_attachment', args=[attachment.pk]), follow=True)

        # follow=True ensures we see the final redirect; the first hop may be
        # the middleware adding a trailing slash.
        self.assertTrue(mock_url.called)
        # final target should be our fake cloudinary URL
        self.assertTrue(resp.redirect_chain)
        self.assertEqual(resp.redirect_chain[-1][0], "https://example.com/download")

    def test_download_falls_back_to_direct_url_if_cloudinary_fails(self):
        file = SimpleUploadedFile("bar.txt", b"foobar")
        attachment = TaskAttachment.objects.create(
            task=self.task,
            uploaded_by=self.developer,
            file=file,
            file_name="bar.txt",
        )

        self.client.login(username='dev', password='pass')

        with patch('tasks.views.cloudinary_url', side_effect=Exception("oops")):
            # We don't follow the external redirect to Cloudinary because the
        # test client will then land on a 404 from the fake URL.  Instead we
        # examine the ``Location`` header returned directly from our view.
        download_url = reverse('tasks:download_attachment', args=[attachment.pk])
        resp = self.client.get(download_url, follow=False)

        # the middleware may issue a 301 if the trailing slash was dropped;
        # chase that first step if needed.
        if resp.status_code == 301:
            resp = self.client.get(resp['Location'], follow=False)

        self.assertIn(resp.status_code, (301, 302))
        # final redirect target should equal whatever the storage backend says
        self.assertEqual(resp['Location'], attachment.file.url)