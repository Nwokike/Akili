// Akili - Main JavaScript File

// PWA Install Prompt
let deferredPrompt;
const installButton = document.getElementById('install-button');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  
  if (installButton) {
    installButton.classList.remove('hidden');
  }
});

if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('PWA installed');
    }
    
    deferredPrompt = null;
    installButton.classList.add('hidden');
  });
}

// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/pwa/serviceworker.js')
      .then(registration => {
        console.log('Service Worker registered successfully:', registration.scope);
      })
      .catch(error => {
        console.log('Service Worker registration failed:', error);
      });
  });
}

// Mobile Menu Toggle (if needed for dropdowns)
function toggleMobileMenu(id) {
  const menu = document.getElementById(id);
  if (menu) {
    menu.classList.toggle('hidden');
  }
}

// Copy Referral Link (EXISTING FUNCTION - ALREADY WORKS)
function copyReferralLink(link) {
  // Use the link value from the profile template's input field
  const referralInput = document.getElementById('referralLinkInput');
  if (referralInput) {
    navigator.clipboard.writeText(referralInput.value).then(() => {
      showToast('Referral link copied!');
    }).catch(err => {
      console.error('Failed to copy:', err);
      showToast('Copy failed. Check console.', 'error');
    });
  }
}

// Toast Notification (EXISTING FUNCTION)
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-20 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg z-50 ${
    type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
  } text-white font-semibold`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Confirm Delete Actions (UPDATED TO SECURE TWO-STEP PROCESS)
function showDeleteConfirmation() {
    // 1. Initial Confirmation
    const isConfirmed = confirm("WARNING: Are you absolutely sure you want to permanently delete your account? This action cannot be reversed.");

    if (isConfirmed) {
        // 2. Secondary Confirmation (for safety)
        const isDoubleConfirmed = confirm("Final Check: Click OK to confirm permanent account deletion.");

        if (isDoubleConfirmed) {
            // 3. Submit the hidden form defined in profile.html
            document.getElementById('deleteAccountForm').submit();
        } else {
            alert("Account deletion cancelled.");
        }
    }
}
// Removed old confirmDelete(message) function as it's replaced by showDeleteConfirmation()

// Auto-dismiss Django Messages
document.addEventListener('DOMContentLoaded', () => {
  const messages = document.querySelectorAll('.django-message');
  messages.forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 300);
    }, 5000);
  });
});

// Credit Purchase Modal
function openCreditModal() {
  const modal = document.getElementById('credit-modal');
  if (modal) {
    modal.classList.remove('hidden');
  }
}

function closeCreditModal() {
  const modal = document.getElementById('credit-modal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Close modal on outside click
window.addEventListener('click', (e) => {
  const modal = document.getElementById('credit-modal');
  if (modal && e.target === modal) {
    closeCreditModal();
  }
});