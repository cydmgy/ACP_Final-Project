
// Time Tracking Script
// This script assumes it is only loaded/run when a user is logged in.

let timeInterval;

function startTimeTracking() {
    timeInterval = setInterval(() => {
        fetch('/update_time', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ seconds: 30 })
        })
            .catch(error => console.error('Error updating time:', error));
    }, 30000); // Every 30 seconds
}

function stopTimeTracking() {
    if (timeInterval) clearInterval(timeInterval);
}

document.addEventListener('DOMContentLoaded', startTimeTracking);
window.addEventListener('beforeunload', stopTimeTracking);
