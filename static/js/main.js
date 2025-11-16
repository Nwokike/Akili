// Akili - Main JavaScript File

// ---------------------------------------------
// DARK MODE TOGGLE
// ---------------------------------------------
function toggleDarkMode() {
  const html = document.documentElement;
  const isDark = html.classList.contains('dark');
  
  if (isDark) {
    html.classList.remove('dark');
    localStorage.setItem('darkMode', 'false');
  } else {
    html.classList.add('dark');
    localStorage.setItem('darkMode', 'true');
  }
}

// Initialize dark mode toggle button
document.addEventListener('DOMContentLoaded', () => {
  const darkModeToggle = document.getElementById('darkModeToggle');
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', toggleDarkMode);
  }
  
  // Header shrink on scroll
  const header = document.getElementById('main-header');
  const headerLogo = document.getElementById('header-logo');
  const headerSpacer = document.getElementById('header-spacer');
  
  if (header && headerLogo) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
        headerLogo.classList.remove('h-12');
        headerLogo.classList.add('h-8');
        if (headerSpacer) {
          headerSpacer.classList.remove('h-16');
          headerSpacer.classList.add('h-12');
        }
      } else {
        header.classList.remove('scrolled');
        headerLogo.classList.remove('h-8');
        headerLogo.classList.add('h-12');
        if (headerSpacer) {
          headerSpacer.classList.remove('h-12');
          headerSpacer.classList.add('h-16');
        }
      }
    });
  }
});

// PWA Install Prompt
let deferredPrompt;
const installButton = document.getElementById('install-button');

// --- PWA LOGIC ---
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

// ---------------------------------------------
// CORE UTILITIES (MUST BE FIRST)
// ---------------------------------------------

// Toast Notification (MOVED TO TOP)
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

// Copy Referral Link (FINAL ROBUST VERSION)
function copyReferralLink() { 
    if (typeof showToast !== 'function') { 
        console.error('showToast utility is missing.');
        return;
    }

    // FINAL ID FIX: Search all possible input IDs used in the project
    const referralInput = document.getElementById('referralLinkInput') || 
                          document.getElementById('referral-input') ||
                          document.getElementById('profile-referral-input'); 
    
    if (!referralInput) {
        showToast('Error: Referral input field not found.', 'error');
        return;
    }
    
    // 1. Attempt the modern Clipboard API
    navigator.clipboard.writeText(referralInput.value)
        .then(() => {
            showToast('Referral link copied!');
        })
        .catch(err => {
            // 2. Fallback to older document.execCommand('copy')
            try {
                // To use execCommand, you must first select the text
                referralInput.select();
                referralInput.setSelectionRange(0, 99999); // For mobile compatibility
                document.execCommand('copy'); 
                showToast('Referral link copied (using fallback)!');
            } catch (fallbackErr) {
                console.error('Failed to copy using all methods:', fallbackErr);
                showToast('Copy failed. Please copy manually.', 'error');
            }
        });
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
// ---------------------------------------------
// END CORE UTILITIES
// ---------------------------------------------


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