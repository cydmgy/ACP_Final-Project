
function showSection(sectionId) {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('register-section').style.display = 'none';
    document.getElementById('forgot-section').style.display = 'none';
    document.getElementById(sectionId).style.display = 'block';
}

document.addEventListener('DOMContentLoaded', function () {
    // Get initial section from data attribute on the container or body
    const initialSection = document.body.dataset.initialSection || 'login';
    showSection(initialSection + '-section');
});
