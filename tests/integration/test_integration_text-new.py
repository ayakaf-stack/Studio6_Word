from random import randint
 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
 
from app import app as flask_app
from models.models import Text
from models.extensions import db
 
 
WORD_ID = 29
 
 
# ============================================================
# 後片付け用ヘルパー(test_user と同じ流儀でDB直接操作)
# ============================================================
 
def _delete_texts_by_title(user_id, title):
    with flask_app.app_context():
        texts = Text.query.filter_by(user_id=user_id, title=title).all()
        for text in texts:
            db.session.delete(text)
        db.session.commit()
        db.session.remove()
        return len(texts)
 
 
def _flash_texts(driver):
    """base.html の <main> 直下に描画されるフラッシュメッセージの文字列一覧を取得する"""
    elements = driver.find_elements(By.CSS_SELECTOR, "main > p")
    return [el.text for el in elements]
 
 
def _fill_and_submit(driver, base_url, title, main_text, submit_value="0"):
    driver.get(f"{base_url}/text-new/{WORD_ID}")
    driver.find_element(By.NAME, "title").send_keys(title)
    driver.find_element(By.NAME, "main_text").send_keys(main_text)
 
    selector = f"form.text_form button[value='{submit_value}']"
    driver.find_element(By.CSS_SELECTOR, selector).click()
 
 
# ============================================================
# 未ログイン時のアクセス
# ============================================================
 
def test_text_new_requires_login_redirects(driver, base_url):
    driver.get(f"{base_url}/text-new/{WORD_ID}")
 
    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "/login" in driver.current_url
 
 
# ============================================================
# フォーム表示
# ============================================================
 
def test_text_new_page_shows_selected_word_and_form(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/text-new/{WORD_ID}")
 
    heading = logged_in_driver.find_element(By.CSS_SELECTOR, "h3").text
    assert "選択した単語" in heading
 
    hidden_word = logged_in_driver.find_element(By.NAME, "word")
    assert hidden_word.get_attribute("value") == str(WORD_ID)
 
    assert logged_in_driver.find_element(By.NAME, "title") is not None
    assert logged_in_driver.find_element(By.NAME, "main_text") is not None
 
    buttons = logged_in_driver.find_elements(By.CSS_SELECTOR, "form.text_form button[type='submit']")
    assert len(buttons) == 2  # 投稿・下書き保存
 
 
def test_text_new_cancel_link_goes_to_mypage_without_creating(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/text-new/{WORD_ID}")
 
    logged_in_driver.find_element(By.LINK_TEXT, "キャンセル").click()
 
    WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))
    assert "/mypage" in logged_in_driver.current_url
 
 
# ============================================================
# バリデーション(いずれも同画面にフラッシュメッセージが表示される)
# ============================================================
 
def test_text_new_missing_title_shows_flash(logged_in_driver, base_url):
    _fill_and_submit(logged_in_driver, base_url, title="", main_text="タイトルなしで投稿しようとするテスト本文です。")
 
    flashes = _flash_texts(logged_in_driver)
    assert any("タイトルを入力してください" in f for f in flashes)
 
 
def test_text_new_title_too_long_shows_flash(logged_in_driver, base_url):
    _fill_and_submit(logged_in_driver, base_url, title="あ" * 256, main_text="タイトルが長すぎる場合のテスト本文です。")
 
    flashes = _flash_texts(logged_in_driver)
    assert any("タイトルは255文字以内で入力してください" in f for f in flashes)
 
 
def test_text_new_missing_main_text_shows_flash(logged_in_driver, base_url):
    _fill_and_submit(logged_in_driver, base_url, title="本文なしテスト", main_text="")
 
    flashes = _flash_texts(logged_in_driver)
    assert any("本文を入力してください" in f for f in flashes)
 
 
def test_text_new_main_text_too_short_shows_flash(logged_in_driver, base_url):
    _fill_and_submit(logged_in_driver, base_url, title="本文短すぎテスト", main_text="短い")
 
    flashes = _flash_texts(logged_in_driver)
    assert any("本文は10文字以上・400文字以内で入力してください" in f for f in flashes)
 
 
def test_text_new_missing_selected_word_shows_flash(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/text-new/{WORD_ID}")
    target_word = logged_in_driver.find_element(By.CSS_SELECTOR, "h3").text.replace("選択した単語：", "")
 
    _fill_and_submit(
        logged_in_driver, base_url,
        title="対象単語なしテスト",
        main_text="この本文には対象の単語がわざと含まれていません。",
    )
 
    flashes = _flash_texts(logged_in_driver)
    assert any(f"本文に選択した単語（{target_word}）が含まれていません" in f for f in flashes)
 
 
# ============================================================
# 正常系
# ============================================================
 
def test_text_new_success_publish(logged_in_driver, base_url, test_user):
    driver = logged_in_driver
    driver.get(f"{base_url}/text-new/{WORD_ID}")
    target_word = driver.find_element(By.CSS_SELECTOR, "h3").text.replace("選択した単語：", "")
 
    title = f"結合テスト投稿{randint(1, 100000)}"
    main_text = f"{target_word}に関する結合テスト用の本文です。"
 
    try:
        _fill_and_submit(driver, base_url, title=title, main_text=main_text, submit_value="0")
 
        WebDriverWait(driver, 5).until(EC.url_contains("/mypage"))
        flashes = _flash_texts(driver)
        assert any("文章を作成しました" in f for f in flashes)
 
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert title in page_text
    finally:
        deleted_count = _delete_texts_by_title(test_user["id"], title)
        assert deleted_count == 1
 
 
def test_text_new_success_draft(logged_in_driver, base_url, test_user):
    driver = logged_in_driver
    driver.get(f"{base_url}/text-new/{WORD_ID}")
    target_word = driver.find_element(By.CSS_SELECTOR, "h3").text.replace("選択した単語：", "")
 
    title = f"結合テスト下書き{randint(1, 100000)}"
    main_text = f"{target_word}に関する下書き確認用の本文です。"
 
    try:
        _fill_and_submit(driver, base_url, title=title, main_text=main_text, submit_value="1")
 
        WebDriverWait(driver, 5).until(EC.url_contains("/mypage"))
 
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert title in page_text
        assert "非公開" in page_text
    finally:
        deleted_count = _delete_texts_by_title(test_user["id"], title)
        assert deleted_count == 1