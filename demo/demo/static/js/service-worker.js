self.addEventListener('push', function (event) {
    if (event.data) {
        var payload = event.data.json();

        return self.registration.showNotification(payload.title, {
            body: payload.body,
            icon: '/static/images/icon-256x256.png',
            data: payload
        });
    }
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    if (event.notification.data && event.notification.data.url) {
        event.waitUntil(clients.matchAll({
            type: "window"
        }).then(function () {
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data.url);
            }
        }));
    }
});
