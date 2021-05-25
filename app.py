import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint
import psycopg2
from sqlalchemy import create_engine
import brawl_data as bd
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import UserForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'acb5113cba3117836ca7368eab681ba168f81d86dab68'

df = pd.DataFrame()

@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
def home():
    form = UserForm()
    if request.method == 'POST':
        if form.get_recommendation.data:
            try:
                df = bd.get_recommendation('postgresql://doadmin:el2of9p8wpgfe99t@brawl-stars-database-do-user-9112116-0.b.db.ondigitalocean.com:25060/db?sslmode=require',  form.player_id.data, form.game_mode.data, form.map.data, form.trophies.data)
                return render_template('home.html', title='Brawl Stars Recommendation', form=form, data = df.to_html(classes='data', header="true", index=False))
            except:
                return render_template('home.html', title='Brawl Stars Recommendation', form=form)
        elif form.get_all_recommendations.data:
            try:
                df = bd.get_all_recommendations('postgresql://doadmin:el2of9p8wpgfe99t@brawl-stars-database-do-user-9112116-0.b.db.ondigitalocean.com:25060/db?sslmode=require',  form.player_id.data, form.trophies.data)
                return render_template('home.html', title='Brawl Stars Recommendation', form=form, data = df.to_html(classes='data', header="true", index=False))
            except:
                return render_template('home.html', title='Brawl Stars Recommendation', form=form)
        elif form.get_map_weaknesses.data:
            try:
                df = bd.get_map_weaknesses('postgresql://doadmin:el2of9p8wpgfe99t@brawl-stars-database-do-user-9112116-0.b.db.ondigitalocean.com:25060/db?sslmode=require', form.trophies.data)
                return render_template('home.html', title='Brawl Stars Recommendation', form=form, data = df.to_html(classes='data', header="true", index=False))
            except:
                return render_template('home.html', title='Brawl Stars Recommendation', form=form)
        elif form.clear.data:
            form.player_id.data = ''
            form.game_mode.data = ''
            form.map.data = ''
            form.trophies.data = ''
            return render_template('home.html', title='Brawl Stars Recommendation', form=form)
    return render_template('home.html', title='Brawl Stars Recommendation', form=form)

@app.route('/about', methods = ['GET', 'POST'])
def about():
    return render_template('about.html', title='About Page')
    

if __name__ == '__main__':
    app.run(debug=True)
