from selenium import webdriver
import time

def view_top_page():

    driver = webdriver.Chrome()

    url = "http://127.0.0.1:5000/"
    # アクセス
    driver.get(url)
    # ページタイトル<title>取得
    title = driver.title
    print(title)
    


    # 2秒停止
    time.sleep(2)
    # 終了
    driver.quit()


if __name__ == "__main__":
    view_top_page()

