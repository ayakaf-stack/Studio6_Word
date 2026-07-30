document.addEventListener("DOMContentLoaded", () => {
    let currentType = "word";
    let selectedGenres = [];

    const searchInput = document.getElementById("search_input");
    const sortSelect = document.getElementById("sort_select");
    const genreList = document.getElementById("genre_list");
    const listContainer = document.getElementById("list_container");
    const noResult = document.getElementById("no_result");

    // タブ切り替え
    const toggleBtns = document.querySelectorAll(".toggle_btn");
    toggleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            currentType = btn.dataset.type;

            toggleBtns.forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");

            genreList.style.display = currentType === "word" ? "flex" : "none";

            fetchAndRender();
        });
    });

    // キーワード検索(即時反映)
    searchInput.addEventListener("input", () => {
        fetchAndRender();
    });

    // ソート変更
    sortSelect.addEventListener("change", () => {
        fetchAndRender();
    });

    // ジャンル選択(複数可)
    genreList.addEventListener("click", (e) => {
        if (!e.target.classList.contains("genre_btn")) return;

        const genreId = e.target.dataset.genreId;
        e.target.classList.toggle("selected");

        if (selectedGenres.includes(genreId)) {
            selectedGenres = selectedGenres.filter(id => id !== genreId);
        } else {
            selectedGenres.push(genreId);
        }
        fetchAndRender();
    });

    async function fetchAndRender() {
        const params = new URLSearchParams();
        params.set("type", currentType);
        params.set("q", searchInput.value.trim());
        params.set("sort", sortSelect.value);
        selectedGenres.forEach(id => params.append("genre", id));

        const response = await fetch(`/contents?${params.toString()}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        const data = await response.json();

        renderList(data.type, data.items);
    }

    function renderList(type, items) {
        listContainer.innerHTML = "";

        if (items.length === 0) {
            noResult.style.display = "block";
            return;
        }
        noResult.style.display = "none";

        items.forEach(item => {
            const li = document.createElement("li");

            if (type === "word") {
                li.className = "word_item";
                li.innerHTML = `
                    単語:${item.word} <br>
                    読み:${item.reading} <br>
                    意味:${item.mean} <br>
                    <form class="good-form" action="/good/word/${item.id}" method="POST">
                        <button type="submit" class="good-button">${item.is_good ? "❤️" : "🤍"}</button>
                        <span class="good-count">${item.good_count}</span>
                    </form>
                    <a href="/text-new/${item.id}">文章作成</a>
                `;
            } else {
                li.className = "text_item";
                    li.innerHTML = `
                        <span class="text_label">タイトル</span>
                        <p class="text_title_display">${item.title}</p>

                        <details class="text_drawer">
                            <summary class="drawer_btn">本文を表示</summary>
                            <p class="drawer_content">${item.main_text}</p>
                        </details>

                        <form class="good-form" action="/good/text/${item.id}" method="POST">
                            <button type="submit" class="good-button">${item.is_good ? "❤️" : "🤍"}</button>
                            <span class="good-count">${item.good_count}</span>
                        </form>
                    `;
            }

            listContainer.appendChild(li);
        });
    }
});