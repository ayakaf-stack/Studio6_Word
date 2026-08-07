from selenium.webdriver.common.by import By
import time


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
def test_login_empty(driver, base_url):
    url = f"{base_url}/login"

    driver.get(url)

    time.sleep(1)

    driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

    time.sleep(2)