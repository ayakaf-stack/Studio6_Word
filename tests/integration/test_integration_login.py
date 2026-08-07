from selenium.webdriver.common.by import By
import time


# ログイン画面表示
def test_login_page(driver, base_url):
    url = f"{base_url}/login"

    driver.get(url)

    time.sleep(1)

    title = driver.find_element(By.TAG_NAME,"h1").text

    assert title == "ログイン"


# ログイン成功
"""
ログイン画面を開きemailとpasswordを入力してログインボタンクリックでマイページへ遷移
"""
def test_login_success(driver, base_url, test_user):
    url = f"{base_url}/login"

    driver.get(url)

    email = test_user["email"]
    password = test_user["password"]

    driver.find_element(
            By.NAME,
            "email"
        ).send_keys(email)

    driver.find_element(
            By.NAME,
            "password"
        ).send_keys(password)
    
    time.sleep(2)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)

    # マイページ画面へ遷移確認
    assert "/mypage" in driver.current_url


# ログイン失敗
"""
空欄エラー
"""
# メールアドレスが未入力
def test_login_empty_email(driver, base_url, test_user):
    url = f"{base_url}/login"

    driver.get(url)

    driver.find_element(
            By.NAME,
            "password"
        ).send_keys("password")

    time.sleep(1)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)

# パスワードが未入力
def test_login_empty_password(driver, base_url, test_user):
    url = f"{base_url}/login"

    driver.get(url)

    driver.find_element(
            By.NAME,
            "email"
        ).send_keys("email@email.com")

    time.sleep(1)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)


"""
整合性エラー
"""
# メールアドレスが違う時
def test_login_wrong_email(driver, base_url, test_user):
    url = f"{base_url}/login"

    driver.get(url)

    password = test_user["password"]

    driver.find_element(
            By.NAME,
            "email"
        ).send_keys("email@email.com")

    driver.find_element(
            By.NAME,
            "password"
        ).send_keys(password)
    
    time.sleep(2)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)

# パスワードが違う時
def test_login_wrong_password(driver, base_url, test_user):
    url = f"{base_url}/login"

    driver.get(url)

    email = test_user["email"]

    driver.find_element(
            By.NAME,
            "email"
        ).send_keys(email)

    driver.find_element(
            By.NAME,
            "password"
        ).send_keys("password")
    
    time.sleep(2)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)


# 新規登録ボタン
"""
ログイン画面を開き新規登録ボタンクリックで新規登録画面へ遷移
"""
def test_login_register(driver, base_url):
    url = f"{base_url}/login"

    driver.get(url)

    time.sleep(2)

    register = driver.find_element(By.LINK_TEXT, "新規登録")
    assert register.text == "新規登録"
    # 新規登録クリック
    register.click()

    time.sleep(2)