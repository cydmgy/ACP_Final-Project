
$(document).ready(function () {
    console.log("Document ready - click script loaded");

    // Get the auth page URL from the data attribute embedded in the HTML or assume standard path
    // Ideally we pass this via a data attribute in a global config or on the button itself.
    // However, since I can't easily change the HTML structure deeply without risking breaking things,
    // I'll grab it from a meta tag or just hardcode/deduce it if standard.
    // Better yet, I'll update home.html to define a global const if needed or use relative paths.
    // For now, I will assume the button might need the URL passed to it.

    const authPageUrl = document.body.dataset.authUrl || '/auth';

    // Click Button Handler
    $('#click-button').click(function () {
        $.post('/click', function (data) {
            // Update counters
            $('#click-counter').text(data.clicks);
            $('#coin-counter').text(data.coins);
            $('#pull-counter').text(Math.floor(data.coins / 5));

            // Handle Mission Completion
            if (data.coins_earned > 0) {
                alert('🎉 Mission Complete! +' + data.coins_earned + ' coins!');
                location.reload();
            }
        }).fail(function (xhr, status, error) {
            if (xhr.status === 401) {
                window.location.href = authPageUrl;
            } else {
                console.error("Error:", error);
            }
        });
    });

    // Notification System
    const modal = $('#announcements-modal');
    const bellBtn = $('#notification-bell');
    const closeBtn = $('.close-modal');

    // Load announcements
    function loadAnnouncements() {
        $.get('/api/announcements', function (data) {
            const announcements = data;
            const container = $('#announcements-list');

            if (announcements.length === 0) {
                container.html('<div class="no-announcements">No announcements yet.</div>');
                return;
            }

            let html = '';
            announcements.forEach(ann => {
                const date = new Date(ann.created_at);
                const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const readClass = ann.is_read ? 'read' : 'unread';

                html += `
                    <div class="announcement-item ${readClass}">
                        <div class="announcement-header">
                            <h4>${ann.title}</h4>
                            <span class="announcement-date">${formattedDate}</span>
                        </div>
                        <div class="announcement-content">
                            ${ann.content.replace(/\n/g, '<br>')}
                        </div>
                        ${announcements.indexOf(ann) < announcements.length - 1 ? '<hr>' : ''}
                    </div>
                `;
            });

            container.html(html);

            // Mark all as read
            $.post('/api/announcements/mark-all-read', function (data) {
                if (data.success) {
                    $('.notification-badge').hide();
                    $('.announcement-item').addClass('read').removeClass('unread');
                }
            });
        }).fail(function (xhr, status, error) {
            $('#announcements-list').html('<div class="error">Failed to load announcements: ' + error + '</div>');
            console.error("API Error:", error, xhr.responseText);
        });
    }

    // Open modal
    bellBtn.click(function () {
        loadAnnouncements();
        modal.show();
    });

    // Close modal
    closeBtn.click(function () {
        modal.hide();
    });

    // Close when clicking outside
    $(window).click(function (event) {
        if ($(event.target).is(modal)) {
            modal.hide();
        }
    });

    // Check for new announcements
    function checkNewAnnouncements() {
        $.get('/api/announcements/unread-count', function (data) {
            if (data.count > 0) {
                $('.notification-badge').show();
            } else {
                $('.notification-badge').hide();
            }
        }).fail(function (xhr) {
            console.error("Failed to get unread count:", xhr.status);
            $('.notification-badge').hide();
        });
    }

    // Check initially
    checkNewAnnouncements();

    // Check every 60 seconds
    setInterval(checkNewAnnouncements, 60000);
});
