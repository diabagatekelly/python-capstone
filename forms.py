from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, Length, Optional

class UserAddForm(FlaskForm):
    """Form for adding users."""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=True)
    option_widget = widgets.CheckboxInput()

class PasswordHidden(PasswordField):
    widget = widgets.PasswordInput(hide_value=True)

class UserEditForm(FlaskForm):
    """Form for editing users"""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordHidden('Password', validators=[Length(min=6), Optional()])
    

    fave_cuisines = MultiCheckboxField("Fave Cuisines (Optional)", coerce=int, validators=[Optional()])
    diets = MultiCheckboxField("Special Diets (Optional)", coerce=int, validators=[Optional()])
    intolerances = MultiCheckboxField("Foods to avoid (Optional)", coerce=int, validators=[Optional()])
    displayCustoms = MultiCheckboxField("Custom (Optional)", coerce=int, validators=[Optional()])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

