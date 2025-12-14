from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .models import (
    Assessment, AssessmentQuestion, AssessmentSubmission, Grade, ProgressReport,
    TeacherProfile, TeacherClass, Assignment, AssignmentSubmission,
    ParentProfile, Notification,
    ContentVersion, ContentModerationQueue, CurriculumUpdateRequest
)
from curriculum.models import (
    AcademicSession, SchoolLevel, Subject, Term, Week, SubjectCurriculum
)

User = get_user_model()


class AssessmentModelTests(TestCase):
    """Tests for Assessment models"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Student'
        )
        cls.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Teacher'
        )
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date='2024-09-09',
            end_date='2025-07-18',
            is_active=True
        )
        cls.school_level = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        cls.subject = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            is_science_subject=True
        )
        cls.subject.school_levels.add(cls.school_level)
        cls.term = Term.objects.create(
            name='First Term',
            order=1,
            total_weeks=14
        )
        cls.week = Week.objects.create(
            term=cls.term,
            week_number=1,
            week_type='INSTRUCTIONAL'
        )
        cls.curriculum = SubjectCurriculum.objects.create(
            school_level=cls.school_level,
            subject=cls.subject,
            term=cls.term,
            version='2024'
        )

    def test_assessment_creation(self):
        assessment = Assessment.objects.create(
            title='Week 1 Test',
            assessment_type='WEEKLY',
            curriculum=self.curriculum,
            week=self.week,
            created_by=self.teacher_user,
            total_marks=100,
            passing_marks=50,
            status='PUBLISHED'
        )
        self.assertEqual(str(assessment), 'Week 1 Test (Weekly Test)')

    def test_assessment_submission_percentage(self):
        assessment = Assessment.objects.create(
            title='Test',
            assessment_type='WEEKLY',
            curriculum=self.curriculum,
            created_by=self.teacher_user,
            total_marks=100,
            passing_marks=50,
            status='PUBLISHED'
        )
        submission = AssessmentSubmission.objects.create(
            assessment=assessment,
            student=self.user,
            score=75,
            status='GRADED'
        )
        self.assertEqual(submission.percentage, 75.0)
        self.assertTrue(submission.is_passing)

    def test_grade_computation_excellent(self):
        grade = Grade.objects.create(
            student=self.user,
            curriculum=self.curriculum,
            term=self.term,
            continuous_assessment_score=35,
            exam_score=45
        )
        grade.compute_grade()
        self.assertEqual(grade.grade_letter, 'A')
        self.assertEqual(grade.remarks, 'Excellent')

    def test_grade_computation_fail(self):
        grade = Grade.objects.create(
            student=self.user,
            curriculum=self.curriculum,
            term=self.term,
            continuous_assessment_score=15,
            exam_score=20
        )
        grade.compute_grade()
        self.assertEqual(grade.grade_letter, 'F')


class TeacherModelTests(TestCase):
    """Tests for Teacher models"""
    
    @classmethod
    def setUpTestData(cls):
        cls.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Teacher'
        )
        cls.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123'
        )
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date='2024-09-09',
            end_date='2025-07-18'
        )
        cls.school_level = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        cls.subject = Subject.objects.create(name='Mathematics', code='MTH')
        cls.term = Term.objects.create(name='First Term', order=1)

    def test_teacher_profile(self):
        profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            employee_id='TCH001',
            is_verified=True
        )
        self.assertIn('Teacher:', str(profile))

    def test_teacher_class_students(self):
        profile = TeacherProfile.objects.create(user=self.teacher_user)
        teacher_class = TeacherClass.objects.create(
            teacher=profile,
            school_level=self.school_level,
            subject=self.subject,
            academic_session=self.session
        )
        teacher_class.students.add(self.student)
        self.assertEqual(teacher_class.students.count(), 1)


class ParentModelTests(TestCase):
    """Tests for Parent models"""
    
    @classmethod
    def setUpTestData(cls):
        cls.parent_user = User.objects.create_user(
            email='parent@test.com',
            password='testpass123'
        )
        cls.child = User.objects.create_user(
            email='child@test.com',
            password='testpass123'
        )

    def test_parent_profile_with_children(self):
        profile = ParentProfile.objects.create(user=self.parent_user)
        profile.children.add(self.child)
        self.assertEqual(profile.children.count(), 1)

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.parent_user,
            notification_type='GRADE',
            title='New Grade',
            message='Your child got a new grade'
        )
        self.assertFalse(notification.is_read)


class AssessmentViewTests(TestCase):
    """Tests for Assessment views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='student@test.com',
            password='testpass123'
        )
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date='2024-09-09',
            end_date='2025-07-18'
        )
        cls.school_level = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        cls.subject = Subject.objects.create(name='Mathematics', code='MTH')
        cls.term = Term.objects.create(name='First Term', order=1)
        cls.curriculum = SubjectCurriculum.objects.create(
            school_level=cls.school_level,
            subject=cls.subject,
            term=cls.term,
            version='2024'
        )

    def setUp(self):
        self.client = Client()
        self.client.login(email='student@test.com', password='testpass123')

    def test_assessments_list_view(self):
        response = self.client.get(reverse('assessments:assessments_list'))
        self.assertEqual(response.status_code, 200)

    def test_my_grades_view(self):
        response = self.client.get(reverse('assessments:my_grades'))
        self.assertEqual(response.status_code, 200)

    def test_notifications_view(self):
        response = self.client.get(reverse('assessments:notifications'))
        self.assertEqual(response.status_code, 200)


class TeacherViewTests(TestCase):
    """Tests for Teacher views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            password='testpass123'
        )
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date='2024-09-09',
            end_date='2025-07-18'
        )
        cls.school_level = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        cls.subject = Subject.objects.create(name='Mathematics', code='MTH')
        cls.teacher_profile = TeacherProfile.objects.create(
            user=cls.teacher_user,
            employee_id='TCH001'
        )
        cls.teacher_class = TeacherClass.objects.create(
            teacher=cls.teacher_profile,
            school_level=cls.school_level,
            subject=cls.subject,
            academic_session=cls.session
        )

    def setUp(self):
        self.client = Client()
        self.client.login(email='teacher@test.com', password='testpass123')

    def test_teacher_dashboard_view(self):
        response = self.client.get(reverse('assessments:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_class_detail_view(self):
        response = self.client.get(
            reverse('assessments:class_detail', kwargs={'pk': self.teacher_class.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_class_analytics_view(self):
        response = self.client.get(
            reverse('assessments:class_analytics', kwargs={'pk': self.teacher_class.pk})
        )
        self.assertEqual(response.status_code, 200)


class ParentViewTests(TestCase):
    """Tests for Parent views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.parent_user = User.objects.create_user(
            email='parent@test.com',
            password='testpass123'
        )
        cls.child = User.objects.create_user(
            email='child@test.com',
            password='testpass123'
        )
        cls.parent_profile = ParentProfile.objects.create(user=cls.parent_user)
        cls.parent_profile.children.add(cls.child)

    def setUp(self):
        self.client = Client()
        self.client.login(email='parent@test.com', password='testpass123')

    def test_parent_dashboard_view(self):
        response = self.client.get(reverse('assessments:parent_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_child_progress_view(self):
        response = self.client.get(
            reverse('assessments:child_progress', kwargs={'child_id': self.child.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_parent_payments_view(self):
        response = self.client.get(reverse('assessments:parent_payments'))
        self.assertEqual(response.status_code, 200)


class NotificationTests(TestCase):
    """Tests for Notification functionality"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123'
        )

    def setUp(self):
        self.client = Client()
        self.client.login(email='user@test.com', password='testpass123')
        self.notification = Notification.objects.create(
            user=self.user,
            notification_type='GENERAL',
            title='Test',
            message='Test message'
        )

    def test_mark_notification_read(self):
        response = self.client.get(
            reverse('assessments:mark_notification_read', kwargs={'pk': self.notification.pk})
        )
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(
            user=self.user,
            notification_type='GRADE',
            title='Another',
            message='Another test'
        )
        self.client.get(reverse('assessments:mark_all_read'))
        unread = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread, 0)
