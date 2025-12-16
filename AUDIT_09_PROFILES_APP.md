# COMPREHENSIVE AUDIT: profiles App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: User profile management including profile viewing, editing, password changes, and account deletion.

**Files Reviewed**:
- `profiles/views.py` (194 lines)
- `profiles/urls.py` (10 lines)
- `profiles/admin.py`
- `profiles/tests.py`
- Templates in `profiles/templates/profiles/`

---

## 2. Data Models Analysis

### NO DEDICATED MODELS

The profiles app uses the `CustomUser` model from the `users` app.

**OBSERVATION**: No separate Profile model means:
- No profile picture storage
- No bio/about text
- No social links
- No additional preferences

This is fine for MVP, but consider future expansion.

---

## 3. Views Analysis (profiles/views.py)

### 3.1 Views Inventory

| View | Class/Function | Auth | Purpose |
|------|----------------|------|---------|
| ProfileView | Class | Yes | View profile + stats |
| EditProfileView | Class | Yes | Edit name/email |
| ChangePasswordView | Class | Yes | Change password |
| DeleteAccountView | Class | Yes | Delete account |

### 3.2 ProfileView Analysis (lines 13-70)

```python
class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        
        # Stats
        courses_count = Course.objects.filter(user=user).count()
        quizzes_count = QuizAttempt.objects.filter(user=user, completed_at__isnull=False).count()
        exams_count = Exam.objects.filter(user=user, completed_at__isnull=False).count()  # LEGACY
        
        # Referral stats
        referrals_count = CustomUser.objects.filter(referred_by=user.username).count()
```

**LEGACY REFERENCE**:
```python
from exams.models import Exam
exams_count = Exam.objects.filter(user=user, completed_at__isnull=False).count()
```

**ACTION REQUIRED**: Remove exam-related imports and stats after exams app deletion.

### 3.3 EditProfileView Analysis (lines 73-108)

```python
class EditProfileView(LoginRequiredMixin, View):
    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validation
        if not first_name or not last_name:
            messages.error(request, 'First name and last name are required.')
            return redirect('profiles:edit')
        
        if email != request.user.email:
            # Check if email is taken
            if CustomUser.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'This email is already in use.')
                return redirect('profiles:edit')
            
            request.user.email = email
```

**GOOD PRACTICES**:
- Validates required fields
- Checks email uniqueness before update
- Uses strip() on inputs

**MISSING**:
- No email format validation
- No XSS protection on display (template responsibility)

**RECOMMENDATION**:
```python
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

if email:
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, 'Please enter a valid email address.')
        return redirect('profiles:edit')
```

### 3.4 ChangePasswordView Analysis (lines 111-148)

```python
class ChangePasswordView(LoginRequiredMixin, View):
    def post(self, request):
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('profiles:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('profiles:change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('profiles:change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
```

**GOOD PRACTICES**:
- Verifies current password
- Checks password match
- Minimum length requirement
- Uses set_password() (proper hashing)
- Updates session hash (stays logged in)

**MISSING**:
- No complexity requirements (uppercase, number, special char)
- No common password check

**RECOMMENDATION** for stronger security:
```python
from django.contrib.auth.password_validation import validate_password

try:
    validate_password(new_password, request.user)
except ValidationError as e:
    for error in e.messages:
        messages.error(request, error)
    return redirect('profiles:change_password')
```

### 3.5 DeleteAccountView Analysis (lines 151-194)

```python
class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request):
        password = request.POST.get('password', '')
        confirm_delete = request.POST.get('confirm_delete', '')
        
        if confirm_delete != 'DELETE':
            messages.error(request, 'Please type DELETE to confirm.')
            return redirect('profiles:delete_account')
        
        if not request.user.check_password(password):
            messages.error(request, 'Password is incorrect.')
            return redirect('profiles:delete_account')
        
        with transaction.atomic():
            # Delete related data
            Course.objects.filter(user=request.user).delete()
            QuizAttempt.objects.filter(user=request.user).delete()
            Exam.objects.filter(user=request.user).delete()  # LEGACY
            
            # Log out and delete user
            logout(request)
            request.user.delete()
```

**GOOD PRACTICES**:
- Requires password confirmation
- Requires typing "DELETE"
- Uses transaction.atomic()
- Logs out before deletion

**LEGACY REFERENCE**:
```python
Exam.objects.filter(user=request.user).delete()  # LEGACY
```

**ACTION REQUIRED**: Remove exam deletion after exams app removal.

**CASCADE DELETE NOTE**: With proper ForeignKey cascade, explicit deletion may not be needed. Current explicit deletion is safer but redundant.

---

## 4. URLs Analysis (profiles/urls.py)

```python
app_name = 'profiles'

urlpatterns = [
    path('', views.ProfileView.as_view(), name='profile'),
    path('edit/', views.EditProfileView.as_view(), name='edit'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('delete/', views.DeleteAccountView.as_view(), name='delete_account'),
]
```

✅ Good - has app_name namespace.

---

## 5. Templates Analysis

### Expected Templates:

| Template | Purpose |
|----------|---------|
| profiles/profile.html | Main profile view |
| profiles/edit.html | Edit profile form |
| profiles/change_password.html | Password change form |
| profiles/delete_account.html | Account deletion confirmation |

**VERIFY**: Check these templates exist and are styled consistently.

---

## 6. Duplicate Code Analysis

### DUPLICATE: core/views.py has profile_view

```python
# core/views.py lines 57-61
@login_required
def profile_view(request):
    return redirect('profiles:profile')
```

This is just a redirect, but it's orphan code since `/profile/` is not in core URLs.

**RECOMMENDATION**: Remove from core/views.py.

---

## 7. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Password verification | ✅ | Current password required for changes |
| Email uniqueness | ✅ | Checked before update |
| Account deletion safety | ✅ | Password + "DELETE" confirmation |
| Session handling | ✅ | update_session_auth_hash used |
| Legacy exam references | ❌ | Remove after exams app deletion |
| Email validation | ⚠️ | Add format validation |
| Password strength | ⚠️ | Use Django validators |
| CSRF protection | ✅ | Django default |

---

## 8. Items for Removal/Deprecation

### MUST REMOVE (with exams app):
1. `profiles/views.py`: `from exams.models import Exam` import
2. `profiles/views.py`: `exams_count` calculation in ProfileView
3. `profiles/views.py`: `Exam.objects.filter(...).delete()` in DeleteAccountView

### SHOULD REMOVE:
1. `core/views.py`: `profile_view` function (orphan redirect)

---

## 9. Recommended Improvements

### 9.1 High Priority (Before Production)

1. **Remove exam references** after exams app deletion

2. **Add email format validation**:
   ```python
   from django.core.validators import validate_email
   ```

3. **Use Django password validators**:
   ```python
   from django.contrib.auth.password_validation import validate_password
   ```

### 9.2 Medium Priority

1. Add profile picture upload
2. Add bio/about field
3. Add class level preference
4. Add notification preferences
5. Add "Download my data" feature (GDPR-like)

### 9.3 Low Priority (Nice to Have)

1. Add social login linking
2. Add two-factor authentication toggle
3. Add session management (view active sessions)
4. Add activity log (recent actions)

---

## 10. Referral URL Generation

### Current Implementation (in users/models.py):

```python
@property
def referral_url(self):
    base_url = os.getenv('REPLIT_DEV_DOMAIN', os.getenv('REPL_SLUG', 'akili.ng'))
    if 'replit' in base_url.lower():
        return f"https://{base_url}/join/{self.username}"
    return f"https://{base_url}/join/{self.username}"
```

**ISSUE for Production**:
- Hardcoded fallback to 'akili.ng'
- Uses Replit env vars - won't work on Google VM

**RECOMMENDATION**: Use Django Sites framework or settings:
```python
# settings.py
SITE_URL = os.getenv('SITE_URL', 'https://akili.ng')

# models.py
@property
def referral_url(self):
    from django.conf import settings
    return f"{settings.SITE_URL}/join/{self.username}"
```

---

## 11. Security Considerations

### 11.1 Rate Limiting Needed

Currently not in RATE_LIMITED_PATHS:
- `/profiles/change-password/` - Should rate limit to prevent brute force
- `/profiles/edit/` - Lower priority but consider

**RECOMMENDATION**:
```python
# core/middleware.py RATE_LIMITED_PATHS
'/profiles/change-password/',
'/profiles/delete/',
```

### 11.2 Account Lockout

No lockout after failed password attempts in ChangePasswordView.

**RECOMMENDATION**: Track failed attempts and lock after 5 failures.

---

**AUDIT COMPLETE FOR: profiles App**
**Next App: admin_syllabus**
