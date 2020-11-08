from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectMultipleField, FileField, widgets
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

class CreateRecipeForm(FlaskForm):
    """Form for creating new recipe"""
    
    title = StringField('Title (required)', render_kw={"placeholder":"Baked Chicken"}, validators=[DataRequired()])
    directions = TextAreaField('Directions (required)', render_kw={"placeholder":
    """Write/paste directions:
    Turn on oven to 375F.Then, rinse the chicken"""}, validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients (required)', render_kw={"placeholder":
    """Add/paste one ingredient per line, separated by commas
    Example: 
    1lb chicken,
    Pan oil
    """}, validators=[DataRequired()])
    servings = StringField('Servings (required)', render_kw={"placeholder":"8"}, validators=[DataRequired()])
    cooking_time = StringField('Cooking Time (optional)', render_kw={"placeholder":"30 min"}, validators=[Optional()])
    summary = TextAreaField('Summary (optional)', render_kw={"placeholder":"Delicious, quick and healthy chicken recipe the whole family is sure to enjoy."}, validators=[Optional()])
    weight_watchers_pts = StringField('Weight Watchers Points (optional)', render_kw={"placeholder":"12"}, validators=[Optional()])
    image = FileField('Image (optional)', render_kw={"placeholder":"Upload image"})


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

