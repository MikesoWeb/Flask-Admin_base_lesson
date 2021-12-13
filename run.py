from datetime import datetime

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from mimesis import Person, Text

app = Flask(__name__)
app.config['FLASK_ENV'] = 'development'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = 'anykey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

person = Person('ru')
text = Text('ru')


@app.get('/')
def index():
    return render_template('index.html')


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    last_seen = db.Column(db.DateTime)
    user_status = db.Column(db.String(40), nullable=True, default='Лучший пользователь проекта')
    tags = db.relationship('Tag', backref='user_tag', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='author', lazy=True)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=False, nullable=False)
    content = db.Column(db.Text(60), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    comments = db.relationship('Comment', backref='article', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', backref='post_tag', lazy=True, cascade="all, delete-orphan")
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    body = db.Column(db.Text(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    name = db.Column(db.Text(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)


class AnyPageView(BaseView):
    @expose('/')
    def any_page(self):
        return self.render('admin/any_page/index.html')


class DashBoardView(AdminIndexView):
    @expose('/')
    def add_data_db(self):
        for i in range(10):
            if not len(User.query.all()) >= 10:
                user = User(username=person.full_name(), email=person.email(), password=person.password())
                db.session.add(user)
                db.session.commit()

                post = Post(title=text.title(), content=text.text(quantity=5))
                post.user_id = user.id
                db.session.add(post)

                comment = Comment(username=user.username, body='Клевая статья. Всем добра', post_id=post.id)
                db.session.add(comment)
            db.session.commit()
        all_users = User.query.all()
        all_posts = Post.query.all()
        all_comments = Comment.query.all()
        return self.render('admin/dashboard_index.html', all_users=all_users, all_posts=all_posts,
                           all_comments=all_comments)


admin = Admin(app, name='Мой блог', template_mode='bootstrap3', index_view=DashBoardView(), endpoint='admin')
admin.add_view(ModelView(User, db.session, name='Пользователь'))
admin.add_view(ModelView(Post, db.session, name='Статьи'))
admin.add_view(ModelView(Comment, db.session, name='Комментарии'))
admin.add_view(ModelView(Tag, db.session, name='Теги'))
admin.add_view(AnyPageView(name='Что-то еще'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
