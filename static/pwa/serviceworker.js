const CACHE_NAME = 'akili-v3';
const STATIC_CACHE = 'akili-static-v3';
const DYNAMIC_CACHE = 'akili-dynamic-v3';

const STATIC_ASSETS = [
  '/',
  '/dashboard/',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/js/dark-mode.js',
  '/static/images/logo.png',
  '/static/pwa/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap'
];

const OFFLINE_PAGE = '/';

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
            .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  if (request.method !== 'GET') return;
  
  if (url.origin === location.origin && (
      url.pathname.includes('/static/') || 
      url.pathname.includes('/pwa/')
  )) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request))
    );
    return;
  }
  
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response && response.status === 200 && response.type === 'basic') {
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then(cached => {
          if (cached) return cached;
          if (request.headers.get('accept').includes('text/html')) {
            return caches.match(OFFLINE_PAGE);
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
