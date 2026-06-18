const CACHE_NAME = 'taskflow-v2';
const URLS = [
  '.',
  'index.html',
  'manifest.json',
  'icon-192.png',
  'icon-512.png'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(URLS);
    })
  );
});

self.addEventListener('fetch', function(event) {
  if (event.request.url.includes('supabase.co')) return;
  if (event.request.url.includes('unpkg.com')) {
    event.respondWith(
      caches.open(CACHE_NAME + '-libs').then(function(cache) {
        return cache.match(event.request).then(function(response) {
          return response || fetch(event.request).then(function(resp) {
            cache.put(event.request, resp.clone());
            return resp;
          });
        });
      })
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.filter(function(n) { return n !== CACHE_NAME && !n.startsWith(CACHE_NAME); })
          .map(function(n) { return caches.delete(n); })
      );
    })
  );
});
