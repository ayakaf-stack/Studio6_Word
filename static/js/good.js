console.log("good.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    // 動的に追加されたフォームにも効くよう、documentに1つだけリスナーを付ける
    document.addEventListener("submit", async function (e) {
        const form = e.target;
        if (!form.classList.contains("good-form")) return;

        e.preventDefault();

        const response = await fetch(form.action, { method: "POST" });
        const data = await response.json();

        if (!response.ok) {
            showFlashMessage(data.error);
            return;
        }

        form.querySelector(".good-button").textContent =
            data.is_good ? "❤️" : "🤍";

        const countEl = form.querySelector(".good-count");
        if (countEl) {
            countEl.textContent = data.good_count;
        }
    });
});

function showFlashMessage(message) {
    const container = document.getElementById("flash-messages");
    container.innerHTML = `<div class="flash-message">${message}</div>`;
}