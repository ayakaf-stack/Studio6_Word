import pytest
from app import app, db
from models.models import User, Text, Word, Good_word, Good_text

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client


# ----------------------------------------------------------------
# 1. ユーザー認証・ライフサイクル & 退会 (AUTH-01 ~ AUTH-04)
# ----------------------------------------------------------------
def test_auth_and_lifecycle(client):
    # 他のテストと衝突しないユニークなメールアドレスを使用
    test_email = 'auth_lifecycle_unique2@example.com'

    # AUTH-01: 新規登録
    res = client.post('/register', data={
        'user_name': '結合ユーザー',
        'email': test_email,
        'password': 'password123'
    }, follow_redirects=True)
    assert '新規登録が完了しました' in res.get_data(as_text=True)

    # AUTH-02: 重複登録チェック（同じメールアドレスで再送）
    res_dup = client.post('/register', data={
        'user_name': '結合ユーザー2',
        'email': test_email,
        'password': 'password123'
    }, follow_redirects=True)
    assert '既に登録済みのメールアドレスか不正なメールアドレスです' in res_dup.get_data(as_text=True)

    # AUTH-01: ログイン
    res_login = client.post('/login', data={
        'email': test_email,
        'password': 'password123'
    }, follow_redirects=True)
    assert 'マイページ' in res_login.get_data(as_text=True)

    # AUTH-03: ログアウト
    res_logout = client.post('/logout', follow_redirects=True)
    assert 'ログアウトしました' in res_logout.get_data(as_text=True)


def test_unregister_process(client):
    """AUTH-04: 退会処理と関連データ削除の検証"""
    # 準備: テスト用ユーザー作成 & ログイン
    client.post('/register', data={
        'user_name': '退会テストユーザー',
        'email': 'unregister_test@example.com',
        'password': 'password123'
    })
    client.post('/login', data={
        'email': 'unregister_test@example.com',
        'password': 'password123'
    })

    # 退会処理送信 (POST)
    res_unreg = client.post('/unregister', data={
        'password': 'password123',
        'checkbox': '1'
    }, follow_redirects=True)

    assert 'ユーザー情報が削除されました' in res_unreg.get_data(as_text=True)

    # DBから該当ユーザーが消えているか検証
    user = User.query.filter_by(email='unregister_test@example.com').first()
    assert user is None


# ----------------------------------------------------------------
# 2. アクセス制御・他者データ保護 (GUARD-01, GUARD-02)
# ----------------------------------------------------------------
def test_access_guard(client):
    # GUARD-01: 未ログイン時のアクセス保護
    res = client.get('/mypage', follow_redirects=True)
    assert 'ログインが必要です' in res.get_data(as_text=True)

    res_new = client.get('/text-new/1', follow_redirects=True)
    assert 'ログインが必要です' in res_new.get_data(as_text=True)


def test_other_user_data_protection(client):
    """GUARD-02: 他ユーザーの文章編集・削除ブロックの検証"""
    # 1. ユーザーA作成 & ログイン & 文章作成
    client.post('/register', data={'user_name': 'ユーザーA', 'email': 'user_a@example.com', 'password': 'password123'})
    client.post('/login', data={'email': 'user_a@example.com', 'password': 'password123'})
    
    word = Word.query.first()
    word_id = word.id if word else 1
    word_str = word.word if word else 'テスト'

    client.post(f'/text-new/{word_id}', data={
        'title': 'ユーザーAの文章',
        'main_text': f'ユーザーAが作成した本文です。【{word_str}】を含みます。',
        'text_status': '0'
    })

    # 作成された文章のIDを取得
    text_a = Text.query.filter_by(title='ユーザーAの文章').first()
    assert text_a is not None

    # ログアウト
    client.post('/logout')

    # 2. ユーザーB作成 & ログイン
    client.post('/register', data={'user_name': 'ユーザーB', 'email': 'user_b@example.com', 'password': 'password123'})
    client.post('/login', data={'email': 'user_b@example.com', 'password': 'password123'})

    # 3. ユーザーBがユーザーAの文章を編集しようとする
    res_edit = client.get(f'/text-edit/{text_a.id}', follow_redirects=True)
    assert '他ユーザーの文章は編集できません' in res_edit.get_data(as_text=True)

    # 4. ユーザーBがユーザーAの文章を削除しようとする
    res_delete = client.post(f'/text-delete/{text_a.id}', follow_redirects=True)
    assert '他ユーザーの文章は削除できません' in res_delete.get_data(as_text=True)


# ----------------------------------------------------------------
# 3. 文章作成・編集・削除・重複下書き化 (TEXT-01 ~ TEXT-04)
# ----------------------------------------------------------------
def test_text_crud_workflow(client):
    # 準備: テスト用ユーザー作成 & ログイン
    client.post('/register', data={'user_name': '文章テストユーザー', 'email': 'text_user@example.com', 'password': 'password123'})
    client.post('/login', data={'email': 'text_user@example.com', 'password': 'password123'})

    word = Word.query.first()
    word_id = word.id if word else 1
    word_str = word.word if word else 'テスト'

    # TEXT-02: 異常系（指定単語が本文に含まれない）
    res_fail = client.post(f'/text-new/{word_id}', data={
        'title': '間違ったタイトル',
        'main_text': '指定された単語が全く含まれていない本文テキストです。',
        'text_status': '0'
    }, follow_redirects=True)
    assert f'本文に選択した単語（{word_str}）が含まれていません' in res_fail.get_data(as_text=True)

    # TEXT-01: 正常系（文章作成）
    res_success = client.post(f'/text-new/{word_id}', data={
        'title': '正常なタイトル',
        'main_text': f'ここには指定されたキーワード【{word_str}】がしっかり含まれています。',
        'text_status': '0'
    }, follow_redirects=True)
    assert '文章を作成しました' in res_success.get_data(as_text=True)

    created_text = Text.query.filter_by(title='正常なタイトル').first()
    assert created_text is not None

    # TEXT-03: 同内容文章の重複作成（下書き化）
    res_dup = client.post(f'/text-new/{word_id}', data={
        'title': '正常なタイトル',
        'main_text': f'ここには指定されたキーワード【{word_str}】がしっかり含まれています。',
        'text_status': '0'
    }, follow_redirects=True)
    assert 'タイトルと本文が同一の文章が既に存在するため、この文章は下書き保存されます' in res_dup.get_data(as_text=True)

    # TEXT-04: 文章編集と削除
    res_edit = client.post(f'/text-edit/{created_text.id}', data={
        'title': '編集後のタイトル',
        'main_text': f'編集後の本文テキストです。【{word_str}】も含みます。',
        'text_status': '0'
    }, follow_redirects=True)
    assert '文章を編集しました' in res_edit.get_data(as_text=True)

    res_delete = client.post(f'/text-delete/{created_text.id}', follow_redirects=True)
    assert '文章を削除しました' in res_delete.get_data(as_text=True)

    # DBから消えていることの確認
    deleted_text = db.session.get(Text, created_text.id)
    assert deleted_text is None


# ----------------------------------------------------------------
# 4. 非同期 いいね機能 (LIKE-01, LIKE-02)
# ----------------------------------------------------------------
def test_like_functionality(client):
    word = Word.query.first()
    word_id = word.id if word else 1

    # LIKE-02: 未ログイン時のいいね（401）
    res_unauth = client.post(f'/good/word/{word_id}')
    assert res_unauth.status_code == 401

    # ログイン
    client.post('/register', data={'user_name': 'いいねユーザー', 'email': 'like_user@example.com', 'password': 'password123'})
    client.post('/login', data={'email': 'like_user@example.com', 'password': 'password123'})

    # LIKE-01: 登録 (1回目)
    res_like = client.post(f'/good/word/{word_id}')
    assert res_like.status_code == 200
    assert res_like.get_json()['is_good'] is True

    # LIKE-01: 解除 (2回目)
    res_unlike = client.post(f'/good/word/{word_id}')
    assert res_unlike.status_code == 200
    assert res_unlike.get_json()['is_good'] is False