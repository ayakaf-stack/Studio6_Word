from flask import Flask, render_template,redirect,session,flash,url_for,request
from models.models import Word,Genre,Word_genre,User,Text,Good_word,Good_text
from models.extensions import db
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://flaskUser:flaskPass@localhost/word_app"
)

db.init_app(app)


# TOP画面
@app.route('/')
def index():

    return render_template('top.html')


# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        return redirect(url_for('index'))

    return render_template('login.html')


# 新規登録
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
        
        # パスワード文字数チェック
        if len(password) < 8 or len(password) > 16:
            flash("パスワードは8文字以上16文字以内で入力してください")
            return redirect(url_for('register'))

        # ユーザー名文字数チェック
        if len(user_name) > 255:
            flash("ユーザー名は255文字以内で入力してください")
            return redirect(url_for('register'))

        flash("新規登録が完了しました")
        return redirect(url_for('login'))

    return render_template('register.html')


# マイページ
@app.route('/mypage/<int:id>', methods=['GET'])
def mypage(id):
    
    return render_template('mypage.html')


# ログアウト
@app.route('/logout')
def logout():

    return redirect(url_for('index'))


# 退会
@app.route('/unregister', methods=['GET', 'POST'])
def unregister():
    if request.method == 'POST':
        
        return redirect(url_for('index'))

    return render_template('unregister.html')


# 一覧・検索
@app.route('/contents', methods=['GET'])
def contents():

    return render_template('contents.html')


# 新規文章作成
@app.route('/text-new', methods=['GET', 'POST'])
def text_new():
    if request.method == 'POST':
        
        return redirect(url_for('mypage'))

    return render_template('text-new.html')



# 文章編集
@app.route('/text-edit/<int:id>', methods=['GET', 'POST'])
def text_edit(id):
    if request.method == 'POST':

        return redirect(url_for('mypage'))

    return render_template('text-edit.html')



# 文章削除
@app.route('/text-delete/<int:id>', methods=['POST'])
def text_delete(id):
   
    return redirect(url_for('mypage'))


# 単語いいね登録・解除
@app.route('/like/word/<int:word_id>', methods=['POST'])
def like_word(word_id):

    return redirect(request.referrer or url_for('index'))


# 文章いいね登録・解除
@app.route('/like/text/<int:text_id>', methods=['POST'])
def like_text(text_id):

    return redirect(request.referrer or url_for('index'))