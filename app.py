import os
import requests
import sys
from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.urandom(24),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///weather.db'
})
db = SQLAlchemy(app)

URL = 'https://api.openweathermap.org/data/2.5/weather'
API_KEY = os.getenv('API_KEY')


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f'City: {self.name}'


with app.app_context():
    db.create_all()


def get_weather(city):
    params = {'q': city,
              'appid': API_KEY,
              'lang': 'ru',
              'units': 'metric'}
    response = requests.get(URL, params=params).json()
    sunrise = response['sys']['sunrise']
    sunset = response['sys']['sunset']
    dt = response['dt']
    if (dt > sunrise + 3600) and (dt < sunset - 3600):
        time_of_day = 'day'
    elif (dt > sunset + 3600) or (dt < sunrise - 3600):
        time_of_day = 'night'
    else:
        time_of_day = 'evening-morning'
    weather = {'name': response['name'],
               'temp': round(response['main']['temp']),
               'wind': response['wind']['speed'],
               'weather': response['weather'][0]['description'],
               'time_of_day': time_of_day}
    return weather


@app.route('/', methods=['GET', 'POST'])
def add_city():
    if request.method == 'GET':
        city_list = City.query.all()
        weather = {}
        for city in city_list:
            weather[city.name] = get_weather(city.name)
            weather[city.name]['id'] = city.id
        return render_template('index.html', weather=weather)
    if request.method == 'POST':
        city = request.form['city_name']
        params = {'q': city, 'appid': API_KEY}
        response = requests.get(URL, params=params)
        if response.status_code in (400, 404):
            flash('The city doesn\'t exist!')
        elif City.query.filter_by(name=city).first():
            flash('The city has already been added to the list!')
        else:
            db.session.add(City(name=city))
            db.session.commit()
        return redirect('/')


@app.route('/delete/<int:city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    if city:
        db.session.delete(city)
        db.session.commit()
    return redirect('/')


# don't change the following way to run flask:
if __name__ == '__main__':
    app.run()
    # if len(sys.argv) > 1:
    #     arg_host, arg_port = sys.argv[1].split(':')
    #     app.run(host=arg_host, port=arg_port)
    # else:
    #     app.run()
