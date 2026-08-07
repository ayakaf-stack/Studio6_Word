from random import randint

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import app as flask_app
from models.models import Text, Word, User
from models.extensions import db
from werkzeug.security import generate_password_hash
import uuid


WORD_ID = 29


# ============================================================
# テストデータ作成・削除用ヘルパー(DB直接操作)
# ============================================================

def _get_word_string():
    with flask_app.app_context():
        return db.session.get(Word, WORD_ID).word


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


def _get_text_snapshot(text_id):
    with flask_app.app_context():
        text = db.session.get(Text, text_id)
        if text is None:
            return None
        snapshot = {"title": text.title, "main_text": text.main_text, "text_status": text.text_status}
        db.session.remove()
        return snapshot


def _create_other_user():
    """login_client とは別の、認可チェック検証用のユーザーをその場で作成する"""
    email = f"other_user_{uuid.uuid4().hex}@example.com"
    with flask_app.app_context():
        user = User(
            user_name="other_test_user",
            email=email,
            password_hash=generate_password_hash("dummy_password"),
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.remove()
    return user_id


def _delete_user_if_exists(user_id):
    with flask_app.app_context():
        user = db.session.get(User, user_id)
        if user is not None:
            db.session.delete(user)
            db.session.commit()
        db.session.remove()


def _flash_texts(driver):
    elements = driver.find_elements(By.CSS_SELECTOR, "main > p")
    return [el.text for el in elements]


def _post_via_js(driver, base_url, path):
    """
    UI上のボタンを経由せず、指定パスへPOSTリクエストを直接送信する。
    (編集画面に入れないため、削除ボタンを経由できない=不正アクセスの検証用)
    """
    driver.get(f"{base_url}/")
    driver.execute_script(f"""
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '{base_url}{path}';
        document.body.appendChild(form);
        form.submit();
    """)


# ============================================================
# GET /text-edit/<id>
# ============================================================

def test_text_edit_get_requires_login(driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集GET未ログイン{randint(1,100000)}",
                            f"{word}を含む本文です。")
    try:
        driver.get(f"{base_url}/text-edit/{text_id}")
        WebDriverWait(driver, 5).until(EC.url_contains("/login"))
        assert "/login" in driver.current_url
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_get_shows_form_with_existing_values(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    title = f"編集GET本人{randint(1,100000)}"
    main_text = f"{word}を含む編集前の本文です。"
    text_id = _create_text(test_user["id"], title, main_text)
    try:
        logged_in_driver.get(f"{base_url}/text-edit/{text_id}")

        assert logged_in_driver.find_element(By.NAME, "title").get_attribute("value") == title
        assert logged_in_driver.find_element(By.NAME, "main_text").text == main_text

        heading = logged_in_driver.find_element(By.CSS_SELECTOR, "h3").text
        assert word in heading
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_get_blocks_other_users_text(logged_in_driver, base_url):
    word = _get_word_string()
    other_user_id = _create_other_user()
    text_id = _create_text(other_user_id, f"編集GET他人{randint(1,100000)}",
                            f"{word}を含む本文です。")
    try:
        logged_in_driver.get(f"{base_url}/text-edit/{text_id}")
        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))

        flashes = _flash_texts(logged_in_driver)
        assert any("他ユーザーの文章は編集できません" in f for f in flashes)
    finally:
        _delete_text_if_exists(text_id)
        _delete_user_if_exists(other_user_id)


def test_text_edit_get_404_for_nonexistent_id(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/text-edit/999999999")
    page_source = logged_in_driver.page_source
    assert "404" in logged_in_driver.title or "Not Found" in page_source


# ============================================================
# POST /text-edit/<id> - バリデーション
# ============================================================

def _fill_and_submit_edit(driver, base_url, text_id, title, main_text, submit_value="0"):
    driver.get(f"{base_url}/text-edit/{text_id}")

    title_input = driver.find_element(By.NAME, "title")
    title_input.clear()
    title_input.send_keys(title)

    main_text_input = driver.find_element(By.NAME, "main_text")
    main_text_input.clear()
    main_text_input.send_keys(main_text)

    selector = f"form.text_form button[value='{submit_value}']"
    driver.find_element(By.CSS_SELECTOR, selector).click()


def test_text_edit_missing_title_shows_flash(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    original_title = f"編集バリデ元{randint(1,100000)}"
    text_id = _create_text(test_user["id"], original_title, f"{word}を含む元の本文です。")
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title="", main_text=f"{word}を含む変更後の本文です。")

        flashes = _flash_texts(logged_in_driver)
        assert any("タイトルを入力してください" in f for f in flashes)

        snapshot = _get_text_snapshot(text_id)
        assert snapshot["title"] == original_title
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_title_too_long_shows_flash(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集バリデ長{randint(1,100000)}",
                            f"{word}を含む元の本文です。")
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title="あ" * 256, main_text=f"{word}を含む変更後の本文です。")

        flashes = _flash_texts(logged_in_driver)
        assert any("タイトルは255文字以内で入力してください" in f for f in flashes)
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_missing_main_text_shows_flash(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集バリデ本文なし{randint(1,100000)}",
                            f"{word}を含む元の本文です。")
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title="変更後タイトル", main_text="")

        flashes = _flash_texts(logged_in_driver)
        assert any("本文を入力してください" in f for f in flashes)
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_main_text_too_short_shows_flash(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集バリデ本文短{randint(1,100000)}",
                            f"{word}を含む元の本文です。")
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title="変更後タイトル", main_text="短い")

        flashes = _flash_texts(logged_in_driver)
        assert any("本文は10文字以上・400文字以内で入力してください" in f for f in flashes)
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_missing_selected_word_shows_flash(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集バリデ単語なし{randint(1,100000)}",
                            f"{word}を含む元の本文です。")
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title="変更後タイトル", main_text="対象の単語を含まない変更後の本文です。")

        flashes = _flash_texts(logged_in_driver)
        assert any(f"本文に選択した単語（{word}）が含まれていません" in f for f in flashes)
    finally:
        _delete_text_if_exists(text_id)


# ============================================================
# POST /text-edit/<id> - 認可(他人の文章)
# ============================================================

def test_text_edit_post_blocks_other_users_text(logged_in_driver, base_url):
    word = _get_word_string()
    other_user_id = _create_other_user()
    original_title = f"編集POST他人{randint(1,100000)}"
    original_main_text = f"{word}を含む元の本文です。"
    text_id = _create_text(other_user_id, original_title, original_main_text)
    try:
        _post_via_js(logged_in_driver, base_url, f"/text-edit/{text_id}")
        # このケースはJS直POSTのためフォームデータが空になるが、
        # 認可チェックはバリデーションより先に行われるため問題なく検証できる
        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))

        snapshot = _get_text_snapshot(text_id)
        assert snapshot["title"] == original_title
        assert snapshot["main_text"] == original_main_text
    finally:
        _delete_text_if_exists(text_id)
        _delete_user_if_exists(other_user_id)


# ============================================================
# POST /text-edit/<id> - 正常系
# ============================================================

def test_text_edit_success_updates_text(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集前タイトル{randint(1,100000)}",
                            f"{word}を含む編集前の本文です。")
    try:
        new_title = f"編集後タイトル{randint(1,100000)}"
        new_main_text = f"{word}を含む編集後の本文です。"

        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title=new_title, main_text=new_main_text, submit_value="0")

        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))
        flashes = _flash_texts(logged_in_driver)
        assert any("文章を編集しました" in f for f in flashes)

        page_text = logged_in_driver.find_element(By.TAG_NAME, "body").text
        assert new_title in page_text

        snapshot = _get_text_snapshot(text_id)
        assert snapshot["title"] == new_title
        assert snapshot["main_text"] == new_main_text
        assert snapshot["text_status"] == 0
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_can_set_draft_status(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"編集下書き化{randint(1,100000)}",
                            f"{word}を含む本文です。", text_status=0)
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, text_id,
                               title=f"下書き化タイトル{randint(1,100000)}",
                               main_text=f"{word}を含む下書き化本文です。", submit_value="1")

        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))

        snapshot = _get_text_snapshot(text_id)
        assert snapshot["text_status"] == 1

        page_text = logged_in_driver.find_element(By.TAG_NAME, "body").text
        assert "非公開" in page_text
    finally:
        _delete_text_if_exists(text_id)


def test_text_edit_duplicate_with_another_text_becomes_draft(logged_in_driver, base_url, test_user):
    word = _get_word_string()

    fixed_title = f"重複対象タイトル{randint(1,100000)}"
    fixed_main_text = f"{word}を含む重複対象の本文です。"
    other_text_id = _create_text(test_user["id"], fixed_title, fixed_main_text, text_status=0)

    target_text_id = _create_text(test_user["id"], f"編集対象タイトル{randint(1,100000)}",
                                   f"{word}を含む編集対象の本文です。", text_status=0)
    try:
        _fill_and_submit_edit(logged_in_driver, base_url, target_text_id,
                               title=fixed_title, main_text=fixed_main_text, submit_value="0")

        flashes = _flash_texts(logged_in_driver)
        assert any("この文章は下書き保存されます" in f for f in flashes)

        snapshot = _get_text_snapshot(target_text_id)
        assert snapshot["text_status"] == 1
    finally:
        _delete_text_if_exists(target_text_id)
        _delete_text_if_exists(other_text_id)


# ============================================================
# GET /text-delete/<id> - 許可されていないメソッド
# ============================================================

def test_text_delete_get_not_allowed(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"削除GET不可{randint(1,100000)}",
                            f"{word}を含む本文です。")
    try:
        logged_in_driver.get(f"{base_url}/text-delete/{text_id}")
        page_source = logged_in_driver.page_source
        assert "405" in logged_in_driver.title or "Method Not Allowed" in page_source
    finally:
        _delete_text_if_exists(text_id)


# ============================================================
# POST /text-delete/<id> - 認可
# ============================================================

def test_text_delete_requires_login(driver, base_url, test_user):
    word = _get_word_string()
    text_id = _create_text(test_user["id"], f"削除未ログイン{randint(1,100000)}",
                            f"{word}を含む本文です。")
    try:
        _post_via_js(driver, base_url, f"/text-delete/{text_id}")
        WebDriverWait(driver, 5).until(EC.url_contains("/login"))

        assert _get_text_snapshot(text_id) is not None  # 削除されていない
    finally:
        _delete_text_if_exists(text_id)


def test_text_delete_blocks_other_users_text(logged_in_driver, base_url):
    word = _get_word_string()
    other_user_id = _create_other_user()
    text_id = _create_text(other_user_id, f"削除他人{randint(1,100000)}",
                            f"{word}を含む本文です。")
    try:
        _post_via_js(logged_in_driver, base_url, f"/text-delete/{text_id}")
        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))

        flashes = _flash_texts(logged_in_driver)
        assert any("他ユーザーの文章は削除できません" in f for f in flashes)
        assert _get_text_snapshot(text_id) is not None  # 削除されていない
    finally:
        _delete_text_if_exists(text_id)
        _delete_user_if_exists(other_user_id)


# ============================================================
# POST /text-delete/<id> - 正常系(編集画面の削除ボタンから実際に操作)
# ============================================================

def test_text_delete_success_via_edit_page_button(logged_in_driver, base_url, test_user):
    word = _get_word_string()
    title = f"削除対象{randint(1,100000)}"
    text_id = _create_text(test_user["id"], title, f"{word}を含む本文です。")

    try:
        logged_in_driver.get(f"{base_url}/text-edit/{text_id}")

        delete_button = logged_in_driver.find_element(By.CSS_SELECTOR, "form.delete_form button.btn-delete")
        delete_button.click()

        WebDriverWait(logged_in_driver, 3).until(EC.alert_is_present())
        logged_in_driver.switch_to.alert.accept()

        WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))
        flashes = _flash_texts(logged_in_driver)
        assert any("文章を削除しました" in f for f in flashes)

        page_text = logged_in_driver.find_element(By.TAG_NAME, "body").text
        assert title not in page_text

        assert _get_text_snapshot(text_id) is None
    finally:
        _delete_text_if_exists(text_id)  # 万一削除されていなかった場合の保険