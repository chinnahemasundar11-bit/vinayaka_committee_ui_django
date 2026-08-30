/**
 * Vinayaka Committee Offline Mobile Cash Receipt Collector
 * Uses localStorage & IndexedDB fallback for recording offline cash donations.
 */

const OFFLINE_KEY = "vinayaka_offline_receipts_queue";

function getOfflineQueue() {
    try {
        return JSON.parse(localStorage.getItem(OFFLINE_KEY)) || [];
    } catch (e) {
        return [];
    }
}

function saveOfflineQueue(queue) {
    localStorage.setItem(OFFLINE_KEY, JSON.stringify(queue));
    updateOfflineUIBadge();
}

function addOfflineReceipt(receiptData) {
    const queue = getOfflineQueue();
    receiptData.client_timestamp = new Date().toISOString();
    receiptData.temp_id = "OFFLINE-" + Date.now();
    queue.push(receiptData);
    saveOfflineQueue(queue);
}

function updateOfflineUIBadge() {
    const queue = getOfflineQueue();
    const badgeEl = document.getElementById("offlineQueueBadge");
    const countEl = document.getElementById("offlineQueueCount");
    
    if (badgeEl && countEl) {
        if (queue.length > 0) {
            countEl.textContent = queue.length;
            badgeEl.classList.remove("d-none");
        } else {
            badgeEl.classList.add("d-none");
        }
    }
}

async function syncOfflineReceipts() {
    const queue = getOfflineQueue();
    if (!queue.length || !navigator.onLine) return;

    const csrfTokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

    try {
        const response = await fetch('/funds/api/sync-offline-receipts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ receipts: queue })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success') {
                localStorage.removeItem(OFFLINE_KEY);
                updateOfflineUIBadge();
                if (data.synced_count > 0) {
                    alert(`✅ Automatically synced ${data.synced_count} offline cash receipt(s) to PostgreSQL database!`);
                    window.location.reload();
                }
            }
        }
    } catch (err) {
        console.warn("Offline sync attempt failed, will retry on next connection.", err);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    updateOfflineUIBadge();

    // Register Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(reg => console.log('PWA Service Worker registered.', reg.scope))
            .catch(err => console.log('Service Worker registration failed:', err));
    }

    // Network status listeners
    window.addEventListener('online', syncOfflineReceipts);

    // Auto sync on page load if online
    if (navigator.onLine) {
        syncOfflineReceipts();
    }

    // Intercept Add Fund form submission if offline
    const addFundForm = document.querySelector('form[action="/funds/add/"]');
    if (addFundForm) {
        addFundForm.addEventListener('submit', function (e) {
            if (!navigator.onLine) {
                e.preventDefault();
                const formData = new FormData(addFundForm);
                const receiptObj = {};
                formData.forEach((value, key) => receiptObj[key] = value);
                
                addOfflineReceipt(receiptObj);
                alert("📶 You are currently offline. Receipt saved locally on device and will auto-sync when internet reconnects!");
                addFundForm.reset();
            }
        });
    }
});
