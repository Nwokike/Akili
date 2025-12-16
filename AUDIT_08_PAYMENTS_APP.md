# COMPREHENSIVE AUDIT: payments App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: Paystack integration for credit purchases. Supports multiple credit packages with Nigerian Naira pricing.

**Files Reviewed**:
- `payments/models.py` (62 lines)
- `payments/views.py` (188 lines)
- `payments/urls.py` (11 lines)
- `payments/admin.py`
- `payments/tests.py`
- Templates in `payments/templates/payments/`

---

## 2. Data Models Analysis (payments/models.py)

### 2.1 CreditPackage Model

```python
class CreditPackage(models.Model):
    name = models.CharField(max_length=100)
    credits = models.IntegerField()
    price_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    is_popular = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

✅ Good structure for flexible package management.

**Expected Packages** (from README):
| Name | Credits | Price (NGN) |
|------|---------|-------------|
| Starter Pack | 10 | ₦500 |
| Value Pack | 50 | ₦2,000 |
| Super Pack | 150 | ₦5,000 |
| Ultimate Pack | 500 | ₦12,000 |

### 2.2 PaymentTransaction Model

```python
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('ABANDONED', 'Abandoned'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    package = models.ForeignKey(CreditPackage, null=True, ...)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    paystack_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    credits_added = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
```

✅ Comprehensive transaction tracking.

### 2.3 MODEL ANALYSIS

| Field | Type | Issues | Notes |
|-------|------|--------|-------|
| reference | CharField(unique=True) | ✅ Good | Prevents duplicates |
| paystack_reference | CharField | ✅ Good | Links to Paystack |
| status | CharField | ✅ Good | Clear states |
| credits_added | IntegerField | ✅ Good | Audit trail |
| metadata | JSONField | ✅ Good | For debug info |

### 2.4 Missing Fields (Consider Adding)

```python
ip_address = models.GenericIPAddressField(null=True)  # For fraud detection
user_agent = models.TextField(blank=True)  # Browser info
```

---

## 3. Views Analysis (payments/views.py)

### 3.1 Views Inventory

| View | Function | Auth | Purpose |
|------|----------|------|---------|
| buy_credits_view | GET | Yes | Display packages |
| initiate_payment | POST | Yes | Start Paystack payment |
| verify_payment | GET | Yes | Verify & credit user |
| payment_history | GET | Yes | Transaction list |

### 3.2 CRITICAL SECURITY ANALYSIS

#### initiate_payment (lines 30-85)

```python
@login_required
def initiate_payment(request):
    if request.method != 'POST':
        return redirect('payments:buy_credits')
    
    package_id = request.POST.get('package_id')
    package = get_object_or_404(CreditPackage, pk=package_id, is_active=True)
    
    reference = f"AKILI-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    # Create transaction record
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        package=package,
        amount=package.price_ngn,
        reference=reference,
        status='PENDING'
    )
    
    # Initialize Paystack
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'email': request.user.email,
        'amount': int(package.price_ngn * 100),  # Convert to kobo
        'reference': reference,
        'callback_url': request.build_absolute_uri(reverse('payments:verify_payment')),
    }
    
    response = requests.post(
        'https://api.paystack.co/transaction/initialize',
        headers=headers,
        json=payload,
        timeout=30
    )
```

**GOOD PRACTICES**:
- CSRF protected (Django default)
- Reference includes user ID and timestamp
- Transaction created BEFORE Paystack call
- Timeout on external request (30s)
- Amount converted to kobo correctly

**ISSUES**:
1. **Paystack secret key exposure risk**:
   ```python
   'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
   ```
   - If settings.PAYSTACK_SECRET_KEY is empty, auth will fail
   - No check for key existence

   **RECOMMENDATION**: Add validation:
   ```python
   if not settings.PAYSTACK_SECRET_KEY:
       messages.error(request, 'Payment system not configured')
       return redirect('payments:buy_credits')
   ```

2. **No idempotency**:
   - User could double-submit form
   - **RECOMMENDATION**: Add idempotency key or disable button on submit

#### verify_payment (lines 88-150)

```python
@login_required
def verify_payment(request):
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Invalid payment reference')
        return redirect('payments:buy_credits')
    
    # Get transaction from DB
    try:
        transaction = PaymentTransaction.objects.get(reference=reference, user=request.user)
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Transaction not found')
        return redirect('payments:buy_credits')
    
    # Already processed?
    if transaction.status == 'SUCCESS':
        messages.info(request, 'This payment has already been processed')
        return redirect('payments:payment_history')
    
    # Verify with Paystack
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    
    response = requests.get(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers=headers,
        timeout=30
    )
    
    data = response.json()
    
    if data.get('status') and data.get('data', {}).get('status') == 'success':
        # Credit user
        with transaction.atomic():
            transaction.status = 'SUCCESS'
            transaction.paystack_reference = data['data'].get('reference', '')
            transaction.credits_added = transaction.package.credits
            transaction.completed_at = timezone.now()
            transaction.save()
            
            request.user.add_credits(transaction.package.credits)
```

**GOOD PRACTICES**:
- Checks transaction belongs to user
- Checks if already processed
- Uses transaction.atomic() for crediting
- Saves Paystack reference

**CRITICAL ISSUE: Double-credit vulnerability**:
```python
if transaction.status == 'SUCCESS':
    messages.info(request, 'This payment has already been processed')
    return redirect('payments:payment_history')
```

If verify_payment is called twice simultaneously:
1. Request 1: Gets transaction, status is PENDING
2. Request 2: Gets transaction, status is PENDING
3. Request 1: Verifies with Paystack, credits user
4. Request 2: Verifies with Paystack, credits user AGAIN!

**RECOMMENDATION**: Use select_for_update():
```python
with transaction.atomic():
    try:
        txn = PaymentTransaction.objects.select_for_update().get(
            reference=reference, 
            user=request.user,
            status='PENDING'  # Only get if still pending
        )
    except PaymentTransaction.DoesNotExist:
        messages.info(request, 'Payment already processed or not found')
        return redirect('payments:payment_history')
    
    # Now verify and credit...
```

---

## 4. URLs Analysis (payments/urls.py)

```python
app_name = 'payments'

urlpatterns = [
    path('buy/', views.buy_credits_view, name='buy_credits'),
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('history/', views.payment_history, name='payment_history'),
]
```

✅ Good - has app_name namespace.

---

## 5. Paystack Integration Analysis

### 5.1 API Endpoints Used

| Endpoint | Purpose | Location |
|----------|---------|----------|
| `/transaction/initialize` | Start payment | initiate_payment |
| `/transaction/verify/{ref}` | Verify payment | verify_payment |

### 5.2 Webhook (MISSING!)

**CRITICAL**: No Paystack webhook handler!

Paystack sends webhooks for:
- Successful payments
- Failed payments
- Disputes/chargebacks

Without webhook:
- If user closes browser after payment, credits may not be added
- No way to handle disputes
- No real-time notification

**RECOMMENDATION**: Add webhook handler:
```python
# payments/views.py
import hmac
import hashlib

@csrf_exempt
def paystack_webhook(request):
    payload = request.body
    signature = request.headers.get('X-Paystack-Signature')
    
    # Verify signature
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    if signature != computed:
        return HttpResponse(status=400)
    
    data = json.loads(payload)
    event = data.get('event')
    
    if event == 'charge.success':
        reference = data['data']['reference']
        # Process payment...
    
    return HttpResponse(status=200)
```

### 5.3 Required Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| PAYSTACK_SECRET_KEY | YES | API secret key |
| PAYSTACK_PUBLIC_KEY | NO | For frontend (not currently used) |

---

## 6. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Secret key validation | ❌ | Add check before API call |
| Double-credit prevention | ❌ | Add select_for_update() |
| Webhook handler | ❌ | Implement webhook |
| Transaction logging | ⚠️ | Add more detailed logging |
| Error handling | ⚠️ | Handle Paystack API errors better |
| Idempotency | ⚠️ | Prevent double-submit |
| Amount verification | ✅ | Matches package price |
| User verification | ✅ | Transaction linked to user |

---

## 7. Items for Removal/Deprecation

### NO REMOVALS NEEDED

Payments app is essential for monetization.

---

## 8. Recommended Improvements

### 8.1 Critical (Before Production)

1. **Fix double-credit vulnerability**:
   ```python
   with transaction.atomic():
       txn = PaymentTransaction.objects.select_for_update().get(
           reference=reference,
           user=request.user,
           status='PENDING'
       )
   ```

2. **Add Paystack webhook**:
   - Create webhook view
   - Add URL pattern
   - Register webhook URL in Paystack dashboard

3. **Add secret key validation**:
   ```python
   if not getattr(settings, 'PAYSTACK_SECRET_KEY', None):
       logger.error("PAYSTACK_SECRET_KEY not configured")
       messages.error(request, 'Payment system unavailable')
       return redirect('dashboard')
   ```

### 8.2 High Priority

1. Add payment retry mechanism for failed API calls
2. Add detailed logging for debugging
3. Add IP address tracking for fraud detection
4. Add email receipt after successful payment

### 8.3 Medium Priority

1. Add payment receipt download (PDF)
2. Add refund functionality (admin)
3. Add subscription/recurring payments option
4. Add promotional codes/discounts

---

## 9. Nigerian Market Considerations

### 9.1 Pricing Strategy

Current packages (from README):
- Starter: ₦500 for 10 credits (₦50/credit)
- Value: ₦2,000 for 50 credits (₦40/credit)
- Super: ₦5,000 for 150 credits (₦33/credit)
- Ultimate: ₦12,000 for 500 credits (₦24/credit)

**GOOD**: Progressive discounts for larger packages.

### 9.2 Payment Methods

Paystack supports:
- Card payments
- Bank transfers
- USSD
- Mobile money

Currently only using card initialization. Consider:
- Adding bank transfer option
- Adding USSD for low-data users

---

## 10. Test Mode vs Live Mode

### Environment Detection

Need to ensure:
- Test keys used in development
- Live keys used in production

**RECOMMENDATION**: Add to settings:
```python
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_IS_TEST = os.getenv('PAYSTACK_IS_TEST', 'true').lower() == 'true'
```

---

## 11. Error Handling Improvements

Current error handling is minimal. Add:

```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    logger.error("Paystack timeout")
    messages.error(request, 'Payment service is slow. Please try again.')
    return redirect('payments:buy_credits')
except requests.RequestException as e:
    logger.error(f"Paystack error: {e}")
    messages.error(request, 'Payment service unavailable. Please try later.')
    return redirect('payments:buy_credits')
```

---

**AUDIT COMPLETE FOR: payments App**
**Next App: profiles**
