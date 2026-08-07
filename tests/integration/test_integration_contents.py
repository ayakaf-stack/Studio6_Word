from random import randint

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait, Select

from app import app as flask_app
from models.extensions import db
from models.models import Text, Word, Good_text


TEXT_OWNER_USER_ID = 1  # いいね対象の文章の作成者（いいねする側とは無関係でよい）
WORD_ID = 29  # 既存の単語ID


# ============================================================
# テストデータ作成・削除用ヘルパー
# ============================================================

def _get_word_string():
    with flask_app.app_context():
        word = db.session.get(Word, WORD_ID).word
        db.session.remove()
        return word


def _create_text(user_id, title, main_text, text_status=0, word_id=WORD_ID):
    with flask_app.app_context():
        text = Text(
            user_id=user_id,
            title=title,
            main_text=main_text,
            text_status=text_status,
            word=word_id,
        )
        db.session.add(text)
        db.session.commit()
        text_id = text.id
        db.session.remove()
        return text_id


def _delete_text_if_exists(text_id):
    with flask_app.app_context():
        text = db.session.get(Text, text_id)
        if text is not None:
            db.session.delete(text)
            db.session.commit()
        db.session.remove()


def _delete_good_text_if_exists(user_id, text_id):
    with flask_app.app_context():
        like = Good_text.query.filter_by(user_id=user_id, text_id=text_id).first()
        if like is not None:
            db.session.delete(like)
            db.session.commit()
        db.session.remove()


# ============================================================
# 画面操作用ヘルパー
# ============================================================

def _wait(driver, timeout=5):
    """StaleElementReferenceExceptionを無視するWebDriverWait。

    検索・並び替え・タブ切替のたびに #list_container が非同期に
    丸ごと作り直されるため、待機条件の評価中（find_elementsした
    要素からテキストを読んでいる最中など）に再描画が走ると
    StaleElementReferenceExceptionが発生することがある。
    デフォルトのWebDriverWaitはこれを無視しないため即座に失敗して
    しまうので、ここで無視するようにし、再描画が収まるまで
    自動的にリトライさせる。
    """
    return WebDriverWait(driver, timeout, ignored_exceptions=(StaleElementReferenceException,))


def _switch_to_text_tab(driver):
    driver.find_element("css selector", '.toggle_btn[data-type="text"]').click()
    # タブ切替時のfetchAndRenderが完了し、文章の一覧に描画が入れ替わるまで待つ
    _wait(driver).until(
        lambda d: d.find_elements("class name", "text_item")
    )


def _search(driver, keyword):
    """検索欄にキーワードをセットする。

    send_keys で1文字ずつ入力すると、文字数分だけ input イベント
    （= fetchAndRenderの非同期リクエスト）が発火し、レスポンスの
    到着順序が入れ替わることで要素が stale になることがある。
    そのため、値を一括でセットして input イベントを1回だけ
    発火させることで、fetchAndRenderが1回だけ走るようにする。
    """
    search_input = driver.find_element("id", "search_input")
    driver.execute_script(
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
        search_input,
        keyword,
    )


def _find_text_item_by_title(driver, title, timeout=5):
    def _find(d):
        for li in d.find_elements("class name", "text_item"):
            title_el = li.find_element("class name", "text_title_display")
            if title_el.text == title:
                return li
        return False

    return _wait(driver, timeout).until(_find)


# ============================================================
# 初期表示
# ============================================================

def test_contents_default_tab_is_word(driver, base_url):
    driver.get(f"{base_url}/contents")

    word_btn = driver.find_element("css selector", '.toggle_btn[data-type="word"]')
    text_btn = driver.find_element("css selector", '.toggle_btn[data-type="text"]')

    assert "selected" in word_btn.get_attribute("class")
    assert "selected" not in text_btn.get_attribute("class")

    genre_list = driver.find_element("id", "genre_list")
    assert genre_list.value_of_css_property("display") != "none"


def test_contents_switch_to_text_tab_hides_genre_and_changes_sort_options(driver, base_url):
    driver.get(f"{base_url}/contents")

    _switch_to_text_tab(driver)

    text_btn = driver.find_element("css selector", '.toggle_btn[data-type="text"]')
    assert "selected" in text_btn.get_attribute("class")

    genre_list = driver.find_element("id", "genre_list")
    assert genre_list.value_of_css_property("display") == "none"

    sort_values = [
        o.get_attribute("value")
        for o in driver.find_elements("css selector", "#sort_select option")
    ]
    assert "date_desc" in sort_values
    assert "date_asc" in sort_values
    assert "aiueo_asc" not in sort_values


# ============================================================
# 検索
# ============================================================

def test_contents_text_search_finds_published_and_excludes_draft(driver, base_url):
    word = _get_word_string()
    keyword = f"検索対象{randint(1,100000)}"

    published_title = f"{keyword}公開"
    draft_title = f"{keyword}下書き"

    published_id = _create_text(
        TEXT_OWNER_USER_ID, published_title, f"{word}{keyword}を含む公開文章です。", text_status=0
    )
    draft_id = _create_text(
        TEXT_OWNER_USER_ID, draft_title, f"{word}{keyword}を含む下書き文章です。", text_status=1
    )

    try:
        driver.get(f"{base_url}/contents")
        _switch_to_text_tab(driver)

        _search(driver, keyword)

        def _has_published_only(d):
            titles = [el.text for el in d.find_elements("class name", "text_title_display")]
            return published_title in titles and draft_title not in titles

        _wait(driver).until(_has_published_only)
    finally:
        _delete_text_if_exists(published_id)
        _delete_text_if_exists(draft_id)


def test_contents_search_no_result_shows_message(driver, base_url):
    driver.get(f"{base_url}/contents")
    _switch_to_text_tab(driver)

    _search(driver, f"絶対に存在しないキーワード{randint(1,100000)}")

    no_result = driver.find_element("id", "no_result")
    _wait(driver).until(lambda d: no_result.value_of_css_property("display") != "none")
    assert "該当する内容がありません" in no_result.text


def test_contents_text_drawer_shows_main_text_on_click(driver, base_url):
    word = _get_word_string()
    keyword = f"本文表示{randint(1,100000)}"
    main_text = f"{word}{keyword}を含む詳細本文です。"
    text_id = _create_text(TEXT_OWNER_USER_ID, keyword, main_text)

    try:
        driver.get(f"{base_url}/contents")
        _switch_to_text_tab(driver)
        _search(driver, keyword)

        item_li = _find_text_item_by_title(driver, keyword)

        item_li.find_element("css selector", ".drawer_btn").click()

        content = item_li.find_element("css selector", ".drawer_content")
        assert content.is_displayed()
        assert content.text == main_text
    finally:
        _delete_text_if_exists(text_id)


# ============================================================
# 並び替え
# ============================================================

def test_contents_text_sort_date_asc_and_desc(driver, base_url):
    word = _get_word_string()
    keyword = f"並び順{randint(1,100000)}"

    first_title = f"{keyword}A"
    second_title = f"{keyword}B"

    first_id = _create_text(TEXT_OWNER_USER_ID, first_title, f"{word}{keyword}Aを含む本文です。")
    second_id = _create_text(TEXT_OWNER_USER_ID, second_title, f"{word}{keyword}Bを含む本文です。")

    try:
        driver.get(f"{base_url}/contents")
        _switch_to_text_tab(driver)
        _search(driver, keyword)

        _wait(driver).until(
            lambda d: len(d.find_elements("class name", "text_title_display")) == 2
        )

        sort_select = driver.find_element("id", "sort_select")

        Select(sort_select).select_by_value("date_asc")
        _wait(driver).until(
            lambda d: [el.text for el in d.find_elements("class name", "text_title_display")]
            == [first_title, second_title]
        )

        Select(driver.find_element("id", "sort_select")).select_by_value("date_desc")
        _wait(driver).until(
            lambda d: [el.text for el in d.find_elements("class name", "text_title_display")]
            == [second_title, first_title]
        )
    finally:
        _delete_text_if_exists(first_id)
        _delete_text_if_exists(second_id)


# ============================================================
# いいねボタン
# ============================================================

def test_contents_good_button_toggle_when_logged_in(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    keyword = f"いいねボタン{randint(1,100000)}"
    text_id = _create_text(TEXT_OWNER_USER_ID, keyword, f"{word}{keyword}を含む本文です。")

    try:
        _delete_good_text_if_exists(test_user["id"], text_id)

        logged_in_driver.get(f"{base_url}/contents")
        _switch_to_text_tab(logged_in_driver)
        _search(logged_in_driver, keyword)

        item_li = _find_text_item_by_title(logged_in_driver, keyword)

        good_button = item_li.find_element("css selector", ".good-button")
        before_count = int(item_li.find_element("css selector", ".good-count").text)

        assert "is-liked" not in good_button.get_attribute("class")

        good_button.click()

        _wait(logged_in_driver).until(
            lambda d: "is-liked" in item_li.find_element("css selector", ".good-button").get_attribute("class")
        )

        after_count = int(item_li.find_element("css selector", ".good-count").text)
        assert after_count == before_count + 1
    finally:
        _delete_good_text_if_exists(test_user["id"], text_id)
        _delete_text_if_exists(text_id)


def test_contents_good_button_shows_flash_when_not_logged_in(driver, base_url):
    word = _get_word_string()
    keyword = f"未ログインいいね{randint(1,100000)}"
    text_id = _create_text(TEXT_OWNER_USER_ID, keyword, f"{word}{keyword}を含む本文です。")

    try:
        driver.get(f"{base_url}/contents")
        _switch_to_text_tab(driver)
        _search(driver, keyword)

        item_li = _find_text_item_by_title(driver, keyword)
        item_li.find_element("css selector", ".good-button").click()

        flash = _wait(driver).until(
            lambda d: d.find_element("css selector", "#flash-messages .flash-message")
        )
        assert "ログイン" in flash.text
    finally:
        _delete_text_if_exists(text_id)