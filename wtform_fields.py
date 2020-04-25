from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo

class RegistrationForm(FlaskForm):

    username = StringField('username', validators = [InputRequired(message="username required"), Length (min =4, max=25)])
    password = PasswordField('password', validators = [InputRequired(message="password required"), Length (min =4, max=25)])
    email = StringField('email',validators = [InputRequired(message="email required"), Length (min =4, max=25)])
    submit_button = SubmitField('Submit')
