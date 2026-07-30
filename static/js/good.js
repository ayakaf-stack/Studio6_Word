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
    document.querySelectorAll("main > p").forEach(p => p.remove());

    let container = document.getElementById("flash-messages");

    if (!container) {
        container = document.createElement("div");
        container.id = "flash-messages";
        document.querySelector("main").prepend(container);
    }

    container.innerHTML = `<div class="flash-message">${message}</div>`;
}