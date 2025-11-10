from django.db import models


class JAMBSyllabus(models.Model):
    """JAMB Examination Syllabus Storage"""
    subject = models.CharField(max_length=200, unique=True)
    syllabus_content = models.TextField(
        help_text="Markdown format with LaTeX for formulas"
    )
    version = models.CharField(max_length=50, default="2025")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jamb_syllabus'
        verbose_name = 'JAMB Syllabus'
        verbose_name_plural = 'JAMB Syllabuses'
    
    def __str__(self):
        return f"JAMB - {self.subject} (v{self.version})"


class SSCESyllabus(models.Model):
    """SSCE (WAEC/NECO) Examination Syllabus Storage"""
    subject = models.CharField(max_length=200, unique=True)
    syllabus_content = models.TextField(
        help_text="Markdown format with LaTeX for formulas"
    )
    version = models.CharField(max_length=50, default="2025")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ssce_syllabus'
        verbose_name = 'SSCE Syllabus'
        verbose_name_plural = 'SSCE Syllabuses'
    
    def __str__(self):
        return f"SSCE - {self.subject} (v{self.version})"


class JSSSyllabus(models.Model):
    """Junior Secondary School Examination Syllabus Storage"""
    subject = models.CharField(max_length=200, unique=True)
    syllabus_content = models.TextField(
        help_text="Markdown format with LaTeX for formulas"
    )
    version = models.CharField(max_length=50, default="2025")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jss_syllabus'
        verbose_name = 'JSS Syllabus'
        verbose_name_plural = 'JSS Syllabuses'
    
    def __str__(self):
        return f"JSS - {self.subject} (v{self.version})"
