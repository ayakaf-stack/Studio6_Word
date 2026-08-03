import pytest
from app import app

# テストクライアントを作成
@pytest.fixture
def client():
    app.config['TESTING']=True

    with app.test_client() as client:
        yield client

# トップページのテスト
def test_index(client):
    response = client.get("/")
    # StatusCode 200の確認
    assert response.status_code == 200
    # 出力文字の確認
    html = response.get_data(as_text=True)
    assert "美しい日本語" in html

# ログインのテスト
def test_login_safe(client):
    # 認証後302リダイレクトを確認
    response = client.post(
        "/login",
        data={
            "email": "takujiozaki@gmail.com",
            "password": "abcd1234"
        }
    )

    assert response.status_code == 302

# ログインのテスト(失敗)
def test_login_fail(client):
    # 認証失敗からリダイレクト
    response = client.post(
        "/login",
        data={
            "email": "takujiozaki@gmail.com",
            "password": "abcd4567"
        },
        follow_redirects=True
     )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # フラッシュメッセージを確認
    assert "ログインに失敗しました" in html
