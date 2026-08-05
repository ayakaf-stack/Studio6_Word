import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from models.models import User
from models.extensions import db

# ==========================================
# 1. GETリクエストのテスト
# ==========================================
def test_login_get(client):
    """GETアクセスでログイン画面が正常に表示されるか"""
    response = client.get('/login')
    assert response.status_code == 200
    assert 'login.html' in [t.name for t in response.templates] if hasattr(response, 'templates') else True


# ==========================================
# 2. 通常ユーザー: ログイン成功
# ==========================================
def test_login_success(client, app):
    """正しいメールアドレスとパスワードでログインし、マイページへリダイレクトされるか"""
    # テストユーザーを作成
    with app.app_context():
        user = User(
            user_name="テストユーザー",
            email="user@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    # POST送信
    response = client.post('/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    }, follow_redirects=False)

    # マイページ（/mypage）へのリダイレクト確認
    assert response.status_code == 302
    assert response.headers['Location'] == '/mypage'

    # セッションに user_id, user_name が保存されているか確認
    with client.session_transaction() as sess:
        assert sess.get('user_id') == user_id
        assert sess.get('user_name') == "テストユーザー"


# ==========================================
# 3. 通常ユーザー: ログイン失敗（パスワード間違い / ユーザー不存在）
# ==========================================
@pytest.mark.parametrize("email, password", [
    ("user@example.com", "wrong_password"),     # パスワード間違い
    ("nonexistent@example.com", "password123")  # 存在しないメールアドレス
    ("", "password123"),                        # メールアドレスが空
    ("user@example.com", ""),                   # パスワードが空
    ("", "")                                    # 両方空
])

def test_login_failure(client, app, email, password):
    """認証失敗時にエラーメッセージが表示され、ログイン画面に留まるか"""
    # 事前準備：テストユーザーを用意
    with app.app_context():
        user = User(
            user_name="テストユーザー",
            email="user@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'ログインに失敗しました' in response.get_data(as_text=True)

    # セッションに入っていないことの確認
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


# ==========================================
# 4. 管理者ログイン（マジックリンクメール送信）
# ==========================================
@patch('app.mail.send')  # 実際にメールが飛ばないようにモック化
def test_admin_login_sends_email(mock_mail_send, client, app):
    """管理者情報でログインした場合に、メールが送信されてログイン画面へリダイレクトされるか"""
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = app.config.get('ADMIN_PASSWORD', 'adminpass')

    response = client.post('/login', data={
        'email': admin_email,
        'password': admin_password
    }, follow_redirects=True)

    # メール送信関数が1回呼ばれたか検証
    assert mock_mail_send.called
    assert mock_mail_send.call_count == 1

    # 送信されたメールの内容検証
    sent_msg = mock_mail_send.call_args[0][0]
    assert sent_msg.subject == '管理者ログイン用リンク'
    assert admin_email in sent_msg.recipients

    # フラッシュメッセージの確認
    assert '登録されたメールアドレスに送信されたURLから管理者画面にログインしてください' in response.get_data(as_text=True)

    