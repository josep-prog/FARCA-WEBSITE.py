// Function to get the user's current location and determine if they are eligible for free delivery
function checkDeliveryEligibility() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLatitude = position.coords.latitude;
            const userLongitude = position.coords.longitude;
            const farcaLatitude = -2.5245; // Approximate latitude for Gihundwe, Rusizi
            const farcaLongitude = 28.9071; // Approximate longitude for Gihundwe, Rusizi

            // Calculate the distance between the user and FARCA using the Haversine formula
            const distance = calculateDistance(userLatitude, userLongitude, farcaLatitude, farcaLongitude);
            
            // Define the radius for free delivery (in km)
            const freeDeliveryRadius = 50; // within 50 km of FARCA

            if (distance <= freeDeliveryRadius) {
                displayFreeDeliveryMessage();
            } else {
                displayDeliveryFeeMessage(distance);
            }
        }, function() {
            alert("Geolocation is not supported by this browser or permission denied.");
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

// Function to calculate the distance between two coordinates using the Haversine formula
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the Earth in kilometers
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c; // Distance in kilometers
    return distance;
}

// Function to convert degrees to radians
function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

// Function to display a message for free delivery
function displayFreeDeliveryMessage() {
    const deliveryMessage = document.getElementById('delivery-message');
    if (deliveryMessage) {
        deliveryMessage.innerHTML = "You are eligible for free delivery! Your order will be delivered to you at no extra cost.";
    }
}

// Function to display a message for delivery fee
function displayDeliveryFeeMessage(distance) {
    const deliveryMessage = document.getElementById('delivery-message');
    if (deliveryMessage) {
        const deliveryFee = 1500; // Delivery fee for areas beyond the free radius
        deliveryMessage.innerHTML = `Delivery Fee: 1,500 RWF. Your location is approximately ${distance.toFixed(2)} km away from FARCA.`;
    }
}

// Event listener for document ready
document.addEventListener('DOMContentLoaded', function() {
    checkDeliveryEligibility();
});
