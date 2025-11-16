// Akili - Main JavaScript File

// ---------------------------------------------
// CORE UTILITIES
// ---------------------------------------------

/**
 * Shows a toast notification at the bottom of the screen.
 * @param {string} message The message to display.
 * @param {string} type 'success', 'error', or 'info'.
 */
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  let bgColor = 'bg-blue-500'; // Default to info
  if (type === 'success') bgColor = 'bg-green-500';
  if (type === 'error') bgColor = 'bg-red-500';
  
  // z-[110] is higher than the loading overlay (z-[100])
  toast.className = `fixed bottom-0 left-1/2 transform -translate-x-1/2 mb-5 px-6 py-3 rounded-lg shadow-lg z-[110] ${bgColor} text-white font-semibold transition-all duration-300 opacity-0 -translate-y-5`;
  toast.textContent = message;
  
  document.body.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translate(-50%, 0)';
  }, 10);

  // Animate out
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translate(-50%, 20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * Copies the referral link to the clipboard using the most robust method.
 */
function copyReferralLink() { 
    if (typeof showToast !== 'function') { 
        console.error('showToast utility is missing.');
        return;
    }

    const referralInput = document.getElementById('referralLinkInput') || 
                          document.getElementById('referral-input') ||
                          document.getElementById('profile-referral-input'); 
    
    if (!referralInput) {
        showToast('Error: Referral input field not found.', 'error');
        return;
    }
    
    // 1. Attempt the modern Clipboard API (Best for HTTPS)
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(referralInput.value)
        .then(() => {
            showToast('Referral link copied!');
        })
        .catch(err => {
            console.warn('Modern clipboard failed, trying fallback.', err);
            fallbackCopy(referralInput);
        });
    } else {
      // 2. Fallback for HTTP or older browsers
      fallbackCopy(referralInput);
    }
}

/**
 * Fallback copy method for older browsers or insecure contexts.
 * @param {HTMLInputElement} inputElement The input to copy from.
 */
function fallbackCopy(inputElement) {
    try {
        inputElement.select();
        inputElement.setSelectionRange(0, 99999); // For mobile compatibility
        
        const successful = document.execCommand('copy');
        
        if (successful) {
            showToast('Referral link copied!');
        } else {
            showToast('Copy failed. Please copy manually.', 'error');
        }
    } catch (err) {
        console.error('Fallback copy failed:', err);
        showToast('Copy failed. Please copy manually.', 'error');
    }
}

// ---------------------------------------------
// LOADING SPINNER FUNCTIONS
// ---------------------------------------------

/**
 * Shows the fullscreen loading spinner.
 */
function showSpinner() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
  }
}

/**
 * Hides the fullscreen loading spinner.
 */
function hideSpinner() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
  }
}

// ---------------------------------------------
// MODAL FUNCTIONS (Credit & Delete)
// ---------------------------------------------

// Credit Purchase Modal
function openCreditModal() {
    const modal = document.getElementById('credit-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex'); // Use flex for centering
    }
}

function closeCreditModal(event) {
    const modal = document.getElementById('credit-modal');
    // Check if the click is on the overlay itself (event.target === modal) or a close button (no event)
    if (!event || event.target === modal) {
      if (modal) {
          modal.classList.add('hidden');
          modal.classList.remove('flex');
      }
    }
}

// Delete Course Modal (Used by dashboard.html)
function openDeleteModal(courseId, examType, subject) {
  const modal = document.getElementById('deleteCourseModal');
  const form = document.getElementById('deleteCourseForm');
  const courseName = document.getElementById('courseName');
  
  if (!modal || !form || !courseName) {
    console.error('Delete modal elements not found.');
    return;
  }
  
  // Set form action dynamically
  form.action = `/courses/${courseId}/delete/`;
  
  // Set course name in warning
  courseName.textContent = `${examType} ${subject}`;
  
  // Clear password field
  document.getElementById('deletePassword').value = '';
  
  // Show modal
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  
  // Focus password field
  setTimeout(() => {
    document.getElementById('deletePassword').focus();
  }, 100);
}

// Close Delete Course Modal
function closeDeleteModal(event) {
  const modal = document.getElementById('deleteCourseModal');
  if (modal) {
    // Only close if clicking the overlay (event.target === modal) or a close button (no event / manual call)
    if (!event || event.target === modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }
}

// ---------------------------------------------
// PWA & OTHER BOOTSTRAP LOGIC
// ---------------------------------------------

// PWA Install Prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  
  const installButton = document.getElementById('install-button');
  if (installButton) {
    installButton.classList.remove('hidden');
  }
});

// Mobile Menu Toggle (if needed for dropdowns)
function toggleMobileMenu(id) {
  const menu = document.getElementById(id);
  if (menu) {
    menu.classList.toggle('hidden');
  }
}

// Dark Mode Toggle
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

// ---------------------------------------------
// EVENT LISTENERS
// ---------------------------------------------

// DOMContentLoaded listener for setup
document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss Django Messages
    const messages = document.querySelectorAll('.django-message');
    messages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Dark Mode Toggle Button
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
      darkModeToggle.addEventListener('click', toggleDarkMode);
    }
  
    // Header shrink on scroll
    const header = document.getElementById('main-header');
    const headerLogo = document.getElementById('header-logo');
    const headerSpacer = document.getElementById('header-spacer');
    const profileAvatar = document.getElementById('profile-avatar');
    const headerContainer = header?.querySelector('div');
    
    if (header && headerLogo) {
      window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
          header.classList.add('scrolled');
          headerLogo.classList.remove('h-12');
          headerLogo.classList.add('h-8');
          if (profileAvatar) {
            profileAvatar.classList.remove('w-10', 'h-10');
            profileAvatar.classList.add('w-8', 'h-8');
          }
          if (headerSpacer) {
            headerSpacer.classList.remove('h-16');
            headerSpacer.classList.add('h-14');
          }
          if (headerContainer) {
            headerContainer.classList.remove('py-3');
            headerContainer.classList.add('py-2');
          }
        } else {
          header.classList.remove('scrolled');
          headerLogo.classList.remove('h-8');
          headerLogo.classList.add('h-12');
          if (profileAvatar) {
            profileAvatar.classList.remove('w-8', 'h-8');
            profileAvatar.classList.add('w-10', 'h-10');
          }
          if (headerSpacer) {
            headerSpacer.classList.remove('h-14');
            headerSpacer.classList.add('h-16');
          }
          if (headerContainer) {
            headerContainer.classList.remove('py-2');
            headerContainer.classList.add('py-3');
          }
        }
      });
    }

    // PWA Install Button
    const installButton = document.getElementById('install-button');
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
});

// Global Listeners
window.addEventListener('click', (e) => {
    // Close modals on overlay click
    const creditModal = document.getElementById('credit-modal');
    if (creditModal && e.target === creditModal) {
        closeCreditModal();
    }
    
    const deleteModal = document.getElementById('deleteCourseModal');
    if (deleteModal && e.target === deleteModal) {
      closeDeleteModal();
    }
});

document.addEventListener('keydown', function(event) {
  // Close modals on Escape key
  if (event.key === 'Escape') {
    closeCreditModal();
    closeDeleteModal();
  }
});

/**
 * Hides spinner on page load or back-button navigation.
 * 'pageshow' is more reliable than 'load' for this.
 */
window.addEventListener('pageshow', function(event) {
  hideSpinner();
});