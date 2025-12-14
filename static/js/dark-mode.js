(function() {
  if (localStorage.getItem('darkMode') === 'true' || (!('darkMode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
})();
