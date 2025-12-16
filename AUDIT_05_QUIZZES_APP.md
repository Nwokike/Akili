# COMPREHENSIVE AUDIT: quizzes App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: Free practice quizzes for each course module. AI-generated 5-question quizzes with instant grading.

**Files Reviewed**:
- `quizzes/models.py` (45 lines)
- `quizzes/views.py` (172 lines)
- `quizzes/urls.py` (12 lines)
- `quizzes/utils.py` (123 lines)
- `quizzes/admin.py`
- `quizzes/tests.py`
- `quizzes/templates/quizzes/quiz_form.html`
- `quizzes/templates/quizzes/quiz_results.html`
- `quizzes/templates/quizzes/quiz_history.html`

---

## 2. Data Models Analysis (quizzes/models.py)

### 2.1 QuizAttempt Model

```python
class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    module = models.ForeignKey('courses.Module', ...)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=10)
    questions_data = models.JSONField(default=list)  # MEMORY CONCERN
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_retake = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    user_answers = models.JSONField(default=dict)  # MEMORY CONCERN
```

### 2.2 MODEL ANALYSIS

| Field | Type | Issues | Notes |
|-------|------|--------|-------|
| user | ForeignKey | ✅ Good | CASCADE delete |
| module | ForeignKey | ✅ Good | CASCADE delete |
| score | IntegerField | ✅ Good | Simple counter |
| total_questions | IntegerField | Default 10, but quizzes are 5 | Consider updating default |
| questions_data | JSONField | ⚠️ MEMORY | Stores all questions + answers |
| user_answers | JSONField | ⚠️ MEMORY | Stores user responses |
| passed | BooleanField | ✅ Good | For module locking |

### 2.3 JSONField Memory Analysis

**questions_data Structure**:
```json
[
  {
    "question_text": "...",
    "choices": ["A", "B", "C", "D"],
    "correct_index": 0,
    "explanation": "..."
  }
]
```

**Estimated Size per Quiz**:
- 5 questions x ~500 bytes = ~2.5KB per attempt
- With thousands of users, this adds up

**RECOMMENDATION** for 1GB VM:
1. Consider archiving old quiz attempts (>30 days)
2. Or store questions in separate table to allow sharing
3. Monitor table size in production

### 2.4 Properties

```python
@property
def percentage(self):
    return round((self.score / self.total_questions) * 100, 2) if self.total_questions else 0

@property
def is_passing(self):
    return self.percentage >= 60
```

✅ Good - 60% passing threshold matches grading scale.

---

## 3. Views Analysis (quizzes/views.py)

### 3.1 Views Inventory

| View | Function | Auth | Purpose | Cost |
|------|----------|------|---------|------|
| start_quiz_view | POST | Yes | Generate new quiz | FREE |
| quiz_detail_view | GET/POST | Yes | Take/view quiz | FREE |
| quiz_history_view | GET | Yes | View all attempts | FREE |

### 3.2 CRITICAL: Quizzes are FREE

```python
# Quizzes are now FREE - no credit check needed
try:
    success, result_id_or_error = generate_quiz_and_save(module, request.user, num_questions=5)
```

**IMPORTANT**: Unlike courses (5 credits) and mock exams (5 credits), quizzes are **FREE and unlimited**.

This is documented in README: "Practice Quizzes: FREE"

### 3.3 start_quiz_view Analysis (lines 16-60)

```python
@login_required
def start_quiz_view(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    
    # Check for existing incomplete quiz
    existing_quiz = QuizAttempt.objects.filter(
        user=request.user,
        module=module,
        completed_at__isnull=True
    ).first()
    
    if existing_quiz:
        return redirect('quizzes:quiz_detail', quiz_id=existing_quiz.id)
```

**GOOD PRACTICES**:
- Checks for incomplete quiz first (no wasted AI calls)
- Allows retakes of completed quizzes
- Uses POST method requirement

**ISSUE**: No ownership check on module:
```python
module = get_object_or_404(Module, pk=module_id)
# Should verify: module.course.user == request.user
```

**SECURITY CONCERN**: User could potentially start quiz for someone else's module!

**RECOMMENDATION**:
```python
module = get_object_or_404(Module, pk=module_id, course__user=request.user)
```

### 3.4 quiz_detail_view Analysis (lines 63-138)

```python
quiz_attempt = get_object_or_404(
    QuizAttempt.objects.filter(user=request.user),
    pk=quiz_id
)
```

✅ Good - filters by user, preventing access to others' quizzes.

**Scoring Logic**:
```python
for index, question in enumerate(quiz_attempt.questions_data):
    user_choice_str = request.POST.get(f'q_{index}')
    correct_index_value = question.get('correct_index')
    
    if user_choice_str and correct_index_value is not None:
        user_choice = int(user_choice_str)
        correct_index = int(correct_index_value)
        is_correct = (user_choice == correct_index)
```

✅ Good - handles missing correct_index safely with `.get()`.

**Pass/Fail Logic**:
```python
quiz_attempt.passed = quiz_attempt.is_passing  # 60% threshold
```

✅ Good - uses property for consistency.

### 3.5 quiz_history_view Analysis (lines 141-172)

```python
completed_quizzes = QuizAttempt.objects.filter(
    user=request.user,
    completed_at__isnull=False
).order_by('-completed_at')

stats = completed_quizzes.aggregate(
    total_s=Sum('score'),
    total_q=Sum('total_questions')
)
```

**ISSUE**: No pagination! If user has hundreds of quiz attempts, this loads all into memory.

**RECOMMENDATION**:
```python
from django.core.paginator import Paginator

completed_quizzes = QuizAttempt.objects.filter(
    user=request.user,
    completed_at__isnull=False
).order_by('-completed_at')

paginator = Paginator(completed_quizzes, 20)  # 20 per page
page = request.GET.get('page', 1)
quizzes = paginator.get_page(page)
```

---

## 4. Utils Analysis (quizzes/utils.py)

### 4.1 generate_quiz_and_save Function

```python
def generate_quiz_and_save(module: Module, user: CustomUser, num_questions=5) -> tuple[bool, str]:
```

**AI Prompt Construction**:
- Includes class level and subject context
- Specifies exact JSON structure required
- Requests 5 questions with 4 choices each
- correct_index must be 0-3 (not letter)

**Error Handling**:
- JSON parsing with detailed error logging
- Validates each question has required fields
- Returns False with error message on failure

### 4.2 CRITICAL: JSON Parsing Robustness

```python
cleaned_text = response_text.strip()

if cleaned_text.startswith('```'):
    lines = cleaned_text.split('\n')
    if len(lines) > 1:
        cleaned_text = '\n'.join(lines[1:])
    if cleaned_text.endswith('```'):
        cleaned_text = cleaned_text.rsplit('```', 1)[0]
```

✅ Good - handles markdown code blocks from AI responses.

### 4.3 Question Validation

```python
for i, q in enumerate(question_list):
    if not isinstance(q, dict):
        raise ValueError(f"Question {i} is not a dictionary.")
    if 'question_text' not in q or 'choices' not in q or 'correct_index' not in q:
        raise ValueError(f"Question {i} missing required fields.")
```

**MISSING**: Validation that:
- `choices` is a list with exactly 4 items
- `correct_index` is 0-3
- `question_text` is non-empty

**RECOMMENDATION**: Add:
```python
if not isinstance(q.get('choices'), list) or len(q.get('choices', [])) != 4:
    raise ValueError(f"Question {i} must have exactly 4 choices.")
if q.get('correct_index') not in [0, 1, 2, 3]:
    raise ValueError(f"Question {i} has invalid correct_index.")
```

---

## 5. URLs Analysis (quizzes/urls.py)

```python
app_name = 'quizzes'

urlpatterns = [
    path('start/<int:module_id>/', views.start_quiz_view, name='start_quiz'),
    path('<int:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('history/', views.quiz_history_view, name='quiz_history'),
]
```

✅ Good - has app_name namespace.

---

## 6. Templates Analysis

### 6.1 quiz_form.html

**Purpose**: Display quiz questions for answering.

**Expected Features**:
- Question text display
- Radio buttons for 4 choices
- Submit button
- Timer (if any)?

### 6.2 quiz_results.html

**Purpose**: Show quiz results after completion.

**Expected Features**:
- Score display (X/5)
- Percentage
- Pass/Fail status
- Question review with correct answers
- Explanations (if provided)
- Retake button

### 6.3 quiz_history.html

**Purpose**: List all completed quizzes.

**Expected Features**:
- List of attempts with scores
- Average score display
- Total questions answered
- Filter/search (if any)?
- Pagination (MISSING - needs to be added)

---

## 7. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Module ownership check | ❌ | Add course__user filter in start_quiz_view |
| Quiz ownership check | ✅ | Filtered by user in quiz_detail_view |
| Free quiz (no credits) | ✅ | Intentional design |
| AI error handling | ✅ | Proper try/catch with logging |
| JSON validation | ⚠️ | Add choices/correct_index validation |
| Quiz history pagination | ❌ | Add pagination |
| Pass threshold (60%) | ✅ | Correctly implemented |
| Module locking integration | ✅ | passed field used by courses app |

---

## 8. Items for Removal/Deprecation

### NO REMOVALS NEEDED

The quizzes app is core functionality and doesn't have legacy exam dependencies.

### SHOULD UPDATE:
1. Add module ownership check in start_quiz_view
2. Add pagination to quiz_history_view
3. Strengthen JSON validation in utils.py

---

## 9. Recommended Improvements

### 9.1 High Priority (Before Production)

1. **Fix module ownership check**:
   ```python
   # In start_quiz_view
   module = get_object_or_404(Module, pk=module_id, course__user=request.user)
   ```

2. **Add pagination to quiz history**:
   ```python
   from django.core.paginator import Paginator
   
   paginator = Paginator(completed_quizzes, 20)
   quizzes = paginator.get_page(request.GET.get('page', 1))
   ```

3. **Strengthen question validation**:
   ```python
   if len(q.get('choices', [])) != 4:
       raise ValueError(...)
   if q.get('correct_index') not in [0, 1, 2, 3]:
       raise ValueError(...)
   ```

### 9.2 Medium Priority

1. Add quiz attempt archival (move old data to archive table)
2. Add quiz timer feature (optional)
3. Add "review mode" to see questions without answering

### 9.3 Low Priority (Nice to Have)

1. Add quiz sharing feature (share score on social)
2. Add difficulty progression (harder questions on retake)
3. Add topic-specific quiz generation
4. Add quiz leaderboard per module

---

## 10. Memory Optimization for 1GB VM

### Current Concern:
- questions_data and user_answers are JSONFields
- Each quiz attempt stores ~2.5KB of JSON
- 1000 users x 100 attempts = 250MB just for quiz data

### Recommendations:

1. **Data Archival Strategy**:
   ```python
   # Management command to archive old quizzes
   old_attempts = QuizAttempt.objects.filter(
       completed_at__lt=timezone.now() - timedelta(days=90)
   )
   # Move to archive table or delete questions_data
   ```

2. **Consider Question Sharing**:
   Instead of storing questions per attempt, store in shared QuizQuestion table:
   ```python
   class QuizQuestion(models.Model):
       module = models.ForeignKey(Module, ...)
       question_text = models.TextField()
       choices = models.JSONField()
       correct_index = models.IntegerField()
       # Reuse questions across attempts
   ```

3. **Lazy Loading**:
   In views, don't load questions_data unless needed:
   ```python
   quiz = QuizAttempt.objects.defer('questions_data').get(pk=quiz_id)
   ```

---

## 11. Feature Analysis: Analytics Dashboard

User mentioned wanting analytics. Current quiz data available:

### What's Tracked:
- Score per attempt
- Total questions per attempt
- Completion time
- Pass/fail status
- Module/subject association

### Possible Analytics:
1. **Student Performance Dashboard**:
   - Average score by subject
   - Improvement over time
   - Weak topics identification

2. **Subject Difficulty Analysis**:
   - Which modules have lowest pass rates
   - Common wrong answers

### Implementation Suggestion:
```python
# New analytics endpoint
def student_analytics_view(request):
    user_attempts = QuizAttempt.objects.filter(user=request.user, completed_at__isnull=False)
    
    by_subject = user_attempts.values('module__course__subject').annotate(
        avg_score=Avg('score'),
        total_attempts=Count('id'),
        pass_rate=Avg(Case(When(passed=True, then=1), default=0, output_field=FloatField()))
    )
    
    return render(request, 'quizzes/analytics.html', {'by_subject': by_subject})
```

---

**AUDIT COMPLETE FOR: quizzes App**
**Next App: exams (TO BE REMOVED)**
