import os
from flask import Flask, request, render_template, jsonify, redirect, flash, url_for, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.security import check_password_hash, generate_password_hash

#from static import login_required

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
      if check_password_hash(listT[0]['password'], request.form.get("password")):
          session['user_id'] = listT[0]['id']
          return redirect('/')

    except IndexError:
      flash('Wrong username', category='danger')
      return redirect('/login')

    flash('Wrong password', category='danger')
    return redirect('/login')

  else:
    return render_template('register.html')


@app.route('/hi')
@login_required
def hi():
  pass

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
        print(unique_profile_pic_src)
        return redirect(url_for("homepage"))
    else:
        return "User email not available or not verified by Google.", 400

#@app.route('/register', methods = ['POST', "GET"])
#def registration_page():
   # form = RegistrationForm()
    #if form.validate_on_submit():
      #  username = form.username.data
       # password = form.password.data

        #user_object = Users.query.filter_by(username=username).first()
        #if user_object:
           # return "Someone has this username!"

        #user = Users(username=username, password=password)
        #db.session.add(user)
        #db.session.commit()

    #return render_template('registration.html', form=form)

   # return render_template('registration.html', form=form)

if __name__ == '__main__':
    app.run(debug='True')
