from flask import Flask, redirect
from flask import render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")
    return "Hello World"

if __name__ == '__main__':
    app.run(debug=True, ssl_context = "adhoc")
