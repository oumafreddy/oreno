// cookies.js
document.addEventListener('DOMContentLoaded', function() {
    // Set a cookie when the user accepts the cookie policy
    const acceptCookiesBtn = document.getElementById('acceptCookies');
    if (acceptCookiesBtn) {
        acceptCookiesBtn.addEventListener('click', function() {
            // Set cookie to expire in 365 days
            const d = new Date();
            d.setTime(d.getTime() + (365 * 24 * 60 * 60 * 1000));
            const expires = "expires=" + d.toUTCString();
            document.cookie = "cookies_accepted=true; " + expires + "; path=/";
            // Hide the cookie consent banner
            const cookieConsent = document.getElementById('cookieConsent');
            if (cookieConsent) {
                cookieConsent.style.display = 'none';
            }
        });
    }
    // Initialize the cookie consent banner
    function checkCookieConsent() {
        const cookiesAccepted = document.cookie.split(';').some((item) => item.trim().startsWith('cookies_accepted='));
        const cookieConsent = document.getElementById('cookieConsent');
        if (!cookiesAccepted && cookieConsent) {
            cookieConsent.style.display = 'flex';
        } else if (cookieConsent) {
            cookieConsent.style.display = 'none';
        }
    }
    // Run the check when the page loads
    checkCookieConsent();
}); 