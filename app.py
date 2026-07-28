import os,re
from random import choice
from flask import Flask, render_template,redirect,session,flash,url_for,request,jsonify
from models.models import Word,Genre,Word_genre,User,Text,Good_word,Good_text
from models.extensions import db
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import func


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://GUEST:GUEST@192.168.10.115/word_app"
)

db.init_app(app)

app.secret_key = 'your_secret_key'


# TOP画面
@app.route('/')
def index():
    words = Word.query.all()
    random_word = choice(words)

    texts = Text.query.filter(
        Text.main_text.contains(random_word.word),
        Text.text_status == 0
    ).all()

    is_login = 'user_id' in session

    texts_items = []
    for text in texts:
        good_count_text = len(text.goods)
        is_good_text = False
        if is_login:
            is_good_text = Good_text.query.filter_by(text_id=text.id, user_id=session['user_id']).first() is not None
        texts_items.append({
            'id': text.id,
            'title': text.title,
            'main_text': text.main_text,
            'good_count': good_count_text,
            'is_good': is_good_text
        })

    is_good = False
    if is_login:
        is_good = Good_word.query.filter_by(word_id=random_word.id, user_id=session['user_id']).first() is not None

    good_count = Good_word.query.filter_by(word_id=random_word.id).count()

    # Ajax(JS)からのリクエストならJSONだけ返す
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'word': {
                'id': random_word.id,
                'word': random_word.word,
                'reading': random_word.reading,
                'mean': random_word.mean
            },
            'is_good': is_good,
            'good_count': good_count,
            'texts': texts_items
        })

    # 通常アクセスはページ全体を返す(texts辞書は既存のテンプレート側の書き方に合わせて渡す)
    texts_contents = {text: (item['good_count'], item['is_good']) for text, item in zip(texts, texts_items)}

    return render_template(
        'top.html',
        word=random_word,
        text=texts_contents,
        is_login=is_login,
        is_good=is_good,
        good_count=good_count
    )


# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('ログインに失敗しました')
            return render_template('login.html')
        
        session['user_id'] = user.id
        session['user_name'] = user.user_name
        return redirect(url_for('mypage'))

    return render_template('login.html')


# 新規登録
# 田中さん担当
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # 未入力チェック
        if not user_name or not email or not password:
            flash("全ての項目を正しく入力してください")
            return redirect(url_for('register'))
        
        # ユーザー名文字数チェック
        if len(user_name) > 255:
            flash("ユーザー名は255文字以内で入力してください")
            return redirect(url_for('register'))
        
        # メールアドレス形式チェック
        if not re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
            flash("既に登録済みのメールアドレスか不正なメールアドレスです")
            return redirect(url_for("register"))

        # メールアドレス重複チェック
        user = User.query.filter_by(email=email).first()
        if user:
            flash("既に登録済みのメールアドレスか不正なメールアドレスです")
            return redirect(url_for('register'))
        
        # パスワード文字数チェック
        if len(password) < 8 or len(password) > 16:
            flash("パスワードは8文字以上16文字以内で入力してください")
            return redirect(url_for('register'))
        
        # パスワードをハッシュ化
        password_hash = generate_password_hash(password)

        # ユーザー登録
        user = User(
             user_name=user_name,
            email=email,
            password_hash=password_hash
         )
        
        db.session.add(user)
        db.session.commit()

        flash("新規登録が完了しました")
        return redirect(url_for('login'))

    return render_template('register.html')


# マイページ
@app.route('/mypage', methods=['GET'])
def mypage():
    # ログインチェック
    if 'user_id' not in session:
        flash('ログインが必要です')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    # --- いいねした単語一覧 ---
    good_words = Good_word.query.filter_by(user_id=user_id).all()
    liked_words = []
    for gw in good_words:
        word = Word.query.get(gw.word_id)
        liked_words.append(word)

    # --- いいねした文章一覧 ---
    good_texts = Good_text.query.filter_by(user_id=user_id).all()
    liked_texts = []
    for gt in good_texts:
        text = Text.query.get(gt.text_id)
        liked_texts.append(text)

    # --- 自分が作成した文章一覧(いいね数つき) ---
    my_texts = Text.query.filter_by(user_id=user_id).all()
    my_texts_data = []
    for text in my_texts:
        good_count = len(text.goods)
        my_texts_data.append((text, good_count))

    return render_template(
        'mypage.html',
        user=user,
        liked_words=liked_words,
        liked_texts=liked_texts,
        my_texts_data=my_texts_data
    )

# ログアウト
@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.clear()
    return redirect(url_for('index'))


# 退会
@app.route('/unregister', methods=['GET', 'POST'])
def unregister():
    if request.method == 'POST':
        # ログインチェック
        if 'user_id' not in session:
            return redirect(url_for('login'))
    
        # ユーザーIDを取得
        my_id = session['user_id']

        user = db.session.get(User,my_id)
        print(user)
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("ユーザー情報が削除されました")
        return redirect(url_for('index'))

     
    user_name = session['user_name']
    return render_template('unregister.html',user_name=user_name)


# 一覧・検索
@app.route('/contents', methods=['GET'])
def contents():
    # 文章、単語のリクエスト取得
    content_type = request.args.get('type','word')
    # キーワード検索
    keyword = request.args.get('q','').strip()
    # ジャンル検索
    genre_ids = request.args.getlist('genre',type=int)
    # 並び替え
    sort = request.args.get('sort','')

    # いいね情報取得のためのユーザー情報
    is_login = 'user_id' in session
    user_id = session.get('user_id')


    # text検索
    if content_type == 'text':
        query = Text.query.filter(Text.text_status == 0)

        if keyword:
            query = query.filter(
                db.or_(
                    Text.title.contains(keyword),
                    Text.main_text.contains(keyword)
                )
            )
        if sort == 'good_desc':
            texts = query.all()
            texts.sort(key=lambda t:len(t.goods),reverse=True)
        elif sort == 'date_asc':
            texts = query.order_by(Text.id.acs()).all()
        elif sort == 'date_desc':
            texts = query.order_by(Text.id.desc()).all()
        else:
            texts = query.order_by(Text.id.desc()).all()

        items = []
        for text in texts:
            good_count = len(text.goods)
            is_good = False
            if is_login:
                is_good = Good_text.query.filter_by(text_id=text.id, user_id=user_id).first() is not None
            items.append({
                'id': text.id,
                'title': text.title,
                'main_text': text.main_text,
                'good_count': good_count,
                'is_good': is_good
            })
    # word検索
    else:
        query = Word.query

        if keyword:
            query = query.filter(
                db.or_(
                    Word.word.contains(keyword),
                    Word.mean.contains(keyword),
                    Word.reading.contains(keyword)
                )
            )

        if genre_ids:
            query = (
                query.join(Word_genre)
                .filter(Word_genre.genre_id.in_(genre_ids))
                .group_by(Word.id)
                .having(func.count(func.distinct(Word_genre.genre_id)) == len(genre_ids))  # ← AND条件化
            )
        words = query.all()

        if sort == 'aiueo_asc':
            words.sort(key=lambda w: w.reading)
        elif sort == 'aiueo_desc':
            words.sort(key=lambda w: w.reading, reverse=True)
        elif sort == 'good_desc':
            words.sort(key=lambda w: len(w.goods), reverse=True)

        items = []
        for word in words:
            good_count = len(word.goods)
            is_good = False
            if is_login:
                is_good = Good_word.query.filter_by(word_id=word.id, user_id=user_id).first() is not None
            items.append({
                'id': word.id,
                'word': word.word,
                'reading': word.reading,
                'mean': word.mean,
                'good_count': good_count,
                'is_good': is_good
            })

    # Ajax(JS)からのリクエストならJSONだけ返す
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'type': content_type, 'items': items})

    # 通常アクセスならページ全体を返す(初期表示は単語一覧、デフォルト)
    genres = Genre.query.all()
    return render_template('contents.html', items=items, content_type=content_type, genres=genres, is_login=is_login)

    return render_template('contents.html')


# 新規文章作成
@app.route('/text-new/<int:id>', methods=['GET', 'POST'])
def text_new(id):
    # ログインチェック
    user_id = session.get('user_id')
    if not user_id:
        flash("ログインが必要です", "warning")
        return redirect(url_for('login'))
    
    # 選択した単語IDの受け取り
    word_id = id
    select_word = Word.query.get(word_id)

    if request.method == 'POST':
        title = request.form.get("title", "").strip()
        main_text = request.form.get("main_text","").strip()
        text_status_val = request.form.get("text_status", "0")
        text_status = int(text_status_val) if text_status_val.isdigit() else 0

        # バリデーション仕様の適用
        render_error = lambda: render_template(
            "text-new.html",
            user_id=user_id,
            title=title,
            main_text=main_text,
            text_status=text_status,
            word=word_id,
            select_word=select_word
        )

        # バリデーション
        if not title:
            flash("タイトルを入力してください", "error")
            return render_error()
        if len(title) > 255:
            flash("タイトルは255文字以内で入力してください", "error")
            return render_error()
        if not main_text:
            flash("本文を入力してください", "error")
            return render_error()
        if len(main_text) < 10 or len(main_text) > 400:
            flash("本文は10文字以上・400文字以内で入力してください", "error")
            return render_error()
        
        if select_word and (select_word.word not in main_text):
            flash(f"本文に選択した単語（{select_word.word}）が含まれていません", "error")
            return render_error()
        
        # 重複チェック
        existing_text = Text.query.filter_by(title=title, main_text=main_text).first()
        if existing_text:
            text_status = 1
            flash("タイトルと本文が同一の文章が既に存在するため、この文章は下書き保存されます", "info")

        # データベース登録処理
        new_text = Text(
            user_id = user_id,
            title=title,
            main_text=main_text,
            text_status=text_status,
            word = word_id
            # word=int(word) if (word and word.isdigit()) else None
            )
        db.session.add(new_text)
        db.session.commit()

        flash("文章を作成しました")
        return redirect(url_for('mypage'))

    return render_template('text-new.html',word=word_id, select_word=select_word)




# 文章編集
@app.route('/text-edit/<int:id>', methods=['GET', 'POST'])
def text_edit(id):
    text = db.get_or_404(Text, id)

    # ログインチェック
    user_id = session.get('user_id')
    if not user_id:
        flash("ログインが必要です", "warning")
        return redirect(url_for('login'))

    # ユーザー判定
    if text.user_id != user_id:
        flash("他ユーザーの文章は編集できません", "error")
        return redirect(url_for('mypage'))
    
    word_id = text.word
    select_word = Word.query.get(word_id) if word_id else None
    
    if request.method == 'POST':
        title = request.form.get("title", "").strip()
        main_text = request.form.get("main_text","").strip()
        text_status_val = request.form.get("text_status", "0")
        text_status = int(text_status_val) if text_status_val.isdigit() else 0

        select_word = Word.query.get(text.word) if text.word else None

        # バリデーション仕様の適用
        render_error = lambda: render_template(
            "text-edit.html",
            text=text,
            title=title,
            main_text=main_text,
            text_status=text_status,
            word=word_id,
            select_word=select_word
        )

        # バリデーション
        if not title:
            flash("タイトルを入力してください", "error")
            return render_error()
        if len(title) > 255:
            flash("タイトルは255文字以内で入力してください", "error")
            return render_error()
        if not main_text:
            flash("本文を入力してください", "error")
            return render_error()
        if len(main_text) < 10 or len(main_text) > 400:
            flash("本文は10文字以上・400文字以内で入力してください", "error")
            return render_error()
        
        if select_word and (select_word.word not in main_text):
            flash(f"本文に選択した単語（{select_word.word}）が含まれていません", "error")
            return render_error()
        
        existing_text = Text.query.filter(
            Text.id != text.id,
            Text.title == title,
            Text.main_text == main_text).first()
        if existing_text:
            text_status = 1
            flash("タイトルと本文が同一の文章が既に存在するため、この文章は下書き保存されます", "info")

        # データベース更新処理
        text.title = title
        text.main_text = main_text
        text.text_status = text_status
        db.session.commit()

        flash("文章を編集しました")
        return redirect(url_for('mypage'))

    return render_template('text-edit.html',text=text, word=word_id, select_word=select_word)





# 文章削除
@app.route('/text-delete/<int:id>', methods=['POST'])
def text_delete(id):
    text = db.get_or_404(Text, id)

    # ログインチェック
    user_id = session.get('user_id')
    if not user_id:
        flash("ログインが必要です", "warning")
        return redirect(url_for('login'))

    # ユーザー判定
    if text.user_id != user_id:
        flash("他ユーザーの文章は削除できません", "error")
        return redirect(url_for('mypage'))
    
    # データベース削除処理
    db.session.delete(text)
    db.session.commit()
    
    flash("文章を削除しました", "success")
    return redirect(url_for('mypage'))



# 単語いいね登録・解除
@app.route('/good/word/<int:word_id>', methods=['POST'])
def good_word(word_id):
    # 未ログインフラッシュメッセージ
    if 'user_id' not in session:
        return jsonify({"error": "いいね機能を使うにはログインしてください"}), 401

    # ユーザーID取得
    user_id = session['user_id']

    # ユーザーのいいね状態取得、更新
    like = Good_word.query.filter_by(word_id=word_id, user_id=user_id).first()
    if like:
        db.session.delete(like)
        is_good = False
    else:
        new_like = Good_word(word_id=word_id,user_id=user_id)
        db.session.add(new_like)
        is_good = True
    db.session.commit()

    # いいね数取得
    good_count = Good_word.query.filter_by(word_id=word_id).count()

    return jsonify({"is_good":is_good, "good_count":good_count})
    
        


# 文章いいね登録・解除
@app.route('/good/text/<int:text_id>', methods=['POST'])
def good_text(text_id):
    # 未ログインフラッシュメッセージ
    if 'user_id' not in session:
        return jsonify({"error":"いいね機能を使うにはログインしてください"}),401

    # ユーザーID取得
    user_id = session['user_id']

    # ユーザーのいいね状態取得、更新
    like = Good_text.query.filter_by(text_id=text_id,user_id=user_id).first()
    if like:
        db.session.delete(like)
        is_good = False
    else:
        new_like = Good_text(text_id=text_id,user_id=user_id)
        db.session.add(new_like)
        is_good = True
    db.session.commit()

    # いいね数取得
    good_count = Good_text.query.filter_by(text_id=text_id).count()

    return jsonify({"is_good":is_good, "good_count":good_count})


if __name__ == "__main__":
    app.run(debug=True)