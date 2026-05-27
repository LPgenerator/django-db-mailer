# Browsers Web Push notifications

## Supporting browsers

**Desktop**

- Chrome ≥ 50
- Firefox ≥ 44
- Safari ≥ 7 (separate APNs / Safari Web Push package)

**Mobile**

- Chrome on Android
- Safari on iOS 16.4+ (PWA only — see Apple's
  [Web Push for Web Apps on iOS and iPadOS](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers))

WebPush requires HTTPS in production (browsers reject service workers
served over plain HTTP — `localhost` is the only exception).

## FCM (Firebase) setup

The legacy GCM HTTP endpoint (`android.googleapis.com/gcm/send`) was
**retired by Google on 2024-06-20**. New projects should use Firebase
Cloud Messaging:

1. Create a project at <https://console.firebase.google.com/>.
2. Enable Cloud Messaging.
3. Generate a service-account JSON.
4. The bundled `dbmail.providers.google.android` provider continues
   to point at `fcm.googleapis.com/fcm/send` for the
   compatibility-shim path; for new deployments expect to write a
   thin custom provider against `firebase-admin` (the FCM v1 rewrite
   is in scope for `3.1`).

Example `settings.py`:

```python
GCM_KEY = "AIza..."   # legacy server key, kept for backwards compat
```

1.  Add `GCM_KEY` with `API KEY` to the project settings:

``` python
GCM_KEY = 'AIza...'
```

2.  Create `/static/manifest.json` with the following lines:

``` json
{
  "gcm_sender_id": "``{APP ID}``",
  "name": "Web Push Notification",
  "short_name": "WebPush",
  "icons": [
    {
      "src": "/static/images/icon-192x192.png",
      "sizes": "192x192"
    }
  ],
  "start_url": "/?homescreen=1",
  "display": "standalone",
  "gcm_user_visible_only": true,
  "permissions": [
    "gcm"
  ]
}
```

3.  Add `/static/manifest.json` to meta on page

``` html
<head>
    <meta charset="UTF-8">
    ...
    <link rel="manifest" href="/static/manifest.json">
</head>
```

4.  Create service worker `/static/js/service-worker.js` file

``` javascript
self.addEventListener('push', function (event) {
    if (event.data) {
        var payload = event.data.json();

        return self.registration.showNotification(payload.title, {
            body: data.body,
            icon: '/static/images/icon-192x192.png',
            data: payload,
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
```

5.  Register service worker to get permission and start background process

``` html
<head>
...
<script>
    function enableWebPush() {
        var is_chrome = navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
        var is_ff = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
        if ((is_chrome || is_ff) && 'serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js').then(function () {
                navigator.serviceWorker.ready.then(function (serviceWorkerRegistration) {
                    serviceWorkerRegistration.pushManager.getSubscription().then(function (subscription) {
                        if (!subscription) {
                            serviceWorkerRegistration.pushManager.subscribe({userVisibleOnly: true}).then(function (subscription_info) {
                                var xhr = new XMLHttpRequest();
                                xhr.open("POST", "/dbmail/web-push/subscribe/", true);
                                xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                                xhr.setRequestHeader("X-CSRFToken", "{{ request.META.CSRF_COOKIE }}");
                                xhr.send(JSON.stringify(subscription_info));

                                document.getElementById('subscription').innerHTML = JSON.stringify(subscription_info);
                            });
                        }
                        document.getElementById('subscription').innerHTML = JSON.stringify(subscription);
                    });

                });
            });
        }
    }
</script>
</head>
<body onload="enableWebPush()">
<div id="subscription"></div>
...
```

6.  Open page to setup notification

``` bash
$ open '/Applications/Google Chrome.app' --args https://localhost:8000/web-push/
```

7.  Install `pywebpush` app

``` bash
$ pip install 'pywebpush>=0.4.0'
```

8.  Add Server-side Endpoints to `urls.py`

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

9.  Add events receiver (subscribe/unsubscribe)

``` python
from dbmail import signals

def _web_push(**kwargs):
    # you must have your own function to store device token into db
    kwargs.pop('instance', None)
    kwargs.pop('sender', None)
    kwargs.pop('signal', None)
    print(kwargs)

signals.push_subscribe.connect(_web_push)
signals.push_unsubscribe.connect(_web_push)
```

10. And finally you can send notification from backend

``` python
from dbmail.providers.google.browser import send

subscription_info = {
    'endpoint': 'https://android.googleapis.com/gcm/send/dVj-T5fXaEw:AP...',
     'keys': {
        'auth': 'X6Ek_...',
        'p256dh': 'BBo..'
     }
}

send(subscription_info, message="Hello, World!", event="Python", url="..")
```

## Safari examples

1.  Register a Website Push ID (requires iOS developer license or Mac developer license)
2.  Download and import to KeyChain the push notification certificate
3.  Exporting Private Key .p12 from KeyChain
4.  Generate .pem certificate to send notification via APNs

``` bash
$ openssl pkcs12 -in apns-cert.p12 -out apns-cert.pem -nodes -clcerts
```

5.  Check APNs connection

``` bash
$ openssl s_client -connect gateway.push.apple.com:2195 -CAfile apns-cert.pem
```

6.  Create contents of the Push Package

``` bash
PushPackage.raw/
  icon.iconset
    icon_128x128@2x.png
    icon_128x128.png
    icon_32x32@2x.png
    icon_32x32.png
    icon_16x16@2x.png
    icon_16x16.png
  website.json
```

7.  Contents of `website.json`

``` json
{
    "websiteName": "Localhost",
    "websitePushID": "web.ru.lpgenerator",
    "allowedDomains": ["https://localhost:8000"],
    "urlFormatString": "https://localhost:8000/%@",
    "authenticationToken": "19f8d7a6e9fb8a7f6d9330dabe",
    "webServiceURL": "https://localhost:8000/dbmail/safari"
}
```

8.  Create Push Package (<https://github.com/connorlacombe/Safari-Push-Notifications>)

``` bash
$ cp `php createPushPackage.php` pushPackages.zip
```

9.  Add Server-side Endpoints to `urls.py`

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

10. Add events receiver (subscribe/unsubscribe/errors)

``` python
from dbmail import signals

def _safari_web_push(**kwargs):
    # you must have your own function to store device token into db
    kwargs.pop('instance', None)
    kwargs.pop('sender', None)
    kwargs.pop('signal', None)
    print(kwargs)

signals.safari_subscribe.connect(_safari_web_push)
signals.safari_unsubscribe.connect(_safari_web_push)
signals.safari_error_log.connect(_safari_web_push)
```

11. Add `APNS_GW_HOST` and `APNS_CERT_FILE` to the project settings

``` python
APNS_GW_HOST = 'api.push.apple.com'
APNS_GW_PORT = 443
APNS_CERT_FILE = 'apns-cert.pem'
APNS_KEY_FILE = None
```

12. Register service worker to get permission and start background process

``` html
<head>
...
<script>
    function enableSafariWebPush() {
        var websitePushID = "web.dev.localhost";
        var webServiceUrl = "https://localhost:8000/web-push/";
        var dataToIdentifyUser = {UserId: "123123"};

        var checkRemotePermission = function (permissionData) {
            if (permissionData.permission === 'default') {
                window.safari.pushNotification.requestPermission(
                        webServiceUrl,
                        websitePushID,
                        dataToIdentifyUser,
                        checkRemotePermission
                );
            }
            else if (permissionData.permission === 'denied') {
                console.dir(arguments);
                alert("Access denied. Please, enable push notification from Safari settings.");
            }
            else if (permissionData.permission === 'granted') {
                document.getElementById('subscription').innerHTML = JSON.stringify(permissionData.deviceToken);
            }
        };

        if ('safari' in window && 'pushNotification' in window.safari) {
            checkRemotePermission(
                window.safari.pushNotification.permission(websitePushID)
            );
        }
    }
</script>
</head>
<body onload="enableSafariWebPush()">
<div id="subscription"></div>
...
```

13. Open page to setup notification

``` bash
$ open '/Applications/Safari.app' --args https://localhost:8000/web-push/
```

14. And finally you can send notification from backend

``` python
from dbmail import send_db_push

send_db_push(
    'welcome',
    '62B63D730C84E363627B95879CF13723B890249A4BA03BAC08004574DF17D2DA',
    use_celery=False,
    alert={
        "title": "Python",
        "body": "Hello, World!",
        "action": "View"
    }, **{"url-args": ["https://localhost:8000/admin/"]}
)
```

## Local demo

You can test by demo which found on repo or use samples

1.  Run server

``` bash
$ cd demo
$ python manage.py runsslserver
```

2.  Copy path to SSL certs

``` bash
export CERT_PATH=`python -c 'import os, sslserver; print(os.path.dirname(sslserver.__file__) + "/certs/development.crt")'`
echo $(CERT_PATH)
```

3.  Import certs to KeyChain

### Linux

``` bash
sudo apt-get install -y ca-certificates
sudo cp "$CERT_PATH" /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### OS X

``` bash
sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" "$CERT_PATH"
```

### Windows (possible will not working)

``` bash
certutil -addstore "Root" "$CERT_PATH"
    # or
certmgr.exe -add -all -c "$CERT_PATH" -s -r localMachine Root
```

4.  Open demo url

``` bash
$ open /Applications/Safari.app --args https://localhost:8000/web-push/
    # or
$ open '/Applications/Google Chrome.app' --args https://localhost:8000/web-push/
```
