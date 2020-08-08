from datetime import timedelta
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Recipe, Cuisine, Diet, Intolerance, FaveRecipes, FaveCuisines, FaveDiets, FoodIntolerances, RecipeRating, Recipe_Cuisine, Recipe_Diet, Recipe_Intolerance
from forms import UserAddForm, UserAddForm, LoginForm
import requests
import keys

CURR_USER_KEY = "curr_user"

NO_RECIPES = "NO_RECIPES"

RECIPES = []

OFFSET = 0

SPOONACULAR_RECIPES_URL = "https://api.spoonacular.com/recipes"
APIKEY = keys.spoonacular_api_key

# CUISINES = [African, American, British, Cajun, Caribbean, Chinese, Eastern European, European, French, German, Greek, Indian, Irish, Italian, Japanese, Jewish, Korean, Latin American, Mediterranean, Mexican, Middle Eastern, Nordic, Southern, Spanish, Thai, Vietnamese]

# DIETS = [Gluten Free, Ketogenic, Vegetarian, Lacto-Vegetarian, Ovo-Vegetarian, Vegan, Pescetarian, Paleo, Primal, Whole30]

# INTOLERANCES = [Dairy, Egg, Gluten, Grain, Peanut, Seafood, Sesame, Shellfish, Soy, Sulfite, Tree Nut, Wheat]

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///recipes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'kellya-01221990'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def create_session_recipes():
    if not NO_RECIPES in session:
        session["recipes"] = []
        session[NO_RECIPES] = "no_recipes"


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id
    del session["recipes"]
    del session[NO_RECIPES]


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        

@app.route("/")
def home():
    
    if not CURR_USER_KEY in session:

        recipes = []

        create_session_recipes()

        page = {}

        if len(session["recipes"]) == 0:
            print("calling api")
            res = requests.get(f"{SPOONACULAR_RECIPES_URL}/random", params={"number":8, "apiKey": APIKEY}).json()

            page["page"] = 1

            for item in res["recipes"]:
                recipes.append({
                    "id": item["id"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "image": item["image"],
                    "cuisines": item["cuisines"],
                    "diets": item["diets"]
                    })

                RECIPES = recipes

                session["recipes"] = RECIPES

            print(page)
            return render_template("home.html", recipes=recipes, page=page)

        elif len(session["recipes"]) > 0:
            print("from session")
            recipes = session["recipes"]

            page["page"] = 1

            print(page)

            return render_template("home.html", recipes=recipes, page=page)
        

    elif session[CURR_USER_KEY]:
        user = User.query.get_or_404(CURR_USER_KEY).all()

        saved_recipes = user.saved_recipes
        created_recipes = user.created_recipes

        return render_template("", saved_recipes=saved_recipes, created_recipes=created_recipes )

# BROWSING FOR NON-USERS
@app.route("/browse")
def browse():
    searchRecipes = []

    offset = OFFSET

    args = request.args.get("search")
    page = int(request.args.get("page"))

    offset = OFFSET + ((page -1) * 20)
    

    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/complexSearch", params={"offset": offset, "query":{args}, "number":20, "apiKey": APIKEY}).json()

    for item in res["results"]:
        searchRecipes.append(item)

    return render_template("browse.html", searchRecipes=searchRecipes, page=page)

@app.route("/recipe/<int:id>")    
def recipe_details(id):
    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/information", params={"includeNutrition": True, "apiKey": APIKEY}).json()

    return render_template("recipe.html", recipe=recipe)



@app.route('/register', methods=["GET", "POST"])
def register():
    """Handle user register.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                username=form.username.data,
                password=form.password.data
            )
            db.session.commit()
            do_login(user)

            return redirect(f"users/{user.id}")

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/register.html', form=form)

    else:
        flash("There was an error, try again", 'danger')
        return render_template('users/register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(f"users/{user.id}")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS
    do_logout()
    flash("You have successfully logged out!", "success")
    return redirect("/login")

    
    if not CURR_USER_KEY in session:
        flash("You are not currently logged in!", "danger")
        return redirect("/login")

@app.route('/users/<int:user_id>')
def user_hub(user_id):
    user = User.query.get_or_404(user_id)

    return render_template("users/user_hub.html", user=user)


