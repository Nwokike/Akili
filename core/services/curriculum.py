from typing import Optional, List
from django.db.models import QuerySet
from django.db import transaction

from curriculum.models import (
    SchoolLevel, Subject, Term, Week, SubjectCurriculum, 
    Topic, StudentProgramme, SubjectEnrolment, 
    AcademicSession, LegacyExamMapping
)


class CurriculumService:
    
    @staticmethod
    def get_school_levels() -> QuerySet[SchoolLevel]:
        return SchoolLevel.objects.all().order_by('level_order')
    
    @staticmethod
    def get_school_level_by_name(name: str) -> Optional[SchoolLevel]:
        try:
            return SchoolLevel.objects.get(name=name)
        except SchoolLevel.DoesNotExist:
            return None
    
    @staticmethod
    def get_school_level_by_id(level_id: int) -> Optional[SchoolLevel]:
        try:
            return SchoolLevel.objects.get(id=level_id)
        except SchoolLevel.DoesNotExist:
            return None
    
    @staticmethod
    def get_subjects_for_level(school_level: SchoolLevel) -> QuerySet[Subject]:
        return school_level.subjects.all().order_by('name')
    
    @staticmethod
    def get_subjects_for_level_by_id(level_id: int) -> QuerySet[Subject]:
        try:
            school_level = SchoolLevel.objects.get(id=level_id)
            return school_level.subjects.all().order_by('name')
        except SchoolLevel.DoesNotExist:
            return Subject.objects.none()
    
    @staticmethod
    def get_terms() -> QuerySet[Term]:
        return Term.objects.all().order_by('order')
    
    @staticmethod
    def get_term_by_id(term_id: int) -> Optional[Term]:
        try:
            return Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            return None
    
    @staticmethod
    def get_subject_by_id(subject_id: int) -> Optional[Subject]:
        try:
            return Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return None
    
    @staticmethod
    def get_curriculum(
        school_level: SchoolLevel, 
        subject: Subject, 
        term: Term,
        version: str = "2025"
    ) -> Optional[SubjectCurriculum]:
        try:
            return SubjectCurriculum.objects.get(
                school_level=school_level,
                subject=subject,
                term=term,
                version=version
            )
        except SubjectCurriculum.DoesNotExist:
            return None
    
    @staticmethod
    def get_curriculum_by_ids(
        school_level_id: int,
        subject_id: int,
        term_id: int,
        version: str = "2025"
    ) -> Optional[SubjectCurriculum]:
        try:
            return SubjectCurriculum.objects.select_related(
                'school_level', 'subject', 'term'
            ).get(
                school_level_id=school_level_id,
                subject_id=subject_id,
                term_id=term_id,
                version=version
            )
        except SubjectCurriculum.DoesNotExist:
            return None
    
    @staticmethod
    def get_topics_for_curriculum(curriculum: SubjectCurriculum) -> QuerySet[Topic]:
        return curriculum.topics.select_related('week').order_by('week__week_number', 'order')
    
    @staticmethod
    def get_weeks_for_term(term: Term) -> QuerySet[Week]:
        return term.weeks.all().order_by('week_number')
    
    @staticmethod
    def get_legacy_mapping(
        exam_type: str, 
        subject_name: str
    ) -> Optional[LegacyExamMapping]:
        try:
            return LegacyExamMapping.objects.select_related(
                'school_level', 'subject', 'curriculum'
            ).get(
                exam_type=exam_type,
                subject_name=subject_name
            )
        except LegacyExamMapping.DoesNotExist:
            return None
    
    @staticmethod
    def get_active_session() -> Optional[AcademicSession]:
        try:
            return AcademicSession.objects.get(is_active=True)
        except AcademicSession.DoesNotExist:
            return AcademicSession.objects.order_by('-start_date').first()
    
    @staticmethod
    @transaction.atomic
    def get_or_create_programme(
        user,
        school_level: SchoolLevel,
        academic_session: Optional[AcademicSession] = None
    ) -> StudentProgramme:
        if academic_session is None:
            academic_session = CurriculumService.get_active_session()
            if academic_session is None:
                raise ValueError("No active academic session found")
        
        programme, created = StudentProgramme.objects.get_or_create(
            user=user,
            academic_session=academic_session,
            school_level=school_level,
            defaults={'is_active': True}
        )
        return programme
    
    @staticmethod
    @transaction.atomic
    def create_enrolment(
        user,
        school_level: SchoolLevel,
        subject: Subject,
        term: Term,
        academic_session: Optional[AcademicSession] = None
    ) -> SubjectEnrolment:
        programme = CurriculumService.get_or_create_programme(
            user, school_level, academic_session
        )
        
        curriculum = CurriculumService.get_curriculum(school_level, subject, term)
        
        first_week = term.weeks.order_by('week_number').first()
        
        enrolment, created = SubjectEnrolment.objects.get_or_create(
            programme=programme,
            subject=subject,
            defaults={
                'curriculum': curriculum,
                'current_term': term,
                'current_week': first_week,
                'progress_percentage': 0.00
            }
        )
        
        if not created and enrolment.current_term != term:
            enrolment.current_term = term
            enrolment.curriculum = curriculum
            enrolment.current_week = first_week
            enrolment.save()
        
        return enrolment
    
    @staticmethod
    def get_user_enrolments(user) -> QuerySet[SubjectEnrolment]:
        return SubjectEnrolment.objects.filter(
            programme__user=user,
            programme__is_active=True
        ).select_related(
            'subject', 'curriculum', 'current_term', 'current_week', 
            'programme__school_level', 'programme__academic_session'
        ).order_by('-last_accessed')
    
    @staticmethod
    def get_enrolment_by_id(enrolment_id: int, user) -> Optional[SubjectEnrolment]:
        try:
            return SubjectEnrolment.objects.select_related(
                'subject', 'curriculum', 'current_term', 'current_week',
                'programme__school_level', 'programme__academic_session'
            ).get(id=enrolment_id, programme__user=user)
        except SubjectEnrolment.DoesNotExist:
            return None
    
    @staticmethod
    def update_enrolment_progress(
        enrolment: SubjectEnrolment,
        current_week: Optional[Week] = None,
        progress_percentage: Optional[float] = None
    ) -> SubjectEnrolment:
        if current_week:
            enrolment.current_week = current_week
        if progress_percentage is not None:
            enrolment.progress_percentage = progress_percentage
        enrolment.save()
        return enrolment
    
    @staticmethod
    def migrate_legacy_course(user, exam_type: str, subject_name: str, term: Term) -> Optional[SubjectEnrolment]:
        mapping = CurriculumService.get_legacy_mapping(exam_type, subject_name)
        if not mapping:
            return None
        
        return CurriculumService.create_enrolment(
            user=user,
            school_level=mapping.school_level,
            subject=mapping.subject,
            term=term
        )
    
    @staticmethod
    def get_previous_topics(
        curriculum: SubjectCurriculum, 
        current_week: Week,
        limit: int = 5
    ) -> List[Topic]:
        return list(curriculum.topics.filter(
            week__week_number__lt=current_week.week_number
        ).select_related('week').order_by('-week__week_number', '-order')[:limit])
    
    @staticmethod
    def get_topic_by_id(topic_id: int) -> Optional[Topic]:
        try:
            return Topic.objects.select_related(
                'curriculum', 'curriculum__school_level', 
                'curriculum__subject', 'curriculum__term', 'week'
            ).get(id=topic_id)
        except Topic.DoesNotExist:
            return None
    
    @staticmethod
    def calculate_progress(enrolment: SubjectEnrolment) -> float:
        if not enrolment.curriculum or not enrolment.current_week:
            return 0.0
        
        total_topics = enrolment.curriculum.topics.count()
        if total_topics == 0:
            return 0.0
        
        completed_topics = enrolment.curriculum.topics.filter(
            week__week_number__lt=enrolment.current_week.week_number
        ).count()
        
        return round((completed_topics / total_topics) * 100, 2)
