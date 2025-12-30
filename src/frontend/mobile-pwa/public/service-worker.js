/* eslint-disable no-restricted-globals */

// Service Worker for Odisha Flood Validation PWA
const CACHE_NAME = 'flood-validator-v1.0';
const URLs_TO_CACHE = [
    '/',
    '/index.html',
    '/manifest.json',
    '/static/js/bundle.js', // React build output
    '/favicon.ico'
];

// Install Event: Cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching all: app shell and content');
            return cache.addAll(URLs_TO_CACHE);
        })
    );
});

// Fetch Event: Network First, Fallback to Cache
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                return caches.match(event.request);
            })
    );
});

// Sync Event: Background Sync for Offline Reports
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-reports') {
        console.log('[Service Worker] Syncing new reports...');
        event.waitUntil(syncReports());
    }
});

// Sync Logic using IndexedDB
async function syncReports() {
    try {
        // Open IndexedDB
        const dbRequest = indexedDB.open('FloodReportsDB', 1);

        dbRequest.onsuccess = async (event) => {
            const db = event.target.result;
            const tx = db.transaction('offline_reports', 'readwrite');
            const store = tx.objectStore('offline_reports');
            const getAllReq = store.getAll();

            getAllReq.onsuccess = async () => {
                const reports = getAllReq.result;

                for (const report of reports) {
                    try {
                        // Attempt to send to API
                        const response = await fetch('http://localhost:8000/reports', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(report.data)
                        });

                        if (response.ok) {
                            console.log(`[Service Worker] Report ${report.id} synced!`);
                            // Create new tx to delete (original tx might be closed)
                            const delTx = db.transaction('offline_reports', 'readwrite');
                            delTx.objectStore('offline_reports').delete(report.id);
                        }
                    } catch (err) {
                        console.error("Sync failed for report:", report.id, err);
                    }
                }
            };
        };
    } catch (err) {
        console.error('[Service Worker] Sync failed', err);
    }
}
