(function() {
  'use strict';

  function showToast(message, type) {
    type = type || 'success';
    var toast = document.createElement('div');
    var bgColor = 'bg-blue-500';
    if (type === 'success') bgColor = 'bg-green-500';
    if (type === 'error') bgColor = 'bg-red-500';
    
    toast.className = 'fixed bottom-0 left-1/2 transform -translate-x-1/2 mb-5 px-6 py-3 rounded-lg shadow-lg z-[110] ' + bgColor + ' text-white font-semibold transition-all duration-300 opacity-0 -translate-y-5';
    toast.textContent = message;
    
    document.body.appendChild(toast);

    setTimeout(function() {
      toast.style.opacity = '1';
      toast.style.transform = 'translate(-50%, 0)';
    }, 10);

    setTimeout(function() {
      toast.style.opacity = '0';
      toast.style.transform = 'translate(-50%, 20px)';
      setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
  }

  function fallbackCopy(inputElement) {
    try {
      inputElement.select();
      inputElement.setSelectionRange(0, 99999);
      var successful = document.execCommand('copy');
      if (successful) {
        showToast('Referral link copied!');
      } else {
        showToast('Copy failed. Please copy manually.', 'error');
      }
    } catch (err) {
      showToast('Copy failed. Please copy manually.', 'error');
    }
  }

  window.copyReferralLink = function() {
    var referralInput = document.getElementById('referralLinkInput') || 
                        document.getElementById('referral-input') ||
                        document.getElementById('profile-referral-input');
    
    if (!referralInput) {
      showToast('Error: Referral input field not found.', 'error');
      return;
    }
    
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(referralInput.value)
        .then(function() {
          showToast('Referral link copied!');
        })
        .catch(function() {
          fallbackCopy(referralInput);
        });
    } else {
      fallbackCopy(referralInput);
    }
  };

  window.showSpinner = function() {
    var overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.remove('hidden');
      overlay.classList.add('flex');
    }
  };

  window.hideSpinner = function() {
    var overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.add('hidden');
      overlay.classList.remove('flex');
    }
  };

  window.openCreditModal = function() {
    var modal = document.getElementById('credit-modal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
  };

  window.closeCreditModal = function(event) {
    var modal = document.getElementById('credit-modal');
    if (!event || event.target === modal) {
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }
  };

  window.openDeleteModal = function(courseId, examType, subject) {
    var modal = document.getElementById('deleteCourseModal');
    var form = document.getElementById('deleteCourseForm');
    var courseName = document.getElementById('courseName');
    
    if (!modal || !form || !courseName) return;
    
    form.action = '/courses/' + courseId + '/delete/';
    courseName.textContent = examType + ' ' + subject;
    document.getElementById('deletePassword').value = '';
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    setTimeout(function() {
      document.getElementById('deletePassword').focus();
    }, 100);
  };

  window.closeDeleteModal = function(event) {
    var modal = document.getElementById('deleteCourseModal');
    if (modal) {
      if (!event || event.target === modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
      }
    }
  };

  window.toggleDarkMode = function() {
    var html = document.documentElement;
    var isDark = html.classList.contains('dark');
    
    if (isDark) {
      html.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    } else {
      html.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    }
  };

  var deferredPrompt;

  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    var installButton = document.getElementById('install-button');
    if (installButton) {
      installButton.classList.remove('hidden');
    }
  });

  function initProfileDropdown() {
    var btn = document.getElementById('profile-dropdown-btn');
    var dropdown = document.getElementById('profile-dropdown');
    var container = document.getElementById('profile-dropdown-container');
    
    if (btn && dropdown) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('hidden');
        var notifDropdown = document.getElementById('notification-dropdown');
        if (notifDropdown) notifDropdown.classList.add('hidden');
      });
      
      document.addEventListener('click', function(e) {
        if (container && !container.contains(e.target)) {
          dropdown.classList.add('hidden');
        }
      });
    }
  }

  function initNotificationDropdown() {
    var btn = document.getElementById('notification-dropdown-btn');
    var dropdown = document.getElementById('notification-dropdown');
    var container = document.getElementById('notification-dropdown-container');
    
    if (btn && dropdown) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('hidden');
        var profileDropdown = document.getElementById('profile-dropdown');
        if (profileDropdown) profileDropdown.classList.add('hidden');
      });
      
      document.addEventListener('click', function(e) {
        if (container && !container.contains(e.target)) {
          dropdown.classList.add('hidden');
        }
      });
    }
  }

  function initMobileMenu() {
    var btn = document.getElementById('mobile-menu-btn');
    var menu = document.getElementById('mobile-menu');
    var container = document.getElementById('mobile-menu-container');
    
    if (btn && menu) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        menu.classList.toggle('hidden');
      });
      
      document.addEventListener('click', function(e) {
        if (container && !container.contains(e.target)) {
          menu.classList.add('hidden');
        }
      });
    }
  }

  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
      anchor.addEventListener('click', function(e) {
        var targetId = this.getAttribute('href');
        if (targetId && targetId !== '#') {
          var target = document.querySelector(targetId);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      });
    });
  }

  function initKatex() {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(document.body, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false}
        ]
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    var messages = document.querySelectorAll('.django-message');
    messages.forEach(function(msg) {
      setTimeout(function() {
        msg.style.opacity = '0';
        setTimeout(function() { msg.remove(); }, 300);
      }, 5000);
    });

    var darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
      darkModeToggle.addEventListener('click', window.toggleDarkMode);
    }

    var header = document.getElementById('main-header');
    var headerLogo = document.getElementById('header-logo');
    var headerSpacer = document.getElementById('header-spacer');
    var profileAvatar = document.getElementById('profile-avatar');

    if (header && headerLogo) {
      window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
          headerLogo.classList.remove('h-10');
          headerLogo.classList.add('h-8');
          if (profileAvatar) {
            profileAvatar.classList.remove('w-9', 'h-9');
            profileAvatar.classList.add('w-8', 'h-8');
          }
          if (headerSpacer) {
            headerSpacer.classList.remove('h-16');
            headerSpacer.classList.add('h-14');
          }
        } else {
          headerLogo.classList.remove('h-8');
          headerLogo.classList.add('h-10');
          if (profileAvatar) {
            profileAvatar.classList.remove('w-8', 'h-8');
            profileAvatar.classList.add('w-9', 'h-9');
          }
          if (headerSpacer) {
            headerSpacer.classList.remove('h-14');
            headerSpacer.classList.add('h-16');
          }
        }
      });
    }

    var installButton = document.getElementById('install-button');
    if (installButton) {
      installButton.addEventListener('click', function() {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function(result) {
          deferredPrompt = null;
          installButton.classList.add('hidden');
        });
      });
    }

    initProfileDropdown();
    initNotificationDropdown();
    initMobileMenu();
    initSmoothScroll();
    initKatex();
  });

  window.addEventListener('click', function(e) {
    var creditModal = document.getElementById('credit-modal');
    if (creditModal && e.target === creditModal) {
      window.closeCreditModal();
    }
    
    var deleteModal = document.getElementById('deleteCourseModal');
    if (deleteModal && e.target === deleteModal) {
      window.closeDeleteModal();
    }
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      window.closeCreditModal();
      window.closeDeleteModal();
    }
  });

  window.addEventListener('pageshow', function() {
    window.hideSpinner();
  });
})();
