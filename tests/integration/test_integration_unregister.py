from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import app as flask_app
from models.models import Text
from models.extensions import db
import time

#============================================================
# 後片付け用ヘルパー(test_user と同じ流儀でDB直接操作)
#============================================================

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
    driver.get(f"{base_url}/text-new/10")
    driver.find_element(By.NAME, "title").send_keys(title)
    driver.find_element(By.NAME, "main_text").send_keys(main_text)
 
    selector = f"form.text_form button[value='{submit_value}']"
    driver.find_element(By.CSS_SELECTOR, selector).click()

#============================================================
# 未ログイン時のアクセス
#============================================================ 

def test_unregister_requires_login_redirects(driver, base_url):
    driver.get(f"{base_url}/unregister")

    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "/login" in driver.current_url


# ============================================================
# フォーム表示
# ============================================================

def test_unregister_page_shows_form(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/unregister")

    heading = logged_in_driver.find_element(By.CSS_SELECTOR, "h1").text
    assert "退会画面" in heading

    form = logged_in_driver.find_element(By.CSS_SELECTOR, "form").text
    assert "退会すると作成した文章、いいねが全て削除されることに同意します。" in form

    button = logged_in_driver.find_element(By.CSS_SELECTOR, "button").text
    assert "退会する" in button

def test_unregister_cansel_link_goes_to_mypage(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/unregister")

    cancel_link = logged_in_driver.find_element(By.LINK_TEXT, "戻る")
    cancel_link.click()

    WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/mypage"))
    assert "/mypage" in logged_in_driver.current_url



# ============================================================
# バリデーションエラー
# ============================================================

def test_unregister_missing_password_shows_error(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/unregister")

    # パスワードを入力せずに退会ボタンをクリック
    logged_in_driver.find_element(By.CSS_SELECTOR, "button").click()

    # エラーメッセージが表示されることを確認
    flashes = _flash_texts(logged_in_driver)
    assert any("パスワードを入力し、注意事項に同意してください" in f for f in flashes)

def test_unregister_missing_checkbox_shows_error(logged_in_driver, base_url,test_user):
    logged_in_driver.get(f"{base_url}/unregister")

    # パスワードを入力して、チェックボックスを未チェックのまま退会ボタンをクリック
    logged_in_driver.find_element(By.NAME, "password").send_keys(test_user["password"])
    logged_in_driver.find_element(By.CSS_SELECTOR, "button").click()

    flashes = _flash_texts(logged_in_driver)
    assert any("パスワードを入力し、注意事項に同意してください" in f for f in flashes)

def test_unregister_incorrect_password_shows_error(logged_in_driver, base_url):
    logged_in_driver.get(f"{base_url}/unregister")

    # 間違ったパスワードを入力して、チェックボックスをチェックして退会ボタンをクリック
    logged_in_driver.find_element(By.NAME, "password").send_keys("wrongpassword")
    logged_in_driver.find_element(By.ID, "check_").click()
    logged_in_driver.find_element(By.CSS_SELECTOR, "button").click()

    flashes = _flash_texts(logged_in_driver)
    assert any("パスワードが正しくありません" in f for f in flashes)


#============================================================
# 退会成功
#============================================================

def test_unregister_success(logged_in_driver, base_url, test_user):
    logged_in_driver.get(f"{base_url}/unregister")

    # 正しいパスワードを入力して、チェックボックスをチェックして退会ボタンをクリック
    logged_in_driver.find_element(By.NAME, "password").send_keys(test_user["password"])
    logged_in_driver.find_element(By.ID, "check_").click()
    logged_in_driver.find_element(By.CSS_SELECTOR, "button").click()

    # マイページにリダイレクトされ、フラッシュメッセージが表示されることを確認
    WebDriverWait(logged_in_driver, 5).until(EC.url_contains("/"))
    assert "/" in logged_in_driver.current_url

    flashes = _flash_texts(logged_in_driver)
    assert any("ユーザー情報が削除されました" in f for f in flashes)

def test_unregister_deletes_user_data(logged_in_driver, base_url, test_user):
    driver = logged_in_driver
    driver.get(f"{base_url}/text-new/10")
    target_word = driver.find_element(By.CSS_SELECTOR, "h3").text.replace("選択した単語：", "")
    title = "退会前に作成したテスト文章"
    main_text = f"この文章は退会前に作成されたテスト文章です。選択した単語は {target_word} です。"

    
    _fill_and_submit(driver, base_url, title=title, main_text=main_text, submit_value="0")

    WebDriverWait(driver, 5).until(EC.url_contains("/mypage"))
    flashes = _flash_texts(driver)
    assert any("文章を作成しました" in f for f in flashes)

    # 作成した文章がDBに存在することを確認
    with flask_app.app_context():
        from models.models import User, Text
        user = User.query.filter_by(email=test_user["email"]).first()
        assert user is not None

        text = Text.query.filter_by(user_id=user.id, title=title).first()
        assert text is not None

    logged_in_driver.get(f"{base_url}/unregister")

    # 正しいパスワードを入力して、チェックボックスをチェックして退会ボタンをクリック
    logged_in_driver.find_element(By.NAME, "password").send_keys(test_user["password"])
    logged_in_driver.find_element(By.ID, "check_").click()
    logged_in_driver.find_element(By.CSS_SELECTOR, "button").click()

    time.sleep(3)  # フラッシュメッセージが表示されるまで少し待つ

    # ユーザー情報が削除されたことを確認するために、DBを直接確認
    with flask_app.app_context():
        from models.models import User
        user = User.query.filter_by(email=test_user["email"]).first()
        assert user is None

    with flask_app.app_context():
        from models.models import Text
        text = Text.query.filter_by(title=title).first()
        assert text is None