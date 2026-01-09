
// Gacha System JavaScript

function createFlipCard(creature, isMini = false, delay = 0) {
    // We need a way to get the base static URL. 
    // Since we can't use url_for in JS, we rely on the path from the API or a global config.
    // For now, assuming the API returns a relative path like 'images/foo.png',
    // We can construct the path. 
    // NOTE: Flask url_for('static', filename='...') usually resolves to /static/...

    // Safety check for image path
    const imagePath = creature.image ? '/static/' + creature.image : '/static/images/default.png';
    const pityBadge = creature.pity ? '<span class="pity-badge">✨ PITY!</span>' : '';

    let cardHtml = `
        <div class="flip-card-container ${isMini ? 'mini' : ''}" style="animation-delay: ${delay}ms;">
            <div class="flip-card">
                <div class="flip-card-inner">
                    <!-- Back of card (shown initially) -->
                    <div class="flip-card-back">
                        <div class="card-back-design">
                            <div class="card-back-pattern"></div>
                            <div class="card-back-shine"></div>
                            <div class="card-back-text">?</div>
                        </div>
                    </div>
                    <!-- Front of card (revealed after flip) -->
                    <div class="flip-card-front">
                        <div class="creature-card ${creature.rarity} ${isMini ? 'mini' : ''}">
                            ${pityBadge}
                            <div class="creature-image-gacha">
                                <img src="${imagePath}" alt="${creature.name}">
                            </div>
                            <h4>${creature.name}</h4>
                            <p class="rarity-text">${creature.rarity}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    return cardHtml;
}

function updatePityDisplay(pityCounter, legendaryPity) {
    $('#pity-counter').text(pityCounter + '/10');
    $('#legendary-pity').text(legendaryPity + '/80');
}

$(document).ready(function () {
    console.log("Gacha page loaded");

    let currentBannerId = null;

    // Get initial pity stats for standard banner (or currently selected)
    // For now, the page loads with global/standard pity.
    // TODO: Fetch pity when switching banners.

    // Banner selection handler
    $('.banner-card').click(function () {
        $('.banner-card').removeClass('selected');
        $(this).addClass('selected');
        currentBannerId = $(this).data('id');
        console.log("Selected banner:", currentBannerId);

        // Fetch Pity Stats for this banner
        $.ajax({
            url: '/get_pity',
            type: 'GET',
            data: { banner_id: currentBannerId || '' },
            success: function (data) {
                if (data.success) {
                    updatePityDisplay(data.pity_counter, data.legendary_pity);
                }
            },
            error: function (err) {
                console.error("Failed to fetch pity stats", err);
            }
        });
    });

    // Single Pull Handler
    $('#pull-single').click(function () {
        console.log("Single pull clicked");

        // Disable button during animation
        $(this).prop('disabled', true);

        $.ajax({
            url: '/pull_gacha',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                type: 'single',
                banner_id: currentBannerId
            }),
            success: function (data) {
                console.log("Single pull success:", data);
                if (data.success) {
                    $('#gacha-coins').text(data.coins);
                    updatePityDisplay(data.pity_counter, data.legendary_pity);

                    const creature = data.creature;
                    const flipCardHtml = createFlipCard(creature, false, 0);

                    // Show only the card, no text
                    $('#gacha-result').html(`
                        <div class="single-pull-result">
                            ${flipCardHtml}
                        </div>
                    `);

                    // Trigger flip animation after a short delay
                    setTimeout(() => {
                        $('.flip-card-container').addClass('flipped');
                    }, 500);

                    // Re-enable button after animation
                    setTimeout(() => {
                        $('#pull-single').prop('disabled', false);
                    }, 2000);

                } else {
                    $('#gacha-result').html(`<div class="error-message">${data.message}</div>`);
                    $('#pull-single').prop('disabled', false);
                }
            },
            error: function (xhr, status, error) {
                console.error("Single pull error:", error);
                $('#gacha-result').html(`<div class="error-message">Error: ${error}</div>`);
                $('#pull-single').prop('disabled', false);
            }
        });
    });

    // Multi Pull Handler (10x)
    $('#pull-multi').click(function () {
        console.log("Multi pull clicked");

        // Disable button during animation
        $(this).prop('disabled', true);

        $.ajax({
            url: '/pull_gacha',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                type: 'multi',
                banner_id: currentBannerId
            }),
            success: function (data) {
                console.log("Multi pull success:", data);
                if (data.success) {
                    $('#gacha-coins').text(data.coins);
                    updatePityDisplay(data.pity_counter, data.legendary_pity);

                    // Create grid with all cards (back side showing)
                    let resultHtml = '<div class="multi-result"><div class="creatures-grid">';

                    data.creatures.forEach((creature, index) => {
                        const delay = index * 500;
                        resultHtml += createFlipCard(creature, true, delay);
                    });

                    resultHtml += '</div></div>';

                    $('#gacha-result').html(resultHtml);

                    // Start flipping cards one by one
                    setTimeout(() => {
                        $('.flip-card-container').each(function (index) {
                            const $card = $(this);
                            setTimeout(() => {
                                $card.addClass('flipped');
                            }, index * 500);
                        });
                    }, 500);

                    // Re-enable button after all animations complete
                    setTimeout(() => {
                        $('#pull-multi').prop('disabled', false);
                    }, 6000);

                } else {
                    $('#gacha-result').html(`<div class="error-message">${data.message}</div>`);
                    $('#pull-multi').prop('disabled', false);
                }
            },
            error: function (xhr, status, error) {
                console.error("Multi pull error:", error);
                $('#gacha-result').html(`<div class="error-message">Error: ${error}</div>`);
                $('#pull-multi').prop('disabled', false);
            }
        });
    });
});
