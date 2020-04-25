
import os
import datetime
import time

from flask import Flask, request, render_template, jsonify, redirect, flash, url_for, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.security import check_password_hash, generate_password_hash

from static import login_required

#google oauth setup
GOOGLE_CLIENT_ID = "968054636635-q424q4ptpbq7t05at4vokjkttg4cspnk.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "9j-RZFHI-uqFlIN2u-SayLdA"
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

client = WebApplicationClient(GOOGLE_CLIENT_ID)
# Support for gomix's 'front-end' and 'back-end' UI.
app = Flask(__name__, static_folder='public')


# Set the app secret key from the secret environment variables.
app.secret = 'SECRETKEYHAHAHA'

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://ggvunutgatnfdw:57fcfacf74ee39a92d826636014371a1c82eb5f4e32b4b582aed6790596159aa@ec2-34-202-7-83.compute-1.amazonaws.com:5432/d35m86v26qepdg")
db = scoped_session(sessionmaker(bind=engine))
s = db()


@app.route('/')
def homepage():
    """Displays the homepage."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':

    username = str(request.form.get('username'))
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    result = s.execute("SELECT * FROM users WHERE email = :email LIMIT 1", {'email': str(email)})
    listT = []
    for row in result:
        row_as_dict = dict(row)
        listT.append(row_as_dict)

    if len(listT) != 0:
      flash("Already registered")
      return redirect('/register')

    if password != confirm:
      flash('Please double check your password', 'danger')

    s.execute('INSERT INTO users (username, password, email) VALUES (:username, :password, :email)',  {'username': username, 'password': generate_password_hash(password), 'email': str(email)})
    s.commit()

    return render_template('success.html', message='Registered Successfully')

  else:
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

  if request.method == 'POST':
    username = request.form.get('username')

    result = s.execute("SELECT * FROM users WHERE username = :username LIMIT 1", {'username': str(username)})
    listT = []
    for row in result:
        row_as_dict = dict(row)
        listT.append(row_as_dict)

    try:
      if listT[0]["password"] == 'Google':
        return redirect('/google')

      if check_password_hash(listT[0]['password'], request.form.get("password")):
          session['user_id'] = listT[0]['id']
          return render_template('activities.html', username=username)

    except IndexError:
      flash('Wrong username', category='danger')
      return redirect('/login')

    flash('Wrong password', category='danger')
    return redirect('/login')

  else:
    return render_template('register.html')



@app.route("/logout")
def logout():
    # forget any user id in session
    session.clear()

    # redirect to homepage
    return redirect("/")


@app.route("/google")
def login_google():
    def get_google_provider_cfg():
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]


    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile",],
    )
    return redirect(request_uri)

@app.route("/google/callback")
def callback():


    code = request.args.get("code")


    def get_google_provider_cfg():
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET), )

    client.parse_request_body_response(json.dumps(token_response.json()))


    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        global unique_profile_pic_src

        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        unique_profile_pic_src =  User.get_user_profilepic(users_email)
        users_last_name = userinfo_response.json()["family_name"]
        # print(unique_profile_pic_src)
        result = s.execute("SELECT * FROM users WHERE email = :email LIMIT 1", {'email': str(users_email)})

        listT = []
        for row in result:
            row_as_dict = dict(row)
            listT.append(row_as_dict)

        if len(listT) != 0:
          flash("Already registered")
          return redirect('/register')

        s.execute("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)", {"username": users_name, "password": "Google", "email": users_email})
        s.commit()
        return redirect(url_for("register"))

    else:
        return "User email not available or not verified by Google.", 400


@app.route('/activities', methods=['GET', 'POST'])
@login_required
def activites():

  # Featured snippet from the web In an ordinary trip with minimal traffic, you're likely to emit around 0.7 pounds of carbon dioxide per mile traveled. If your average speed drops to 15 miles per hour, that emissions amount rises to 1.2 pounds. ... Congestion was heavy, with more than half the cars traveling less than 25 miles per hour
  # The U.S. Environmental Protection Agency just released rules limiting particulate emissions of wood stoves sold after January 1, 2016 to 4.5 grams per hour, or three to ten times less than the 15 to 40 grams per hour that an older stove emits.
  # 66 grams of Co2 emitted per kilowatt hour for ... an oven and a gas stove
  # 40lbs co2 per lbs landfills

  if request.method == 'POST':
    ts = time.time()
    car_pollution = float(request.form.get("car-hours")) * float(request.form.get("car-mile")) * 0.7 * 454 # grams
    wood_pollution = float(request.form.get('wood-hours')) * 4.5 # grams
    gas_pollution = float(request.form.get("gas-hours")) * 66 # grams
    trash_pollution = float(request.form.get("trash-pounds")) * 40 * 454 # grams

    total = car_pollution + wood_pollution + gas_pollution + trash_pollution
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    info = {'timestamp': str(timestamp), 'description': 'Car Pollution: {}g <br>Wood Pollution: {}g <br>Gas Pollution: {}g <br>Trash pollution: {}g'.format(car_pollution, wood_pollution, gas_pollution, trash_pollution), 'user_id': session.get('user_id'), 'total_carbon': total}
    s.execute('INSERT INTO logs (timestamp, description, user_id, total_carbon) VALUES (:timestamp, :description, :user_id, :total_carbon)', info)
    s.commit()

    return render_template("activity-complete.html", description=info["description"], total=total)

  else:

    return render_template('activities.html')

@app.route('/logs')
@login_required
def logs():

  results = s.execute("SELECT * FROM logs WHERE user_id = :user_id", {"user_id": session.get('user_id')})
  return render_template('logs.html', results=results)

if __name__ == '__main__':
    app.run(debug='True')
