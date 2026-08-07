from random import randint

import pytest
from flask import session
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait

from app import app as flask_app
from models.extensions import db
from models.models import Word, Genre, Word_genre


# ============================================================
# 管理者としてログイン済み状態のdriverを作るフィクスチャ
# ============================================================

def _build_admin_session_cookie():
    with flask_app.test_request_context():
        session["is_admin"] = True
        serializer = flask_app.session_interface.get_signing_serializer(flask_app)
        return serializer.dumps(dict(session))


@pytest.fixture
def admin_driver(driver, base_url):
    cookie_value = _build_admin_session_cookie()
    cookie_name = flask_app.config.get("SESSION_COOKIE_NAME", "session")

    # Cookieをセットするには、先に同一オリジンへアクセスしておく必要がある
    driver.get(base_url)
    driver.add_cookie({
        "name": cookie_name,
        "value": cookie_value,
        "path": "/",
    })

    driver.get(f"{base_url}/admin")

    return driver


# ============================================================
# テストデータ作成・削除用ヘルパー
# ============================================================

def _create_word():
    suffix = randint(1, 1000000)
    with flask_app.app_context():
        word = Word(
            word=f"テスト単語{suffix}",
            reading=f"てすとたんご{suffix}",
            mean="Selenium結合テスト用の単語です。",
        )
        db.session.add(word)
        db.session.commit()
        word_id = word.id
        word_text = word.word
        reading_text = word.reading
        db.session.remove()
        return word_id, word_text, reading_text


def _delete_word_if_exists(word_id):
    with flask_app.app_context():
        Word_genre.query.filter_by(word_id=word_id).delete()
        word = db.session.get(Word, word_id)
        if word is not None:
            db.session.delete(word)
        db.session.commit()
        db.session.remove()


def _create_genre():
    suffix = randint(1, 1000000)
    with flask_app.app_context():
        genre = Genre(genre=f"テストジャンル{suffix}")
        db.session.add(genre)
        db.session.commit()
        genre_id = genre.id
        genre_name = genre.genre
        db.session.remove()
        return genre_id, genre_name


def _delete_genre_if_exists(genre_id):
    with flask_app.app_context():
        Word_genre.query.filter_by(genre_id=genre_id).delete()
        genre = db.session.get(Genre, genre_id)
        if genre is not None:
            db.session.delete(genre)
        db.session.commit()
        db.session.remove()


def _link_word_genre(word_id, genre_id):
    with flask_app.app_context():
        db.session.add(Word_genre(word_id=word_id, genre_id=genre_id))
        db.session.commit()
        db.session.remove()


def _get_word_genre_ids(word_id):
    with flask_app.app_context():
        ids = {wg.genre_id for wg in Word_genre.query.filter_by(word_id=word_id).all()}
        db.session.remove()
        return ids


# ============================================================
# 画面操作用ヘルパー
# ============================================================

def _wait(driver, timeout=5):
    return WebDriverWait(driver, timeout, ignored_exceptions=(StaleElementReferenceException,))


def _radio_for_word(driver, word_id):
    return driver.find_element(
        "css selector", f'input[name="selected_word"][value="{word_id}"]'
    )


def _li_for_word(driver, word_id):
    return _radio_for_word(driver, word_id).find_element("xpath", "./ancestor::li")


def _genre_tag_texts(driver, word_id):
    li = _li_for_word(driver, word_id)
    return [el.text for el in li.find_elements("class name", "genre_tag")]


def _checkbox_for_genre(driver, genre_id):
    return driver.find_element(
        "css selector", f'input[name="selected_genre"][value="{genre_id}"]'
    )


# ============================================================
# アクセス制御
# ============================================================

def test_admin_redirects_to_login_when_not_logged_in(driver, base_url):
    driver.get(f"{base_url}/admin")

    _wait(driver).until(lambda d: "/login" in d.current_url)
    assert "/login" in driver.current_url


def test_admin_redirects_to_login_for_normal_user(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/admin")

    _wait(logged_in_driver).until(lambda d: "/login" in d.current_url)
    assert "/login" in logged_in_driver.current_url


# ============================================================
# 絞り込み
# ============================================================

def test_admin_filter_none_and_has(admin_driver, base_url):
    tagged_id, tagged_word, _ = _create_word()
    untagged_id, untagged_word, _ = _create_word()
    genre_id, _ = _create_genre()

    def _tagged_present(d):
        return bool(d.find_elements("css selector", f'input[name="selected_word"][value="{tagged_id}"]'))

    def _untagged_present(d):
        return bool(d.find_elements("css selector", f'input[name="selected_word"][value="{untagged_id}"]'))

    try:
        _link_word_genre(tagged_id, genre_id)

        admin_driver.get(f"{base_url}/admin")

        # 「登録済みのみ」: タグ付き単語だけが表示される状態になるまで待つ
        # (タグ付き単語は絞り込み前の「すべて」表示にも含まれるため、
        #  存在確認だけでは絞り込み前後を区別できない。
        #  「存在してほしいもの」と「存在してほしくないもの」を
        #  1つの条件として同時に満たすまで待つ)
        admin_driver.find_element("css selector", '.filter_btn[data-filter="has"]').click()
        _wait(admin_driver).until(lambda d: _tagged_present(d) and not _untagged_present(d))

        # 「未登録のみ」: タグなし単語だけが表示される状態になるまで待つ
        admin_driver.find_element("css selector", '.filter_btn[data-filter="none"]').click()
        _wait(admin_driver).until(lambda d: _untagged_present(d) and not _tagged_present(d))

        # 「すべて」: 両方表示される状態になるまで待つ
        admin_driver.find_element("css selector", '.filter_btn[data-filter="all"]').click()
        _wait(admin_driver).until(lambda d: _tagged_present(d) and _untagged_present(d))
    finally:
        _delete_word_if_exists(tagged_id)
        _delete_word_if_exists(untagged_id)
        _delete_genre_if_exists(genre_id)


# ============================================================
# 単語選択時の既存ジャンルのチェック復元
# ============================================================

def test_admin_selecting_word_checks_existing_genres(admin_driver, base_url):
    word_id, _, _ = _create_word()
    genre_id_1, _ = _create_genre()
    genre_id_2, _ = _create_genre()

    try:
        _link_word_genre(word_id, genre_id_1)
        _link_word_genre(word_id, genre_id_2)

        admin_driver.get(f"{base_url}/admin")

        radio = _radio_for_word(admin_driver, word_id)
        radio.click()

        checkbox_1 = _checkbox_for_genre(admin_driver, genre_id_1)
        checkbox_2 = _checkbox_for_genre(admin_driver, genre_id_2)

        _wait(admin_driver).until(lambda d: checkbox_1.is_selected() and checkbox_2.is_selected())
    finally:
        _delete_word_if_exists(word_id)
        _delete_genre_if_exists(genre_id_1)
        _delete_genre_if_exists(genre_id_2)


# ============================================================
# 登録(追加・削除)
# ============================================================

def test_admin_register_adds_genre_to_untagged_word(admin_driver, base_url):
    word_id, _, _ = _create_word()
    genre_id, genre_name = _create_genre()

    try:
        admin_driver.get(f"{base_url}/admin")

        _radio_for_word(admin_driver, word_id).click()
        _checkbox_for_genre(admin_driver, genre_id).click()
        admin_driver.find_element("id", "register_btn").click()

        flash = _wait(admin_driver).until(
            lambda d: d.find_element("css selector", "#flash-messages .flash-message")
        )
        assert "ジャンルを更新しました" in flash.text

        # 再描画後、その単語にジャンルタグが付いていることを確認
        _wait(admin_driver).until(
            lambda d: genre_name in _genre_tag_texts(d, word_id)
        )

        # DB側でも紐付けが作られていることを確認
        assert _get_word_genre_ids(word_id) == {genre_id}
    finally:
        _delete_word_if_exists(word_id)
        _delete_genre_if_exists(genre_id)


def test_admin_register_removes_genre_from_tagged_word(admin_driver, base_url):
    word_id, _, _ = _create_word()
    genre_id, genre_name = _create_genre()

    try:
        _link_word_genre(word_id, genre_id)

        admin_driver.get(f"{base_url}/admin")

        _radio_for_word(admin_driver, word_id).click()

        checkbox = _checkbox_for_genre(admin_driver, genre_id)
        _wait(admin_driver).until(lambda d: checkbox.is_selected())
        checkbox.click()  # チェックを外す

        admin_driver.find_element("id", "register_btn").click()

        flash = _wait(admin_driver).until(
            lambda d: d.find_element("css selector", "#flash-messages .flash-message")
        )
        assert "ジャンルを更新しました" in flash.text

        _wait(admin_driver).until(
            lambda d: genre_name not in _genre_tag_texts(d, word_id)
        )

        assert _get_word_genre_ids(word_id) == set()
    finally:
        _delete_word_if_exists(word_id)
        _delete_genre_if_exists(genre_id)


def test_admin_register_without_selecting_word_shows_message(admin_driver, base_url):
    admin_driver.get(f"{base_url}/admin")

    admin_driver.find_element("id", "register_btn").click()

    flash = _wait(admin_driver).until(
        lambda d: d.find_element("css selector", "#flash-messages .flash-message")
    )
    assert "単語を選択してください" in flash.text