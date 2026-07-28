document.addEventListener("DOMContentLoaded", () => {
    const nextBtn = document.getElementById("next_word_btn");

    nextBtn.addEventListener("click", async () => {
        const response = await fetch("/", {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        const data = await response.json();

        // 単語部分を書き換え
        document.getElementById("word_text").textContent = data.word.word;
        document.getElementById("word_reading").textContent = data.word.reading;
        document.getElementById("word_mean").textContent = data.word.mean;

        const wordForm = document.getElementById("word_good_form");
        wordForm.action = `/good/word/${data.word.id}`;
        wordForm.querySelector(".good-button").textContent = data.is_good ? "❤️" : "🤍";
        wordForm.querySelector(".good-count").textContent = data.good_count;

        document.getElementById("text_new_link").href = `/text-new/${data.word.id}`;

        // 文章一覧を書き換え
        const textListArea = document.getElementById("text_list_area");
        textListArea.innerHTML = "";

        data.texts.forEach(text => {
            const div = document.createElement("div");
            div.className = "text_item";
            div.innerHTML = `
                文章タイトル:${text.title} <br>
                文章本文:${text.main_text} <br>
                <form class="good-form" action="/good/text/${text.id}" method="POST">
                    <button type="submit" class="good-button">${text.is_good ? "❤️" : "🤍"}</button>
                    <span class="good-count">${text.good_count}</span>
                </form>
            `;
            textListArea.appendChild(div);
        });
    });
});