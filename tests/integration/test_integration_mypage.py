import uuid
import pytest
from werkzeug.security import generate_password_hash
from app import db
from models.models import User, Word, Text, Good_word, Good_text


def test_mypage_access_denied_when_not_logged_in(client):
    """【シナリオ1】未ログイン状態でマイページにアクセスした際、ログイン画面へリダイレクトされるか"""
    response = client.get('/mypage')
    
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_mypage_display_empty_state(app, client):
    """【シナリオ2】投稿やいいねなどのデータが0件のユーザーでログインした際、
    空状態メッセージが表示されエラーにならないかを検証
    """
    unique_suffix = str(uuid.uuid4())[:8]
    user_empty = User(
        user_name=f'empty_user_{unique_suffix}',
        email=f'empty_{unique_suffix}@example.com',
        password_hash=generate_password_hash('pass123')
    )

    # --- アプリケーションコンテキスト内で DB 操作 ---
    with app.app_context():
        db.session.add(user_empty)
        db.session.commit()
        user_id = user_empty.id
        user_name = user_empty.user_name

    try:
        # --- ログイン状態でマイページへアクセス ---
        with client.session_transaction() as session:
            session['user_id'] = user_id

        response = client.get('/mypage')
        assert response.status_code == 200

        html = response.get_data(as_text=True)

        # --- 画面（HTML）の検証 ---
        assert user_name in html
        assert 'まだ作成した文章はありません' in html
        assert 'まだいいねした単語はありません' in html
        assert 'まだいいねした文章はありません' in html

    finally:
        # --- クリーンアップ ---
        with app.app_context():
            User.query.filter_by(id=user_id).delete()
            db.session.commit()


def test_mypage_data_integration_for_logged_in_user(app, client):
    """【シナリオ3】マイページで自分のデータ（投稿・いいね）のみが正しく表示され、
    他ユーザーのデータが混ざらないことを検証する結合テスト
    """
    suffix_b = str(uuid.uuid4())[:8]
    suffix_c = str(uuid.uuid4())[:8]

    # --- アプリケーションコンテキスト内で DB 操作 ---
    with app.app_context():
        user_b = User(
            user_name=f'user_b_{suffix_b}',
            email=f'b_{suffix_b}@example.com',
            password_hash=generate_password_hash('pass123')
        )
        user_c = User(
            user_name=f'user_c_{suffix_c}',
            email=f'c_{suffix_c}@example.com',
            password_hash=generate_password_hash('pass123')
        )
        db.session.add_all([user_b, user_c])
        db.session.commit()

        word_1 = Word(word=f'単語B_{suffix_b}', reading='タンゴビー', mean='ユーザーB用')
        word_2 = Word(word=f'単語C_{suffix_c}', reading='タンゴシー', mean='ユーザーC用')
        db.session.add_all([word_1, word_2])
        db.session.commit()

        # ユーザーBの投稿文章
        text_b = Text(
            user_id=user_b.id,
            title=f'ユーザーBの投稿タイトル_{suffix_b}',
            main_text='ユーザーBの文章本文です。',
            text_status=0,
            word=word_1.id
        )
        # ユーザーCの投稿文章（ユーザーBはいいねもしない）
        text_c = Text(
            user_id=user_c.id,
            title=f'ユーザーCの秘密投稿_{suffix_c}',
            main_text='ユーザーCの文章本文です。',
            text_status=0,
            word=word_2.id
        )
        # ユーザーCの投稿文章（ユーザーBが「いいね」する文章）
        text_c_liked = Text(
            user_id=user_c.id,
            title=f'ユーザーBがいいねしたCの文章_{suffix_c}',
            main_text='いいね対象の文章本文です。',
            text_status=0,
            word=word_2.id
        )
        db.session.add_all([text_b, text_c, text_c_liked])
        db.session.commit()

        # いいねデータ（ユーザーBが単語1・文章(text_c_liked)に「いいね」）
        good_w_b = Good_word(user_id=user_b.id, word_id=word_1.id)
        good_t_b = Good_text(user_id=user_b.id, text_id=text_c_liked.id)
        db.session.add_all([good_w_b, good_t_b])
        db.session.commit()

        # 変数保持
        user_b_id = user_b.id
        user_c_id = user_c.id
        user_b_name = user_b.user_name
        text_b_title = text_b.title
        text_c_title = text_c.title
        text_c_liked_title = text_c_liked.title
        word_1_word = word_1.word
        text_b_id = text_b.id
        text_c_id = text_c.id
        text_c_liked_id = text_c_liked.id
        word_1_id = word_1.id
        word_2_id = word_2.id

    try:
        # --- ユーザーBでログインしてマイページにアクセス ---
        with client.session_transaction() as session:
            session['user_id'] = user_b_id

        response = client.get('/mypage')
        assert response.status_code == 200

        html = response.get_data(as_text=True)

        # --- 画面（HTML）のデータ連携検証 ---
        assert user_b_name in html
        assert text_b_title in html         # 自分が作った投稿が表示されているか
        assert text_c_liked_title in html   # 自分がいいねした投稿が表示されているか
        assert text_c_title not in html     # 自分に関係ない他人の投稿が表示されていないか
        assert word_1_word in html          # 自分がいいねした単語が表示されているか

    finally:
        # --- クリーンアップ ---
        with app.app_context():
            Good_text.query.filter_by(user_id=user_b_id).delete()
            Good_word.query.filter_by(user_id=user_b_id).delete()
            Text.query.filter_by(id=text_b_id).delete()
            Text.query.filter_by(id=text_c_id).delete()
            Text.query.filter_by(id=text_c_liked_id).delete()
            Word.query.filter_by(id=word_1_id).delete()
            Word.query.filter_by(id=word_2_id).delete()
            User.query.filter_by(id=user_b_id).delete()
            User.query.filter_by(id=user_c_id).delete()
            db.session.commit()