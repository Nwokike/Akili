import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment
from django.views.decorators.csrf import csrf_exempt


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


@login_required
def initialize_payment(request):
    if request.method == "POST":
        amount = int(request.POST.get("amount")) * 100  # Paystack uses kobo
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        data = {
            "email": request.user.email,
            "amount": amount,
        }
        res = requests.post("https://api.paystack.co/transaction/initialize",
                            headers=headers, json=data)
        response_data = res.json()

        if response_data["status"]:
            Payment.objects.create(
                user=request.user,
                reference=response_data["data"]["reference"],
                amount=amount / 100
            )
            return redirect(response_data["data"]["authorization_url"])
        else:
            messages.error(request, "Payment initialization failed.")
    return render(request, "payments/initialize.html")


@csrf_exempt
def verify_payment(request):
    reference = request.GET.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    data = res.json()

    try:
        payment = Payment.objects.get(reference=reference)
        if data["data"]["status"] == "success" and not payment.verified:
            payment.verified = True
            payment.save()
            
            # Allocate credits based on amount paid
            amount = payment.amount
            credits_to_add = 0
            
            # Map payment amounts to credits
            if amount >= 2000:
                credits_to_add = 300  # Premium package
            elif amount >= 1000:
                credits_to_add = 120  # Standard package
            elif amount >= 500:
                credits_to_add = 50   # Starter package
            else:
                credits_to_add = int(amount / 10)  # 10 Naira per credit as fallback
            
            # Add credits to user account
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

    return redirect("dashboard")
