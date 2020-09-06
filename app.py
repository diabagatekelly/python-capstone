from datetime import timedelta
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify
from werkzeug.exceptions import HTTPException
from flask_session import Session
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, CreatedRecipe, SavedRecipe, CustomTag, Cuisine, Diet, Intolerance, FaveSavedRecipes, FaveCreatedRecipes, UserCustomTags, FaveCuisines, FaveDiets, FoodIntolerances, UserSavedRecipesCustom, UserSavedRecipesCuisine, UserCreatedRecipesCustom, UserCreatedRecipesCuisine, UserSavedRecipesDiet, UserCreatedRecipesDiet
from forms import UserAddForm, UserEditForm, LoginForm
import requests
import os
import keys

CURR_USER_KEY = "curr_user"
NO_RECIPES = "NO_RECIPES"
RECIPES = []
OFFSET = 0

SPOONACULAR_RECIPES_URL = "https://api.spoonacular.com/recipes"
APIKEY = keys.spoonacular_api_key

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql:///recipes')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kellya01sdlhLAKDS22hdjhjakshdk1990')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)
connect_db(app)

sess = Session()
sess.init_app(app)

@app.before_request
def make_session_permanent():
    """Establish session"""
    SESSION_PERMANENT = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def create_session_recipes():
    """Add recent API recipes to session"""
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
    if "saved_recipes" in session:
        del session["saved_recipes"]

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html'), 500


@app.route('/register', methods=["GET", "POST"])
def register():
    """Handle user register"""

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
        return render_template('users/register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    if not CURR_USER_KEY in session:
        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)

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
            else:
                flash("Invalid credentials.", 'danger')
                return render_template('users/login.html', form=form)
        else:
            return render_template('users/login.html', form=form)

    elif "curr_user" in session:
        return redirect("/")


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("You have successfully logged out!", "success")
    return redirect("/")
    
    if not CURR_USER_KEY in session:
        flash("You are not currently logged in!", "danger")
        return redirect("/login")
    

@app.route("/")
def home():
    page = {}

    if not CURR_USER_KEY in session or not 'curr_user' in session:
        recipes = []
        create_session_recipes()

        if len(session["recipes"]) == 0:
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

            return render_template("home.html", recipes=recipes, page=page)


        elif len(session["recipes"]) > 0:
            print("from session")
            recipes = session["recipes"]

            page["page"] = 1

            return render_template("home.html", recipes=recipes, page=page)
        

    elif session[CURR_USER_KEY] or 'curr_user' in session:
        user = User.query.get_or_404(session['curr_user'])
        savedRecipes = []
        createdRecipes = []

        page["page"] = 1

        saved_recipes = user.saved_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificRes = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY}).json()
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes
        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        DBSavedRecipes = saved_recipes

        created_recipes = user.created_recipes

        return render_template("users/home_logged_in.html", user=user, savedRecipes=savedRecipes, createdRecipes=createdRecipes, DBSavedRecipes=DBSavedRecipes, page=page)

# BROWSING 
@app.route("/browse")
def browse():
    searchRecipes = []
    totalResults = 0

    user = User.query.get_or_404(session["curr_user"])

    offset = OFFSET

    searchArgs = request.args.get("search")

    intolerances = [i.name for i in user.intolerances]
    intoleranceString = ' ,'.join(intolerances)

    searchDiets = request.args.getlist('diets')
    dietString = ' ,'.join(searchDiets)

    searchCuisines = request.args.getlist("cuisines")
    cuisineString = ' ,'.join(searchCuisines)
    

    page = int(request.args.get("page"))

    offset = OFFSET + ((page -1) * 20)   

    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/complexSearch", params={"offset": offset, "query":{searchArgs}, "intolerances": {intoleranceString}, "diet":{dietString}, "cuisine":{cuisineString}, "number":20, "sort": "popularity", "apiKey": APIKEY}).json()
    if not res["results"]:
        print(res)
    else:
        print("EVerything working fine")

    for item in res["results"]:
        searchRecipes.append(item)
    totalResults = res["totalResults"]

    return render_template("browse.html", searchRecipes=searchRecipes, page=page, user=user, totalResults=totalResults)


@app.route("/recipe/<int:id>")
def recipe_details(id):
    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/information", params={"includeNutrition": True, "apiKey": APIKEY}).json()

    if "curr_user" in session:
        user = User.query.get_or_404(session["curr_user"])
        helperRecipes = [c for c in user.saved_recipes if c.api_id == id]
        recipeLinkedCuisines = UserSavedRecipesCuisine.query.filter(UserSavedRecipesCuisine.user_id==session["curr_user"], UserSavedRecipesCuisine.recipe_id==helperRecipes[0].id).all()
        recipeLinkedDiets = UserSavedRecipesDiet.query.filter(UserSavedRecipesDiet.user_id==session["curr_user"], UserSavedRecipesDiet.recipe_id==helperRecipes[0].id).all()
        recipeLinkedCustoms = UserSavedRecipesCustom.query.filter(UserSavedRecipesCustom.user_id==session["curr_user"], UserSavedRecipesCustom.recipe_id==helperRecipes[0].id).all()

        form = UserEditForm()

        cuisines = db.session.query(Cuisine.id, Cuisine.name)
        diets = db.session.query(Diet.id, Diet.name)
        displayCustoms = db.session.query(CustomTag.id, CustomTag.name)

        form.fave_cuisines.choices = cuisines
        form.diets.choices = diets
        form.displayCustoms.choices = displayCustoms
       
        form.fave_cuisines.data = [(c.cuisine_id) for c in recipeLinkedCuisines]
        form.diets.data = [(c.diet_id) for c in recipeLinkedDiets ]
        form.displayCustoms.data = [(c.custom_id) for c in recipeLinkedCustoms ]

        return render_template("recipe.html", recipe=res, helperRecipes=helperRecipes, user=user, form=form)
    else:
        return render_template("recipe.html", recipe=res, helperRecipes=[])

@app.route("/recipe/<int:id>/similar")    
def similar_recipes(id):
    searchRecipes = []
    totalResults = 0

    page = int(request.args.get("page"))

    offset = OFFSET + ((page -1) * 20)

    res = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/similar", params={"offset": offset, "number": 20, "apiKey": APIKEY}).json()

    if len(res) == 0 or not res:
        print(res)
    else:
        print('Everything ok')

    searchRecipes = res
    totalResults = len(res)

    return render_template("browse.html", searchRecipes=searchRecipes, page=page, totalResults=totalResults)



@app.route("/save_recipe/<int:id>")
def save_recipe(id):
    ID = id
    if CURR_USER_KEY in session:
        userId= session[CURR_USER_KEY]
        recipesInDB = [(r.api_id) for r in SavedRecipe.query.all()]
        user = User.query.get_or_404(userId)

        if ID not in recipesInDB:
            savedRecipe = SavedRecipe(api_id=ID)
            db.session.add(savedRecipe)

            db.session.commit()

        helper = FaveSavedRecipes(user_id=userId, recipes_id=ID)
        db.session.add(helper)

        db.session.commit()

        del session["saved_recipes"]
        flash("You successfully added this recipe to your library", 'success')

        return redirect("/")
    else: 
        session["saveRecipe"] = ID
        flash("Log in or Create an Account to save this recipe!", 'danger')
        return redirect("/login") 


@app.route("/delete_recipe/<int:id>")
def delete_recipe(id):
    ID = id
    if "curr_user" in session:
        userId= session["curr_user"]
        recipe = FaveSavedRecipes.query.filter(FaveSavedRecipes.user_id == userId, FaveSavedRecipes.recipes_id == ID).delete()

        db.session.commit()

        del session["saved_recipes"]

        flash("You successfully deleted this recipe from your library", 'success')

        return redirect("/")
    else: 
        flash("You must be logged in to do this!", 'danger')
        return redirect("/login") 


@app.route("/recipe/<recipe_id>/editLibraryTags", methods=["POST"])
def recipe_tags(recipe_id):
    if CURR_USER_KEY in session or "curr_user" in session:
        user = User.query.get_or_404(session["curr_user"])
        savedRecipe = SavedRecipe.query.get_or_404(recipe_id)
        currentSavedRecipeCuisines = UserSavedRecipesCuisine.query.filter(UserSavedRecipesCuisine.user_id == user.id, UserSavedRecipesCuisine.recipe_id == savedRecipe.id).all()
        currentSavedRecipeDiets = UserSavedRecipesDiet.query.filter(UserSavedRecipesDiet.user_id == user.id, UserSavedRecipesDiet.recipe_id == savedRecipe.id).all()
        currentSavedRecipeCustomTags = UserSavedRecipesCustom.query.filter(UserSavedRecipesCustom.user_id == user.id, UserSavedRecipesCustom.recipe_id == savedRecipe.id).all()

        cuisineIDs = []
        dietIDs = []
        customIDs = []

        for item in currentSavedRecipeCuisines:
            cuisineIDs.append(item.cuisine_id)

        for item in currentSavedRecipeDiets:
            dietIDs.append(item.diet_id)

        for item in currentSavedRecipeCustomTags:
            customIDs.append(item.custom_id)

        form = UserEditForm()

        cuisines = db.session.query(Cuisine.id, Cuisine.name)
        diets = db.session.query(Diet.id, Diet.name)
        displayCustoms = db.session.query(CustomTag.id, CustomTag.name)


        form.fave_cuisines.choices = cuisines
        form.diets.choices = diets
        form.displayCustoms.choices = displayCustoms

        if form.is_submitted():

            recipe_cuisine_tags = form.fave_cuisines.data
            recipe_diet_tags = form.diets.data
            recipe_custom_tags = form.displayCustoms.data
 
            for cuisine in cuisineIDs:
                if cuisine not in recipe_cuisine_tags:
                    deleted = UserSavedRecipesCuisine.query.filter(UserSavedRecipesCuisine.cuisine_id==cuisine, UserSavedRecipesCuisine.user_id==user.id, UserSavedRecipesCuisine.recipe_id==recipe_id).delete()

            for cuisine in recipe_cuisine_tags:
                if cuisine not in cuisineIDs:
                    newCuisine = UserSavedRecipesCuisine(user_id=user.id, recipe_id=recipe_id, cuisine_id=cuisine)
                    db.session.add(newCuisine)

            for diet in dietIDs:
                if diet not in recipe_diet_tags:
                    deleted = UserSavedRecipesDiet.query.filter(UserSavedRecipesDiet.diet_id==diet, UserSavedRecipesDiet.user_id==user.id, UserSavedRecipesDiet.recipe_id==recipe_id).delete()

            for diet in recipe_diet_tags:
                if diet not in dietIDs:
                    newDiet = UserSavedRecipesDiet(user_id=user.id, recipe_id=recipe_id, diet_id=diet)
                    db.session.add(newDiet)

            for tag in customIDs:
                if tag not in recipe_custom_tags:
                    deleted = UserSavedRecipesCustom.query.filter(UserSavedRecipesCustom.custom_id==tag, UserSavedRecipesCustom.user_id==user.id, UserSavedRecipesCustom.recipe_id==recipe_id).delete()

            for tag in recipe_custom_tags:
                if tag not in customIDs:
                    newCustom = UserSavedRecipesCustom(user_id=user.id, recipe_id=recipe_id, custom_id=tag)
                    db.session.add(newCustom)       

            db.session.commit()
 
            flash("You successfully picked your food preferences", "success")
            return redirect(f"/users/{user.id}/hub")
            
    return redirect(f"/users/{user.id}/hub")

@app.route("/recipe/<recipe_id>/newTag")
def create_new_tags(recipe_id):
    user = User.query.get_or_404(session["curr_user"])
    recipe = SavedRecipe.query.filter_by(api_id=recipe_id).all()
    newTagRequest = request.args.get("newCustomTag")

    newTag = CustomTag(name=newTagRequest)
    db.session.add(newTag)
    db.session.commit()

    currentTag = CustomTag.query.filter_by(name=newTagRequest).all()
    userTag = UserCustomTags(user_id=user.id, custom_id=currentTag[0].id)
    userRecipeTag = UserSavedRecipesCustom(user_id=user.id, recipe_id=recipe[0].id, custom_id=currentTag[0].id)
    db.session.add(userTag)
    db.session.add(userRecipeTag)
    db.session.commit()

    return redirect(f"/recipe/{recipe_id}#editLibraryTags")



@app.route('/users/<int:user_id>/hub')
def user_hub(user_id):
    page = {}

    if CURR_USER_KEY in session or "curr_user" in session:
        user = User.query.get_or_404(user_id)
       
        saved_recipes = user.saved_recipes
        created_recipes = user.created_recipes
        recipeLinkedCuisines = UserSavedRecipesCuisine.query.filter(UserSavedRecipesCuisine.user_id==user.id).all()
        recipeLinkedDiets = UserSavedRecipesDiet.query.filter(UserSavedRecipesDiet.user_id==user.id).all()

        savedRecipes = []

        page["page"] = 1

        DBSavedRecipes = saved_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificRes = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY}).json()
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes

        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        return render_template("users/user_hub.html", user=user, savedRecipes=savedRecipes, page=page, DBSavedRecipes=DBSavedRecipes, recipeLinkedCuisines=recipeLinkedCuisines, recipeLinkedDiets=recipeLinkedDiets)

    else:
        flash("You must be logged in to access this page", 'danger')
        return redirect("/login") 



@app.route('/users/<int:user_id>/preferences', methods=["GET"])
def user_pref_form(user_id):
    if CURR_USER_KEY in session:
        user = User.query.get_or_404(user_id)
        exisitingfaveCuisines = FaveCuisines.query.filter_by(user_id=user_id).all()
        exisitingfaveDiets = FaveDiets.query.filter_by(user_id=user_id).all()
        exisitingFoodIntolerances = FoodIntolerances.query.filter_by(user_id=user_id).all()

        form = UserEditForm(obj=user)

        cuisines = db.session.query(Cuisine.id, Cuisine.name)
        diets = db.session.query(Diet.id, Diet.name)
        intolerances = db.session.query(Intolerance.id, Intolerance.name)
        # customs = db.session.query(CustomTag.id, CustomTag.name)

        form.fave_cuisines.choices = cuisines
        form.diets.choices = diets
        form.intolerances.choices = intolerances
        # form.displayCustoms.choices = customs

        form.fave_cuisines.data = [(c.cuisines_id) for c in exisitingfaveCuisines ]
        form.diets.data = [(c.diets_id) for c in exisitingfaveDiets ]
        form.intolerances.data = [(c.intolerances_id) for c in exisitingFoodIntolerances ]
            
        return render_template("users/user_pref_form.html", user=user, form=form)



@app.route('/users/<int:user_id>/preferences/edit', methods=["POST"])
def user_pref_form_edit(user_id):
    if CURR_USER_KEY in session:
        user = User.query.get_or_404(user_id)
        exisitingfaveCuisines = FaveCuisines.query.filter_by(user_id=user_id).all()
        exisitingfaveDiets = FaveDiets.query.filter_by(user_id=user_id).all()
        exisitingFoodIntolerances = FoodIntolerances.query.filter_by(user_id=user_id).all()

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

            print(f"hjghsdgghgagfffffffffffffffffffffffffffffffffffffffffff{exisitingfaveCuisines}")
            print(new_fave_cuisines)

            for current in exisitingfaveCuisines:
                if current.cuisines_id not in new_fave_cuisines:
                    deleted = FaveCuisines.query.filter(FaveCuisines.cuisines_id==current.cuisines_id, FaveCuisines.user_id==user.id).delete()

            for cuisine in new_fave_cuisines:
                if cuisine not in cuisineIDs:
                    newCuisine = FaveCuisines(user_id=user.id, cuisines_id=cuisine)
                    db.session.add(newCuisine)

            for current in exisitingfaveDiets:
                if current.diets_id not in new_diets:
                    deleted = FaveDiets.query.filter(FaveDiets.diets_id==current.diets_id, FaveDiets.user_id==user.id).delete()

            for diet in new_diets:
                if diet not in dietIDs:
                    newDiet = FaveDiets(user_id=user.id, diets_id=diet)
                    db.session.add(newDiet)
            
            for current in exisitingFoodIntolerances:
                if current.intolerances_id not in new_intolerances:
                    deleted = FoodIntolerances.query.filter(FoodIntolerances.intolerances_id==current.intolerances_id, FoodIntolerances.user_id==user.id).delete()

            for intol in new_intolerances:
                if intol not in intoleranceIDs:
                    newIntolerance = FoodIntolerances(user_id=user.id, intolerances_id=intol)
                    db.session.add(newIntolerance)

            user.new_user = False

            db.session.commit()

            print('after validate')
            flash("You successfully picked your food preferences", "success")
            return redirect(f"/users/{user.id}/hub")
            
    return redirect(f"/users/{user.id}/preferences")

@app.route('/users/<int:user_id>/library')
def user_library(user_id):
    page = {}
    page["page"] = 1
    if CURR_USER_KEY in session or "curr_user" in session:
        user = User.query.get_or_404(user_id)
       
        saved_recipes = user.saved_recipes
        created_recipes = user.created_recipes

        DBSavedRecipes = saved_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificRes = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY}).json()
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes

        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        return render_template("users/library.html", user=user, savedRecipes=savedRecipes, DBSavedRecipes=DBSavedRecipes, page=page)
    else:
        flash("You must be logged in to access this page", 'danger')

        return redirect('/login')

@app.route('/users/<int:user_id>/library/sort')
def user_library_sort(user_id):
    page = {}
    page["page"] = 1
    user = User.query.get_or_404(user_id)

    cuisinesRequest = request.args.getlist("cuisines")
    dietsRequest = request.args.getlist("diets")
    customsRequest = request.args.getlist("customs")

    print(customsRequest)

    return render_template("users/library.html", user=user, savedRecipes=savedRecipes, DBSavedRecipes=DBSavedRecipes, page=page)
