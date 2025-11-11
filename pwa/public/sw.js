self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open("arxos-cache-v1").then((cache) => cache.addAll(["/", "/index.html"]))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => !key.startsWith("arxos-cache")).map((key) => caches.delete(key)))
      )
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open("arxos-cache-v1").then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => cached);
    })
  );
});

