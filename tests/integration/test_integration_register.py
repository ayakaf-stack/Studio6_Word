from selenium.webdriver.common.by import By
import time
import uuid

# 新規登録画面表示
def test_show_register_page(driver, base_url):
    url = f"{base_url}/register"

    driver.get(url)

    time.sleep(1)

    title = driver.find_element(By.TAG_NAME,"h1").text

    assert title == "新規登録"


# 正常登録
def test_show_register_success(driver, base_url):
    url = f"{base_url}/register"

    driver.get(url)

    user_name = f"test_{uuid.uuid4(). hex}user"
    email = f"test_{uuid.uuid4(). hex}@ezample.com"
    password = f"password{uuid.uuid4(). hex}"

    driver.find_element(
        By.NAME,
        "user_name"
    ).send_keys(user_name)


    driver.find_element(
        By.NAME,
        "email"
    ).send_keys(email)


    driver.find_element(
        By.NAME,
        "password"
    ).send_keys(password)


    driver.find_element(
        By.CSS_SELECTOR,
        "button[type='submit']"
    ).click()


    time.sleep(2)

    # ログイン画面へ遷移確認
    assert "/login" in driver.current_url


# 空欄エラー
def test_register_empty(driver, base_url):

    driver.get(f"{base_url}/register")

    driver.find_element(
        By.NAME,
        "user_name"
    ).send_keys("")


    driver.find_element(
        By.NAME,
        "email"
    ).send_keys("")


    driver.find_element(
        By.NAME,
        "password"
    ).send_keys("")


    driver.find_element(
        By.CSS_SELECTOR,
        "button[type='submit']"
    ).click()


    time.sleep(1)

    # エラーメッセージ確認
    message = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text

    assert "全ての項目を正しく入力してください" in message

# 重複メールエラー
def test_register_duplicate_email(driver, base_url):

    driver.get(f"{base_url}/register")

    driver.find_element(
        By.NAME,
        "user_name"
    ).send_keys("test_user")


    driver.find_element(
        By.NAME,
        "email"
    ).send_keys("already@test.com")


    driver.find_element(
        By.NAME,
        "password"
    ).send_keys("password123")


    driver.find_element(
        By.CSS_SELECTOR,
        "button[type='submit']"
    ).click()


    time.sleep(1)

    # エラーメッセージ確認
    message = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text

    assert "既に登録済みのメールアドレス" in message