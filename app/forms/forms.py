from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, FloatField, SelectField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

# --- Authentication Forms ---

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    username = StringField('Choose Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Choose Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Account')

class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Update Password')

# --- Profile Form ---

class ProfileForm(FlaskForm):
    avatar = SelectField('Avatar', choices=[
        ('B1.png', 'B1'),
        ('B2.png', 'B2'),
        ('B3.png', 'B3'),
        ('G1.png', 'G1'),
        ('G2.png', 'G2'),
        ('G3.png', 'G3')
    ], validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[Length(max=200)])
    submit = SubmitField('Update Profile')

# --- Admin Forms ---

class CreatureForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    rarity = SelectField('Rarity', choices=[
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()]) 
    image = StringField('Image Filename (e.g. shark.png)', validators=[Optional()]) 
    probability = FloatField('Probability (0.0001 - 1.0)', validators=[DataRequired(), NumberRange(min=0.0001, max=1.0)])
    active = BooleanField('Active', default=True) 
    submit = SubmitField('Save Creature')

class MissionForm(FlaskForm):
    name = StringField('Mission Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    target = IntegerField('Target (Clicks)', validators=[DataRequired(), NumberRange(min=1)])
    reward = IntegerField('Reward (Coins)', validators=[DataRequired(), NumberRange(min=0)])
    order = IntegerField('Display Order (Lower is first)', default=0, validators=[DataRequired(), NumberRange(min=0)]) 
    active = BooleanField('Active', default=True)  
    submit = SubmitField('Save Mission')