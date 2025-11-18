import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse  # Required for generating the URL
from .models import Payment

@login_required
def initialize_payment(request):
    """
    Initializes a transaction with Paystack and redirects the user to the payment page.
    """
    PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    
    if not PAYSTACK_SECRET_KEY:
        messages.error(
            request, 
            "Payment system is not configured. Please contact support."
        )
        return render(request, "payments/initialize.html")
    
    if request.method == "POST":
        try:
            # Paystack expects amount in kobo (multiply by 100)
            amount = int(request.POST.get("amount")) * 100
            headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
            
            # --- CALLBACK URL LOGIC ---
            # 1. Generate the relative path using the namespace 'payments' defined in urls.py
            verify_path = reverse('payments:verify_payment')
            
            # 2. Build the absolute URL (e.g., https://yourdomain.com/payments/verify/)
            callback_url = request.build_absolute_uri(verify_path)
            
            data = {
                "email": request.user.email,
                "amount": amount,
                "callback_url": callback_url  # Tells Paystack where to return the user
            }
            
            # 3. Call Paystack API
            res = requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers=headers, 
                json=data,
                timeout=15  # Slightly increased timeout for safety
            )
            res.raise_for_status()
            response_data = res.json()

            if response_data.get("status"):
                # 4. Create local payment record before redirecting
                Payment.objects.create(
                    user=request.user,
                    reference=response_data["data"]["reference"],
                    amount=amount / 100  # Store actual currency amount, not kobo
                )
                messages.success(request, "Payment initialized successfully! Redirecting to payment gateway...")
                return redirect(response_data["data"]["authorization_url"])
            else:
                error_message = response_data.get("message", "Payment initialization failed.")
                messages.error(request, f"Payment failed: {error_message}")
                
        except requests.exceptions.RequestException as e:
            messages.error(request, "Payment service error: Unable to connect to payment gateway. Please try again later.")
        except (KeyError, ValueError) as e:
            messages.error(request, "Invalid payment data. Please try again.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
    
    return render(request, "payments/initialize.html")


@csrf_exempt
def verify_payment(request):
    """
    Callback view that Paystack redirects to after payment.
    Verifies the transaction status and rewards credits.
    """
    PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    
    if not PAYSTACK_SECRET_KEY:
        messages.error(request, "Payment system is not configured.")
        return redirect("dashboard")
    
    reference = request.GET.get("reference")
    
    if not reference:
        messages.error(request, "Invalid payment reference.")
        return redirect("dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        
        # 1. Verify transaction with Paystack
        res = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}", 
            headers=headers,
            timeout=15
        )
        res.raise_for_status()
        data = res.json()

        # 2. Retrieve local record
        payment = Payment.objects.get(reference=reference)
        
        # 3. Check status and prevent double-crediting
        if data.get("data", {}).get("status") == "success" and not payment.verified:
            payment.verified = True
            payment.save()
            
            # 4. Calculate Credits
            amount = payment.amount
            credits_to_add = 0
            
            if amount >= 2000:
                credits_to_add = 300
            elif amount >= 1000:
                credits_to_add = 120
            elif amount >= 500:
                credits_to_add = 50
            else:
                credits_to_add = int(amount / 10)
            
            # 5. Update User Balance
            user = payment.user
            user.tutor_credits += credits_to_add
            user.save()
            
            messages.success(request, f"Payment verified successfully! {credits_to_add} credits added to your account.")
            
        elif payment.verified:
            messages.info(request, "This payment has already been processed.")
        else:
            messages.error(request, "Payment verification failed or was not successful.")
            
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
    except requests.exceptions.RequestException:
        messages.error(request, "Unable to connect to Paystack for verification.")
    except Exception as e:
        messages.error(request, "An error occurred during payment verification.")

    return redirect("dashboard")
