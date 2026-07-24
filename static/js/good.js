document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".good-form").forEach(form => {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();

            const response = await fetch(form.action, { method: "POST" });
            const data = await response.json();

            console.log("status:", response.status);
            console.log("data:", data);
            console.log("container:", document.getElementById("flash-messages"));

            if (!response.ok) {
                showFlashMessage(data.error);
                return;
            }

            form.querySelector(".good-button").textContent =
                data.is_good ? "❤️" : "🤍";

            form.querySelector(".good-count").textContent = data.good_count;
        });
    });
});

function showFlashMessage(message) {
    console.log("showFlashMessage called with:", message);
    const container = document.getElementById("flash-messages");
    container.innerHTML = `<div class="flash-message">${message}</div>`;
}