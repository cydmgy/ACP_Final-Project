document.addEventListener("DOMContentLoaded", () => {

    console.log("Inventory JS loaded!");

    const popup = document.getElementById("descriptionPopup");
    const popupName = document.getElementById("popupName");
    const popupRarity = document.getElementById("popupRarity");
    const popupDescription = document.getElementById("popupDescription");
    const popupClose = document.getElementById("popupClose");

    document.querySelectorAll(".creature-card").forEach(card => {
        card.addEventListener("click", () => {

            const name = card.querySelector(".creature-name").innerText;
            const rarity = card.querySelector(".rarity")?.innerText || "Unknown";
            const description = card.querySelector(".creature-description").textContent.trim();

            popupName.innerText = name;
            popupRarity.innerText = rarity;
            popupDescription.innerText = description;

            popup.style.display = "flex";
        });
    });

    document.querySelectorAll(".toggle-desc").forEach(img => {
        img.addEventListener("click", (event) => {
            event.stopPropagation();          
            img.closest(".creature-card").click();
        });
    });

    popupClose.addEventListener("click", () => popup.style.display = "none");

    window.addEventListener("click", (e) => {
        if (e.target === popup) popup.style.display = "none";
    });
});
