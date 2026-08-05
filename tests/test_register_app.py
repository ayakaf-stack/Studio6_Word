import pytest
from werkzeug.security import check_password_hash
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING']=True

    with app.test_client() as client:
        with app.app_context():
            yield client

# 登録画面(GET)
def test_register_get(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert "新規登録".encode("utf-8") in response.data


# 登録完了(POST)
def test_register_success(client):

    response = client.post("/register", data={
        "user_name": "test_user",
        "email": "test_user@test.com",
        "password": "password123"
    })

    assert response.status_code == 302
    assert "/register" in response.location

# DBに登録されたことを確認
    user = User.query.filter_by(
        email="test_user@test.com"
    ).first()

    assert user is not None
    assert user.user_name == "test_user"

# ユーザー名未入力チェック
def test_register_user_name(client):
    response = client.post("/register", date={
        "user_name" : "",
        "email" : "test@test.com",
        "password" : "password123"
    })

    assert response.status_code == 302
    assert "/register" in response.location

# メールアドレス未入力
def test_register_empty_email(client):

    response = client.post("/register", data={
        "user_name" : "test_user",
        "email" : "",
        "passwprd" : "password123"
    })

    assert response.status_code == 302
    assert "/register" in response.location

# パスワード未入力
def test_register_empty_password(client):

    response = client.post("/register", data={
        "user_name" : "test_user",
        "email" : "test@test.com",
        "password" : ""
    })

    assert response.status_code == 302
    assert "/register" in response.location

# Flashメッセージ
def test_register_empty_flash(client):

    response = client.post("/register", data={
        "user_name" : "",
        "email" : "",
        "password" : ""
    })

    html = response.data.decode("utf-8")

    assert "全ての項目を正しく入力してください" in html


# ユーザー名255文字以上


# 不正なメールアドレス


# パスワード8文字未満


# パスワード16文字以上


# 重複メールアドレス

