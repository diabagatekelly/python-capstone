from datetime import timedelta
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, CreatedRecipe, SavedRecipe, Cuisine, Diet, Intolerance, FaveSavedRecipes, FaveCreatedRecipes, FaveCuisines, FaveDiets, FoodIntolerances, Saved_Recipe_Cuisine, Saved_Recipe_Diet, Saved_Recipe_Intolerance, Created_Recipe_Cuisine, Created_Recipe_Diet, Created_Recipe_Intolerance
from forms import UserAddForm, UserEditForm, LoginForm
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


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    if "recipes" in session:
        del session["recipes"]
        del session[NO_RECIPES]
    if "saveRecipe" in session:
        del session["saveRecipe"]
        

@app.route("/")
def home():
    page = {}
    if not CURR_USER_KEY in session or not "curr_user" in session:

        recipes = []

        create_session_recipes()

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
        

    elif session[CURR_USER_KEY] or 'curr_user' in session:
        user = User.query.get_or_404(session['curr_user'])
        savedRecipes = []
        createdRecipes = []

        page["page"] = 1


        saved_recipes = user.saved_recipes
        for item in saved_recipes:
            specificRes = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY}).json()
            savedRecipes.append(specificRes)

        created_recipes = user.created_recipes

        return render_template("users/home_logged_in.html", user=user, savedRecipes=savedRecipes, createdRecipes=createdRecipes, page=page )

# BROWSING FOR NON-USERS
@app.route("/browse")
def browse():
    searchRecipes = []

    offset = OFFSET

    args = request.args.get("search")
    page = int(request.args.get("page"))

    offset = OFFSET + ((page -1) * 20)
    

    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/complexSearch", params={"offset": offset, "query":{args}, "intolerances":"dairy", "number":20, "apiKey": APIKEY}).json()

    print(res)
    
    for item in res["results"]:
        searchRecipes.append(item)

    return render_template("browse.html", searchRecipes=searchRecipes, page=page)

@app.route("/recipe/<int:id>")
def recipe_details(id):
    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/information", params={"includeNutrition": True, "apiKey": APIKEY}).json()
    return render_template("recipe.html", recipe=res)



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

            if "saveRecipe" in session:
                    recipeID = session["saveRecipe"]
                    savedRecipe = SavedRecipe(api_id=recipeID)
                    db.session.add(savedRecipe)

                    helper = FaveSavedRecipes(user_id=user.id, recipes_id=recipeID)
                    db.session.add(helper)

                    db.session.commit()
                    del session["saveRecipe"]

            return redirect(f"users/{user.id}/preferences")

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/register.html', form=form)

    else:
        # flash("There was an error, try again", 'danger')
        return render_template('users/register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    if not CURR_USER_KEY in session:
        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)
            print(user)

            if user:
                do_login(user)

                if "saveRecipe" in session:
                    recipeID = session["saveRecipe"]
                    savedRecipe = SavedRecipe(api_id=recipeID)
                    db.session.add(savedRecipe)
                    db.session.commit()

                    helper = FaveSavedRecipes(user_id=user.id, recipes_id=recipeID)
                    db.session.add(helper)

                    db.session.commit()
                    del session["saveRecipe"]

                if user.new_user == True:
                    flash(f"Hello, {user.username}!", "success")
                    return redirect(f"users/{user.id}/preferences")
                elif user.new_user == False:
                    flash(f"Hello, {user.username}!", "success")
                    return redirect("/")

            flash("Invalid credentials.", 'danger')

        return render_template('users/login.html', form=form)

    elif "curr_user" in session:
        return redirect("/")


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


@app.route('/users/<int:user_id>/preferences', methods=["GET"])
def user_pref_form(user_id):
    if CURR_USER_KEY in session:
        user = User.query.get_or_404(user_id)
        if user.new_user == False:
            return redirect(f'/users/{user.id}/hub')
        else:
            exisitingfaveCuisines = FaveCuisines.query.filter_by(user_id=user_id).all()
            exisitingfaveDiets = FaveDiets.query.filter_by(user_id=user_id).all()
            exisitingFoodIntolerances = FoodIntolerances.query.filter_by(user_id=user_id).all()

            form = UserEditForm(obj=user)

            cuisines = db.session.query(Cuisine.id, Cuisine.name)
            diets = db.session.query(Diet.id, Diet.name)
            intolerances = db.session.query(Intolerance.id, Intolerance.name)

            form.fave_cuisines.choices = cuisines
            form.diets.choices = diets
            form.intolerances.choices = intolerances

            form.fave_cuisines.data = [(c.cuisines_id) for c in exisitingfaveCuisines ]
            form.diets.data = [(c.diets_id) for c in exisitingfaveDiets ]
            form.intolerances.data = [(c.intolerances_id) for c in exisitingFoodIntolerances ]
          
        return render_template("users/user_pref_form.html", user=user, form=form)


@app.route('/users/<int:user_id>/preferences/edit', methods=["POST"])
def user_pref_form_edit(user_id):
    if CURR_USER_KEY in session:
        user = User.query.get_or_404(user_id)
        exisitingfaveCuisines = FaveCuisines.query.all()
        exisitingfaveDiets = FaveDiets.query.all()
        exisitingFoodIntolerances = FoodIntolerances.query.all()

        cuisineIDs = []
        dietIDs = []
        intoleranceIDs = []

        for item in exisitingfaveCuisines:
            cuisineIDs.append(item.cuisines_id)

        for item in exisitingfaveDiets:
            dietIDs.append(item.diets_id)

        for item in exisitingFoodIntolerances:
            intoleranceIDs.append(item.intolerances_id)

        form = UserEditForm()

        cuisines = db.session.query(Cuisine.id, Cuisine.name)
        diets = db.session.query(Diet.id, Diet.name)
        intolerances = db.session.query(Intolerance.id, Intolerance.name)

        form.fave_cuisines.choices = cuisines
        form.diets.choices = diets
        form.intolerances.choices = intolerances

        if form.validate_on_submit():
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            if form.password.data == '':
                user.password = user.password
            elif form.password.data != '':
                user.password = form.password.data

            db.session.commit()

            new_fave_cuisines = form.fave_cuisines.data
            new_diets = form.diets.data
            new_intolerances = form.intolerances.data

            for current in exisitingfaveCuisines:
                if current.cuisines_id not in new_fave_cuisines:
                    deleted = FaveCuisines.query.filter_by(cuisines_id=current.cuisines_id).delete()

            for cuisine in new_fave_cuisines:
                if cuisine not in cuisineIDs:
                    newCuisine = FaveCuisines(user_id=user.id, cuisines_id=cuisine)
                    db.session.add(newCuisine)

            for current in exisitingfaveDiets:
                if current.diets_id not in new_diets:
                    deleted = FaveDiets.query.filter_by(diets_id=current.diets_id).delete()

            for diet in new_diets:
                if diet not in dietIDs:
                    newDiet = FaveDiets(user_id=user.id, diets_id=diet)
                    db.session.add(newDiet)
            
            for current in exisitingFoodIntolerances:
                if current.intolerances_id not in new_intolerances:
                    deleted = FoodIntolerances.query.filter_by(intolerances_id=current.intolerances_id).delete()

            for intol in new_intolerances:
                if intol not in intoleranceIDs:
                    newIntolerance = FoodIntolerances(user_id=user.id, intolerances_id=intol)
                    db.session.add(newIntolerance)

            user.new_user = False

            db.session.commit()
 
            flash("You successfully picked your food preferences", "success")
            return redirect(f"/users/{user.id}/hub")
            
    return redirect(f"/users/{user.id}/preferences")


@app.route('/users/<int:user_id>/hub')
def user_hub(user_id):
    if CURR_USER_KEY in session:
        user = User.query.get_or_404(user_id)
        saved_recipes = user.saved_recipes
        created_recipes = user.created_recipes

        return render_template("users/user_hub.html", user=user)
    else:
        flash("You must be logged in to access this page", 'danger')
        return redirect("/login") 

@app.route("/save_recipe/<int:id>")
def save_recipe(id):
    ID = id
    if CURR_USER_KEY in session:
        userId= session[CURR_USER_KEY]
        user = User.query.get_or_404(userId)

        savedRecipe = SavedRecipe(api_id=ID)
        db.session.add(savedRecipe)

        db.session.commit()


        helper = FaveSavedRecipes(user_id=userId, recipes_id=ID)
        db.session.add(helper)

        db.session.commit()

        flash("You successfully added this recipe to your library", 'success')

        return redirect("/")
    else: 
        session["saveRecipe"] = ID
        flash("Log in or Create an Account to save this recipe!", 'danger')
        return redirect("/login") 
