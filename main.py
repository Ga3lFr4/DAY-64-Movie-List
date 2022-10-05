from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
from dotenv import load_dotenv
import requests

load_dotenv('variables.env')

api_key = os.getenv('TMDB_API')
TMDB_IMG_URL='https://image.tmdb.org/t/p/w500/'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String(250), unique=True, nullable=True)
    img_url = db.Column(db.String(250), unique=True, nullable=False)

db.create_all()

class EditForm(FlaskForm):
    new_rating = StringField('Your rating out of 10 e.g 7.5', validators=[DataRequired()])
    new_review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Done')

class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

db.create_all()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)



@app.route("/edit/<movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    form = EditForm()
    if form.validate_on_submit():
        movie_to_update = Movie.query.filter_by(id=movie_id).first()
        movie_to_update.rating = request.form["new_rating"]
        movie_to_update.review = request.form["new_review"]
        db.session.commit()
        return redirect("/")
    return render_template("edit.html", form=form)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect("/")

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        query = form.title.data
        response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&query={query}&page=1&include_adult=false")
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find/<movie_id>", methods=['GET', 'POST'])
def find_movie(movie_id):
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}")
    data = response.json()
    new_movie = Movie(
        title=data["title"],
        year=data["release_date"].split('-')[0],
        description=data["overview"],
        img_url=f"{TMDB_IMG_URL}{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    new_id = new_movie.id
    return redirect(url_for('edit', movie_id=new_id))


if __name__ == '__main__':
    app.run(debug=True, port=8000)