import time
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:5000"


# 1. トップページ表示テスト
def test_show_top_page():
    driver = webdriver.Chrome()
    
    # アクセス
    driver.get(BASE_URL)
   
    # ページタイトル<title>取得
    title = driver.title

    # テスト
    assert title == "美しい日本語"
    
    # 2秒停止
    time.sleep(2)
    # 終了
    driver.quit()


# 2. 既存ログイン/ログアウトテスト
def test_login_to_mypage():
    driver = webdriver.Chrome()
    url = f"{BASE_URL}/login"
    driver.get(url)

    time.sleep(1)

    # メール入力欄を取得(#mail)
    mail = driver.find_element(By.ID, "mail")
    mail.send_keys("takujiozaki@gmail.com")

    # パスワード入力欄を取得(#Password)
    password = driver.find_element(By.ID, "Password")
    password.send_keys("abcd1234")

    time.sleep(1)

    # submitボタン取得＆クリック
    button = driver.find_element(By.TAG_NAME, "button")
    button.click()

    time.sleep(1)

    # テスト(ユーザー名、マイページの表示を確認)
    h1_element = driver.find_element(By.TAG_NAME, "h1").text
    assert h1_element == "マイページ"
    h2_elements = driver.find_elements(By.TAG_NAME, "h2")
    assert h2_elements[0].text == "ログインユーザー：ozaki"

    # ログアウト
    logout = driver.find_element(By.CLASS_NAME, "logout-btn")
    logout.click()

    time.sleep(2)

    # ログアウトメッセージ(flash)の取得
    main_element = driver.find_element(By.TAG_NAME, "main")
    flash_message = main_element.find_element(By.TAG_NAME, "p").text
    assert flash_message == "ログアウトしました"
    
    # 終了
    driver.quit()


# 3. 新規登録テスト（E2E-01）
def test_register_flow():
    driver = webdriver.Chrome()
    url = f"{BASE_URL}/register"
    driver.get(url)

    time.sleep(1)

    # 毎回ユニークなメールアドレスを生成（重複エラー防止）
    unique_email = f"user_{int(time.time())}@example.com"

    # 新規登録フォーム入力
    user_name = driver.find_element(By.NAME, "user_name")
    user_name.send_keys("Seleniumユーザー")

    email = driver.find_element(By.NAME, "email")
    email.send_keys(unique_email)

    password = driver.find_element(By.NAME, "password")
    password.send_keys("password123")

    time.sleep(1)

    # 送信
    button = driver.find_element(By.TAG_NAME, "button")
    button.click()

    time.sleep(1)

    # フラッシュメッセージ確認
    main_element = driver.find_element(By.TAG_NAME, "main")
    flash_message = main_element.find_element(By.TAG_NAME, "p").text
    assert flash_message == "新規登録が完了しました"

    driver.quit()


# 4. いいねボタン非同期操作テスト（E2E-02）
def test_good_button_ajax():
    driver = webdriver.Chrome()
    
    # トップページ（トップ画面）へアクセス
    driver.get(BASE_URL)
    time.sleep(1)

    # クラス名 "good-button" のボタンを取得（トップページの単語いいねボタン）
    good_buttons = driver.find_elements(By.CLASS_NAME, "good-button")
    assert len(good_buttons) > 0, "トップページにいいねボタン(good-button)が見つかりませんでした"

    # いいねボタンをクリック
    good_btn = good_buttons[0]
    good_btn.click()

    time.sleep(1)  # Ajax通信待ち

    driver.quit()


# 5. 未ログイン時のガード制御テスト（E2E-03）
def test_access_guard():
    driver = webdriver.Chrome()

    # 未ログイン状態で直接マイページへアクセス
    driver.get(f"{BASE_URL}/mypage")

    time.sleep(1)

    # ログイン画面にリダイレクトされ、h1が「ログイン」であることを確認
    h1_element = driver.find_element(By.TAG_NAME, "h1").text
    assert h1_element == "ログイン"

    driver.quit()