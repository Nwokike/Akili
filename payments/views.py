import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment
from django.views.decorators.csrf import csrf_exempt


@login_required
def initialize_payment(request):
    PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    
    if not PAYSTACK_SECRET_KEY:
        messages.error(
            request, 
            "Payment system is not configured. Please add your PAYSTACK_SECRET_KEY to the Secrets (environment variables) to enable payments."
        )
        return render(request, "payments/initialize.html")
    
    if request.method == "POST":
        try:
            amount = int(request.POST.get("amount")) * 100
            headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
            data = {
                "email": request.user.email,
                "amount": amount,
            }
            
            res = requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers=headers, 
                json=data,
                timeout=10
            )
            res.raise_for_status()
            response_data = res.json()

            if response_data.get("status"):
                Payment.objects.create(
                    user=request.user,
                    reference=response_data["data"]["reference"],
                    amount=amount / 100
                )
                messages.success(request, "Payment initialized successfully! Redirecting to payment gateway...")
                return redirect(response_data["data"]["authorization_url"])
            else:
                error_message = response_data.get("message", "Payment initialization failed.")
                messages.error(request, f"Payment failed: {error_message}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Payment service error: Unable to connect to payment gateway. Please try again later.")
        except (KeyError, ValueError) as e:
            messages.error(request, "Invalid payment data. Please try again.")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
    
    return render(request, "payments/initialize.html")


@csrf_exempt
def verify_payment(request):
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
        res = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}", 
            headers=headers,
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        payment = Payment.objects.get(reference=reference)
        if data.get("data", {}).get("status") == "success" and not payment.verified:
            payment.verified = True
            payment.save()
            
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
            
            user = payment.user
            user.tutor_credits += credits_to_add
            user.save()
            
            messages.success(request, f"Payment verified successfully! {credits_to_add} credits added to your account.")
        elif payment.verified:
            messages.info(request, "This payment has already been processed.")
        else:
            messages.error(request, "Payment verification failed.")
    except Payment.DoesNotExist:
        messages.error(request, "Payment not found.")
    except requests.exceptions.RequestException as e:
        messages.error(request, "Unable to verify payment. Please contact support.")
    except Exception as e:
        messages.error(request, "An error occurred during payment verification.")

    return redirect("dashboard")
