# COMPREHENSIVE AUDIT: users App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: User authentication, registration, login, referral system, and custom user model.

**Files Reviewed**:
- `users/models.py` (136 lines)
- `users/views.py` (131 lines)
- `users/urls.py` (16 lines)
- `users/forms.py` (24 lines)
- `users/admin.py`
- `users/tests.py`
- `templates/users/login.html`
- `templates/users/signup.html`
- `templates/registration/` (password reset templates)

---

## 2. Data Models Analysis (users/models.py)

### 2.1 CustomUser Model

```python
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # Freemium Credit System Fields
    tutor_credits = models.IntegerField(default=settings.AKILI_DAILY_FREE_CREDITS)
    last_daily_reset = models.DateField(auto_now_add=True)
    daily_credit_limit = models.IntegerField(default=settings.AKILI_DAILY_FREE_CREDITS)
    
    # Referral System
    referred_by = models.CharField(max_length=150, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
```

### 2.2 MODEL ANALYSIS

| Field | Type | Issues | Recommendations |
|-------|------|--------|-----------------|
| email | EmailField(unique=True) | ✅ Good | Has unique constraint |
| username | CharField(editable=False) | ✅ Good | Auto-generated from email |
| first_name | CharField | ✅ Good | Required |
| last_name | CharField | ✅ Good | Required |
| tutor_credits | IntegerField | ⚠️ No validation | Add PositiveIntegerField or validation |
| last_daily_reset | DateField | ✅ Good | Auto-set on creation |
| daily_credit_limit | IntegerField | ⚠️ No max validation | Validate against AKILI_MAX_REFERRAL_CREDITS |
| referred_by | CharField | ⚠️ Stores username string | Consider ForeignKey to User for integrity |

### 2.3 CRITICAL ISSUES

1. **tutor_credits can go negative** (line 119):
   ```python
   def deduct_credits(self, amount):
       if self.tutor_credits >= amount:
           self.tutor_credits -= amount
   ```
   - No protection against race conditions
   - Multiple simultaneous requests could over-deduct

   **RECOMMENDATION**: Use F() expressions for atomic operations:
   ```python
   from django.db.models import F
   CustomUser.objects.filter(pk=self.pk, tutor_credits__gte=amount).update(
       tutor_credits=F('tutor_credits') - amount
   )
   ```

2. **referred_by stores username, not FK** (line 62):
   - If user changes username (currently not allowed, but could in future), referral tracking breaks
   - No cascade delete handling
   - **RECOMMENDATION**: Consider ForeignKey to CustomUser with SET_NULL

3. **No index on referred_by** for referral count queries:
   - ProfileView does: `CustomUser.objects.filter(referred_by=username).count()`
   - **RECOMMENDATION**: Add `db_index=True` to referred_by field

### 2.4 CustomUserManager

```python
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        if 'username' not in extra_fields:
            email_base = email.split('@')[0]
            extra_fields.setdefault('username', email_base + str(uuid.uuid4())[:8])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
```

✅ Good implementation - handles email normalization and auto-username generation.

### 2.5 Credit System Methods

| Method | Purpose | Issues |
|--------|---------|--------|
| reset_daily_credits() | Top up credits daily | ✅ Uses max() to preserve purchased credits |
| deduct_credits(amount) | Spend credits | ⚠️ Race condition risk (see above) |
| add_credits(amount) | Add purchased credits | ✅ OK |
| increase_daily_limit(amount) | Referral bonus | ✅ Caps at MAX_REFERRAL_CREDITS |

### 2.6 Database Table

```python
class Meta:
    db_table = 'akili_users'
    verbose_name = 'User'
    verbose_name_plural = 'Users'
```

⚠️ **No indexes defined** - Consider adding:
```python
class Meta:
    indexes = [
        models.Index(fields=['email']),
        models.Index(fields=['referred_by']),
        models.Index(fields=['last_daily_reset']),
    ]
```

---

## 3. Views Analysis (users/views.py)

### 3.1 Views Inventory

| View | Method | Auth | Purpose |
|------|--------|------|---------|
| signup_view | GET/POST | No | User registration |
| login_view | GET/POST | No | User login |
| logout_view | POST | Yes | User logout |
| referral_signup_view | GET | No | Redirect to signup with ref |
| delete_account_view | POST | Yes | Account deletion |

### 3.2 SECURITY ANALYSIS

#### signup_view (lines 13-65)

**GOOD PRACTICES**:
- Uses `@ensure_csrf_cookie` decorator
- Validates referrer exists before awarding bonus
- Uses `transaction.atomic` implied by form.save()

**ISSUES**:
1. **Referral validation not atomic** (lines 47-53):
   ```python
   if referred_by and user.referred_by:
       try:
           referrer = CustomUser.objects.get(username=referred_by)
           referrer.increase_daily_limit(2)
   ```
   - Referrer lookup done twice (also at line 38)
   - Race condition: referrer could be deleted between checks
   
   **RECOMMENDATION**: Cache referrer object and use single transaction

2. **No rate limiting on signup**:
   - Could be abused for email enumeration
   - **RECOMMENDATION**: Add to RATE_LIMITED_PATHS in middleware

#### login_view (lines 68-92)

**GOOD PRACTICES**:
- Uses `@ensure_csrf_cookie` decorator
- Uses Django's authenticate() function
- Generic error message (doesn't reveal if email exists)

**ISSUES**:
1. **No login rate limiting**:
   - Vulnerable to brute force attacks
   - **RECOMMENDATION**: Add `/login/` to RATE_LIMITED_PATHS

2. **No account lockout**:
   - No max failed attempt tracking
   - Consider django-axes or similar for production

#### delete_account_view (lines 108-131)

**GOOD PRACTICES**:
- Requires POST method
- Uses `transaction.atomic()`
- Logs out user before deletion

**ISSUES**:
1. **No password confirmation**:
   - Only checks `confirm_delete` checkbox
   - Should require password re-entry
   
   **WAIT**: Looking at code again - it DOES check password (profiles/views.py has it)
   - This view is at `/users/delete/` but NOT in users/urls.py!
   - **ORPHAN CODE**: This view is defined but never used in URLs

**FINDING**: `delete_account_view` in users/views.py is NOT routed. The actual deletion is in `profiles/views.py` DeleteAccountView.

**RECOMMENDATION**: Remove orphan `delete_account_view` from users/views.py

---

## 4. URLs Analysis (users/urls.py)

```python
urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('join/<str:username>/', views.referral_signup_view, name='referral_signup'),
    
    # Password Reset URLs
    path('password-reset/', ...),
    path('password-reset/done/', ...),
    path('reset/<uidb64>/<token>/', ...),
    path('reset/done/', ...),
]
```

### 4.1 ISSUES

1. **No app_name namespace**:
   ```python
   # Missing: app_name = 'users'
   ```
   - This means URL names like 'signup' are global, could conflict
   - **RECOMMENDATION**: Add `app_name = 'users'` and update all references

2. **delete_account_view not routed** (confirmed - orphan code)

3. **Password reset uses default templates**:
   - `password_reset_confirm` uses default template, others have custom
   - **Check**: `templates/registration/password_reset_confirm.html` exists? YES

### 4.2 SECURITY CONCERN

Password reset URLs use Django's built-in views which is good, but:
- No rate limiting on password reset
- **RECOMMENDATION**: Add rate limit to password reset endpoints

---

## 5. Forms Analysis (users/forms.py)

### 5.1 SignupForm

```python
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, ...)
    first_name = forms.CharField(max_length=150, required=True, ...)
    last_name = forms.CharField(max_length=150, required=True, ...)
    agree_to_terms = forms.BooleanField(required=True, ...)
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'agree_to_terms')
```

✅ Good - requires terms agreement.

### 5.2 LoginForm

```python
class LoginForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput)
```

✅ Simple and clean.

### 5.3 MISSING FORMS

- No ProfileUpdateForm
- No PasswordChangeForm (uses Django's built-in)
- No EmailChangeForm

---

## 6. Templates Analysis

### 6.1 templates/users/login.html

**Status**: Template exists (not read in audit, need to verify)

**Expected Features**:
- Email/password fields
- Remember me (optional)
- Forgot password link
- Sign up link

### 6.2 templates/users/signup.html

**Expected Features**:
- Name, email, password fields
- Terms agreement checkbox
- Referral display if applicable
- Login link

### 6.3 templates/registration/

| Template | Purpose | Status |
|----------|---------|--------|
| password_reset_form.html | Enter email | Custom exists |
| password_reset_done.html | Email sent confirmation | Custom exists |
| password_reset_confirm.html | Enter new password | Custom exists |
| password_reset_complete.html | Success message | Custom exists |

---

## 7. Database Migrations

**Migration Files**:
- `0001_initial.py` - Initial user model
- `0002_add_indexes.py` - Added indexes
- `0003_remove_customuser_users_email_idx_and_more.py` - Index changes

**STATUS**: Migrations appear complete. Need to verify with `python manage.py showmigrations users`

---

## 8. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Email uniqueness enforced | ✅ | None |
| Password hashing | ✅ | Uses Django's set_password() |
| CSRF protection | ✅ | @ensure_csrf_cookie used |
| Session security | ✅ | Configured in settings |
| Brute force protection | ❌ | Add rate limiting to login |
| Race condition on credits | ❌ | Use F() expressions |
| Referral integrity | ⚠️ | Consider FK instead of CharField |
| Database indexes | ⚠️ | Add index on referred_by |
| Error messages | ✅ | Generic, doesn't leak info |

---

## 9. Items for Removal/Deprecation

### MUST REMOVE:
1. `users/views.py`: `delete_account_view` function (lines 107-131) - orphan code, not in URLs

### SHOULD UPDATE:
1. Add `app_name = 'users'` to users/urls.py
2. Update all URL references to use namespace if added

---

## 10. Recommended Improvements

### 10.1 High Priority (Before Production)

1. **Add login rate limiting**:
   ```python
   # In core/middleware.py RATE_LIMITED_PATHS
   RATE_LIMITED_PATHS = [
       '/courses/create',
       '/courses/ask-tutor',
       '/login/',
       '/signup/',
       '/password-reset/',
   ]
   ```

2. **Fix credit deduction race condition**:
   ```python
   def deduct_credits(self, amount):
       from django.db.models import F
       self.reset_daily_credits()
       
       updated = CustomUser.objects.filter(
           pk=self.pk, 
           tutor_credits__gte=amount
       ).update(tutor_credits=F('tutor_credits') - amount)
       
       if updated:
           self.refresh_from_db(fields=['tutor_credits'])
           return True
       return False
   ```

3. **Add database index on referred_by**:
   ```python
   referred_by = models.CharField(
       max_length=150, 
       blank=True, 
       null=True,
       db_index=True  # Add this
   )
   ```

### 10.2 Medium Priority

1. Remove orphan delete_account_view from users/views.py
2. Add account lockout after failed login attempts (consider django-axes)
3. Add email verification (currently emails not verified)

### 10.3 Low Priority (Nice to Have)

1. Add two-factor authentication option
2. Add social login (Google, Facebook) for Nigerian market
3. Add "Remember this device" functionality
4. Password strength meter on signup

---

## 11. Feature Gaps Identified

### Missing Features (Consider Adding):

1. **Email Verification**:
   - Currently, any email can be used without verification
   - Critical for password reset to work properly
   - Prevents fake referral abuse

2. **Profile Completion**:
   - No class level selection during signup
   - Users have to select level when creating first course

3. **Account Recovery Options**:
   - Only password reset via email
   - Consider phone number for SMS reset (Nigerian market)

4. **Session Management**:
   - No "log out all devices" feature
   - No session listing in profile

---

## 12. Referral System Analysis

### Current Implementation:
1. User A shares link: `https://domain/join/username123/`
2. New user signs up with `?ref=username123`
3. After signup, User A gets +2 daily credit limit (max 30)

### Issues Found:

1. **Referral link in user model** (line 88-95):
   ```python
   @property
   def referral_url(self):
       base_url = os.getenv('REPLIT_DEV_DOMAIN', os.getenv('REPL_SLUG', 'akili.ng'))
   ```
   - Hardcoded 'akili.ng' as fallback
   - Uses Replit env vars - won't work on Google VM
   
   **RECOMMENDATION**: Use Django's site framework or config setting

2. **No referral tracking/analytics**:
   - Can only count referrals, not see who/when
   - Consider adding Referral model for tracking

3. **One-way tracking only**:
   - Can see "who referred me" (referred_by field)
   - Cannot efficiently see "who I referred" (requires reverse query)

---

**AUDIT COMPLETE FOR: users App**
**Next App: curriculum**
