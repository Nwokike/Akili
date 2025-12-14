from django.test import TestCase
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus


class JAMBSyllabusModelTestCase(TestCase):
    """Tests for JAMBSyllabus model"""
    
    def test_jamb_syllabus_creation(self):
        """Test creating a JAMB syllabus entry"""
        syllabus = JAMBSyllabus.objects.create(
            subject='Mathematics',
            syllabus_content='## Topics\n- Algebra\n- Geometry\n- Trigonometry',
            version='2025'
        )
        self.assertEqual(syllabus.subject, 'Mathematics')
        self.assertEqual(syllabus.version, '2025')
    
    def test_jamb_syllabus_string_representation(self):
        """Test JAMB syllabus string representation"""
        syllabus = JAMBSyllabus.objects.create(
            subject='Physics',
            syllabus_content='Physics content'
        )
        self.assertIn('JAMB', str(syllabus))
        self.assertIn('Physics', str(syllabus))
    
    def test_jamb_subject_unique(self):
        """Test JAMB subject is unique"""
        JAMBSyllabus.objects.create(
            subject='Chemistry',
            syllabus_content='Chemistry content'
        )
        
        with self.assertRaises(Exception):
            JAMBSyllabus.objects.create(
                subject='Chemistry',
                syllabus_content='Different content'
            )
    
    def test_jamb_syllabus_update(self):
        """Test updating JAMB syllabus"""
        syllabus = JAMBSyllabus.objects.create(
            subject='Biology',
            syllabus_content='Initial content'
        )
        
        syllabus.syllabus_content = 'Updated content'
        syllabus.save()
        
        syllabus.refresh_from_db()
        self.assertEqual(syllabus.syllabus_content, 'Updated content')


class SSCESyllabusModelTestCase(TestCase):
    """Tests for SSCESyllabus model"""
    
    def test_ssce_syllabus_creation(self):
        """Test creating an SSCE syllabus entry"""
        syllabus = SSCESyllabus.objects.create(
            subject='English Language',
            syllabus_content='## Grammar\n- Tenses\n- Parts of Speech',
            version='2025'
        )
        self.assertEqual(syllabus.subject, 'English Language')
    
    def test_ssce_syllabus_string_representation(self):
        """Test SSCE syllabus string representation"""
        syllabus = SSCESyllabus.objects.create(
            subject='Literature',
            syllabus_content='Literature content'
        )
        self.assertIn('SSCE', str(syllabus))
        self.assertIn('Literature', str(syllabus))
    
    def test_ssce_subject_unique(self):
        """Test SSCE subject is unique"""
        SSCESyllabus.objects.create(
            subject='Government',
            syllabus_content='Government content'
        )
        
        with self.assertRaises(Exception):
            SSCESyllabus.objects.create(
                subject='Government',
                syllabus_content='Different content'
            )
    
    def test_ssce_default_version(self):
        """Test SSCE default version"""
        syllabus = SSCESyllabus.objects.create(
            subject='Economics',
            syllabus_content='Economics content'
        )
        self.assertEqual(syllabus.version, '2025')


class JSSSyllabusModelTestCase(TestCase):
    """Tests for JSSSyllabus model"""
    
    def test_jss_syllabus_creation(self):
        """Test creating a JSS syllabus entry"""
        syllabus = JSSSyllabus.objects.create(
            subject='Basic Science',
            syllabus_content='## Topics\n- Living Things\n- Matter',
            version='2025'
        )
        self.assertEqual(syllabus.subject, 'Basic Science')
    
    def test_jss_syllabus_string_representation(self):
        """Test JSS syllabus string representation"""
        syllabus = JSSSyllabus.objects.create(
            subject='Basic Technology',
            syllabus_content='Basic Tech content'
        )
        self.assertIn('JSS', str(syllabus))
        self.assertIn('Basic Technology', str(syllabus))
    
    def test_jss_subject_unique(self):
        """Test JSS subject is unique"""
        JSSSyllabus.objects.create(
            subject='Social Studies',
            syllabus_content='Social Studies content'
        )
        
        with self.assertRaises(Exception):
            JSSSyllabus.objects.create(
                subject='Social Studies',
                syllabus_content='Different content'
            )
    
    def test_jss_syllabus_latex_content(self):
        """Test JSS syllabus with LaTeX content"""
        syllabus = JSSSyllabus.objects.create(
            subject='Mathematics',
            syllabus_content='## Algebra\n$$x^2 + 2x + 1 = 0$$'
        )
        self.assertIn('$$', syllabus.syllabus_content)


class SyllabusQueryTestCase(TestCase):
    """Tests for syllabus queries"""
    
    def test_get_all_jamb_syllabuses(self):
        """Test getting all JAMB syllabuses"""
        JAMBSyllabus.objects.create(subject='Math', syllabus_content='Math')
        JAMBSyllabus.objects.create(subject='Physics', syllabus_content='Physics')
        
        syllabuses = JAMBSyllabus.objects.all()
        self.assertEqual(syllabuses.count(), 2)
    
    def test_filter_by_version(self):
        """Test filtering syllabuses by version"""
        JAMBSyllabus.objects.create(
            subject='Chemistry',
            syllabus_content='Chemistry 2024',
            version='2024'
        )
        JAMBSyllabus.objects.create(
            subject='Biology',
            syllabus_content='Biology 2025',
            version='2025'
        )
        
        current_year = JAMBSyllabus.objects.filter(version='2025')
        self.assertEqual(current_year.count(), 1)
        self.assertEqual(current_year.first().subject, 'Biology')
