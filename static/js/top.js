document.addEventListener("DOMContentLoaded", () => {
    const nextBtn = document.getElementById("next_word_btn");
    const INITIAL_BACKGROUND_COLOR = "#062c54";

        // 暗めのランダム背景色を生成する関数（色は戻すだけ）
        function generateRandomDarkColor() {
        // 色相(H): 0〜360度（全色相からランダムに選ぶ）
        const h = Math.floor(Math.random() * 360);

        // 彩度(S): 20%〜35%
        const s = Math.floor(Math.random() * 16) + 20; 

        // 輝度(L): 20%〜35%
        const l = Math.floor(Math.random() * 16) + 20;

        return `hsl(${h}, ${s}%, ${l}%)`;
    }

    // ★ ポイント2: 背景色を適用する関数（フェードさせるため少し遅らせる）
    function applyBackgroundColor(color) {
        setTimeout(() => {
            document.body.style.backgroundColor = color;
        }, 100); 
    }

    nextBtn.addEventListener("click", async () => {
        // ② 「次へ」ボタンを押した時
        // ランダムな暗い色を生成して適用
        const nextColor = generateRandomDarkColor();
        applyBackgroundColor(nextColor);
        const response = await fetch("/", {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        const data = await response.json();

        // 単語部分を書き換え
        document.getElementById("word_text").textContent = data.word.word;
        document.getElementById("word_reading").textContent = `【 ${data.word.reading} 】`;
        document.getElementById("word_mean").textContent = data.word.mean;

        const wordForm = document.getElementById("word_good_form");
        wordForm.action = `/good/word/${data.word.id}`;

        const wordButton = wordForm.querySelector(".good-button");
        wordButton.classList.toggle("is-liked", data.is_good);

        wordForm.querySelector(".good-count").textContent = data.good_count;

        document.getElementById("text_new_link").href = `/text-new/${data.word.id}`;

        // 文章一覧を書き換え
        const textListArea = document.getElementById("text_list_area");
        textListArea.innerHTML = '<div class="text_scroll_list"></div>';
        const scrollList = textListArea.querySelector(".text_scroll_list");

        data.texts.forEach(text => {
            const div = document.createElement("div");
            div.className = "text_item";
            div.innerHTML = `
                <span class="text_label">タイトル</span>
                <p class="text_title_display">${text.title}</p>

                <details class="text_drawer">
                    <summary class="drawer_btn">本文を表示</summary>
                    <p class="drawer_content white-space">${text.main_text}</p>
                </details>

                <form class="good-form" action="/good/text/${text.id}" method="POST">
                    <button type="submit" class="good-button${text.is_good ? " is-liked" : ""}" aria-label="お気に入り">
                        <svg class="bookmark-icon" width="18" height="22" viewBox="0 0 24 30">
                            <path d="M5 3 H19 V27 L12 20.5 L5 27 Z"/>
                        </svg>
                    </button>
                    <span class="good-count">${text.good_count}</span>
                </form>
            `;
            scrollList.appendChild(div);
        });
    });
});