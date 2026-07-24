import os,re
from random import choice
from flask import Flask, render_template,redirect,session,flash,url_for,request
from models.models import Word,Genre,Word_genre,User,Text,Good_word,Good_text
from models.extensions import db
from werkzeug.security import generate_password_hash,check_password_hash


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://GUEST:GUEST@192.168.10.115/word_app"
)

db.init_app(app)

app.secret_key = 'your_secret_key'


# TOP画面
@app.route('/')
def index():
    # wordsの全件取得
    words = Word.query.all()

    # wordsから単語をランダムに抽出
    random_word = choice(words)

    # ワードのいいね数をカウント
    like_words = len(Good_word.query.filter_by(word_id=random_word.id).all())

    # ワードに紐づいたtextsを抽出
    texts = Text.query.filter(
        Text.main_text.contains(random_word.word),
        Text.text_status == 0
    ).all()

    # textsのいいね数をカウント
    like_texts = []
    for text in texts:
        like_texts.append(len(text.goods))
    
    # 各textsといいね数をzipで紐付け
    texts_contents = dict(zip(texts,like_texts))

    # ログイン判定
    is_login = 'user_id' in session
    return render_template(
        'top.html',
        word = random_word,
        like_word = like_words,
        text = texts_contents,
        is_login = is_login
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
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # ユーザーネームを取得
    user_name = session['user_name']
    my_id = session['user_id']

    # ユーザーがいいねしたワードを表示
    good_words = Good_word.query.filter_by(user_id=my_id).all()
    word_ids = [good.word_id for good in good_words]
    words = Word.query.filter(Word.id.in_(word_ids)).all()

    # ユーザーがいいねした文章を表示
    good_texts = Good_text.query.filter_by(user_id=my_id).all()
    text_ids = [good.text_id for good in good_texts]
    texts = Text.query.filter(Text.id.in_(text_ids)).all()
    
    
    # ユーザーが作成した文章を表示
    user_texts = Text.query.filter_by(user_id=my_id)

    # textsのいいね数をカウント
    like_texts = []
    for text in user_texts:
        like_texts.append(len(text.goods))
    
    # 各textsといいね数をzipで紐付け
    texts_contents = dict(zip(user_texts,like_texts))

    return render_template(
        'mypage.html',
        user_name = user_name,
        words = words,
        texts = texts,
        user_texts = texts_contents
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
@app.route('/like/word/<int:word_id>', methods=['POST'])
def like_word(word_id):
    if 'user_id' not in session:
        flash('いいね機能を使うにはログインしてください')
    return redirect(request.referrer or url_for('index'))


# 文章いいね登録・解除
@app.route('/like/text/<int:text_id>', methods=['POST'])
def like_text(text_id):

    return redirect(request.referrer or url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)