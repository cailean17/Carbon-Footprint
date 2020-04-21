
import json
import os
from flask import Flask, request, render_template, jsonify, redirect, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask_bcrypt import Bcrypt

#google oauth setup
GOOGLE_CLIENT_ID = "968054636635-q424q4ptpbq7t05at4vokjkttg4cspnk.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "9j-RZFHI-uqFlIN2u-SayLdA"
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

client = WebApplicationClient(GOOGLE_CLIENT_ID)
# Support for gomix's 'front-end' and 'back-end' UI.
app = Flask(__name__, static_folder='public')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Set the app secret key from the secret environment variables.
app.secret = "asdasd123412423asd"#os.environ.get('SECRET')

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
Bcrypt(app)

# Set up database
engine = create_engine("postgres://ggvunutgatnfdw:57fcfacf74ee39a92d826636014371a1c82eb5f4e32b4b582aed6790596159aa@ec2-34-202-7-83.compute-1.amazonaws.com:5432/d35m86v26qepdg")
db = scoped_session(sessionmaker(bind=engine))
s = db()

@app.after_request
def apply_kr_hello(response):
    """Adds some headers to all responses."""

    # Made by Kenneth Reitz.
    if 'MADE_BY' in os.environ:
        response.headers["X-Was-Here"] = os.environ.get('MADE_BY')

    # Powered by Flask.
    response.headers["X-Powered-By"] = os.environ.get('POWERED_BY')
    return response


@app.route('/')
def homepage():
    """Displays the homepage."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    if password != confirmed:
      flash('Please double check your password', 'danger')


  else:
    return render_template('register.html')

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
        #global unique_profile_pic_src

        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        #unique_profile_pic_src =  User.get_user_profilepic(users_email)
        users_last_name = userinfo_response.json()["family_name"]
    #    print(unique_profile_pic_src)
        return redirect(url_for("homepage"))
    else:
        return "User email not available or not verified by Google.", 400


if __name__ == '__main__':
    app.run(debug='True')
