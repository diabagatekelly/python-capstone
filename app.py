from datetime import timedelta
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify, json
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from flask_session import Session
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, CreatedRecipe, SavedRecipe, CustomTag, Cuisine, Diet, Intolerance, FaveSavedRecipes, FaveCreatedRecipes, UserCustomTags, FaveCuisines, FaveDiets, FoodIntolerances, UserSavedRecipesCustom, UserSavedRecipesCuisine, UserCreatedRecipesCustom, UserCreatedRecipesCuisine, UserSavedRecipesDiet, UserCreatedRecipesDiet
from forms import UserAddForm, UserEditForm, LoginForm, CreateRecipeForm
import requests
import os
import re
import ast
from keys import Keys
from recipe_scrapers import scrape_me


CURR_USER_KEY = "curr_user"
NO_RECIPES = "NO_RECIPES"
RECIPES = []
OFFSET = 0

SPOONACULAR_RECIPES_URL = "https://api.spoonacular.com/recipes"
EDAMAM_URL = "https://api.edamam.com/api/nutrition-details"

APIKEY = os.environ.get('APIKEY')
# APIKEY = os.environ.get('APIKEY', Keys.spoonacular_api_key)

EDAMAM_APP_ID = os.environ.get('EDAMAM_APP_ID')
# EDAMAM_APP_ID = os.environ.get('EDAMAM_APP_ID', Keys.edamam_app_id)

EDAMAM_APP_KEY = os.environ.get('EDAMAM_APP_KEY')
# EDAMAM_APP_KEY = os.environ.get('EDAMAM_APP_KEY', Keys.edamam_app_key)

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
    if "created_recipes" in session:
        del session["created_recipes"]

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
            result = requests.get(f"{SPOONACULAR_RECIPES_URL}/random", params={"number":8, "apiKey": APIKEY})
            print(f'total used: {result.headers["X-API-Quota-Used"]}, this call:{result.headers["X-API-Quota-Request"]}')

            res = result.json()
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
        created_recipes = user.created_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificResult = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY})
                print(f'total used: {specificResult.headers["X-API-Quota-Used"]}, this call:{specificResult.headers["X-API-Quota-Request"]}')

                specificRes = specificResult.json()
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes
        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        if not 'created_recipes' in session:
            print('calling db for created recipes')
            for item in created_recipes:
                createdRecipes.append(item)

            session['created_recipes'] = createdRecipes
        elif 'created_recipes' in session:
            print('calling session for created recipes')
            createdRecipes = session['created_recipes']

        print(session["created_recipes"])
        DBSavedRecipes = saved_recipes
        DBCreatedRecipes = created_recipes

        return render_template("users/home_logged_in.html", user=user, savedRecipes=savedRecipes, createdRecipes=createdRecipes, DBSavedRecipes=DBSavedRecipes, DBCreatedRecipes=DBCreatedRecipes, page=page)

# BROWSING 
@app.route("/browse")
def browse():
    searchRecipes = []
    totalResults = 0

    if "curr_user" in session:

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

        result = requests.get(f"{SPOONACULAR_RECIPES_URL}/complexSearch", params={"offset": offset, "query":{searchArgs}, "intolerances": {intoleranceString}, "diet":{dietString}, "cuisine":{cuisineString}, "number":20, "sort": "popularity", "apiKey": APIKEY})
        print(f'total used: {result.headers["X-API-Quota-Used"]}, this call:{result.headers["X-API-Quota-Request"]}')

        res = result.json()
        if not res["results"]:
            print(res)
        else:
            print("EVerything working fine")

        for item in res["results"]:
            searchRecipes.append(item)
        totalResults = res["totalResults"]

        return render_template("browse.html", searchRecipes=searchRecipes, page=page, user=user, totalResults=totalResults)
    else:
        user = None
        offset = OFFSET

        searchArgs = request.args.get("search")

        intoleranceString = ''

        dietString = ''

        cuisineString = ''
        
        page = int(request.args.get("page"))

        offset = OFFSET + ((page -1) * 20)   

        result = requests.get(f"{SPOONACULAR_RECIPES_URL}/complexSearch", params={"offset": offset, "query":{searchArgs}, "intolerances": {intoleranceString}, "diet":{dietString}, "cuisine":{cuisineString}, "number":20, "sort": "popularity", "apiKey": APIKEY})
        
        print(f'total used: {result.headers["X-API-Quota-Used"]}, this call:{result.headers["X-API-Quota-Request"]}')

        res = result.json()
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
    result = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/information", params={"includeNutrition": True, "apiKey": APIKEY})

    print(f'total used: {result.headers["X-API-Quota-Used"]}, this call:{result.headers["X-API-Quota-Request"]}')

    res = result.json()
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

@app.route('/users/<int:user_id>/created-recipe/<int:id>')
def created_recipe(user_id, id):
    if "curr_user" in session:
        user = User.query.get_or_404(user_id)
        recipe = CreatedRecipe.query.get_or_404(id)
        helperRecipes = [c for c in user.created_recipes if c.id == id]

        recipeLinkedCuisines = UserCreatedRecipesCuisine.query.filter(UserCreatedRecipesCuisine.user_id==user_id, UserCreatedRecipesCuisine.recipe_id==helperRecipes[0].id).all()
        recipeLinkedDiets = UserCreatedRecipesDiet.query.filter(UserCreatedRecipesDiet.user_id==user_id, UserCreatedRecipesDiet.recipe_id==helperRecipes[0].id).all()
        recipeLinkedCustoms = UserCreatedRecipesCustom.query.filter(UserCreatedRecipesCustom.user_id==user_id, UserCreatedRecipesCustom.recipe_id==helperRecipes[0].id).all()

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


        return render_template("users/created_recipe.html", user=user, recipe=recipe, form=form, helperRecipes=helperRecipes)
    else:
        flash("You must be logged in to access this page", 'danger')

        return redirect('/')


@app.route("/recipe/<int:id>/similar")    
def similar_recipes(id):
    searchRecipes = []
    totalResults = 0

    page = int(request.args.get("page"))

    offset = OFFSET + ((page -1) * 20)

    result = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/similar", params={"offset": offset, "number": 20, "apiKey": APIKEY})

    print(f'total used: {result.headers["X-API-Quota-Used"]}, this call:{result.headers["X-API-Quota-Request"]}')

    res = result.json()
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

        # Adding new saved recipe to session
        getRecforSession = requests.get(f"{SPOONACULAR_RECIPES_URL}/{id}/information", params={"includeNutrition": True, "apiKey": APIKEY})

        print(f'total used: {getRecforSession.headers["X-API-Quota-Used"]}, this call:{getRecforSession.headers["X-API-Quota-Request"]}')

        res = getRecforSession.json()

        session["saved_recipes"].append(res)
        flash("You successfully added this recipe to your library", 'success')

        return redirect("/")
    else: 
        session["saveRecipe"] = ID
        flash("Log in or Create an Account to save this recipe!", 'danger')
        return redirect("/login")


@app.route("/users/<int:user_id>/created-recipe/<int:id>/edit", methods=["GET", "POST"])
def edit_created_recipe(user_id, id):
    if CURR_USER_KEY in session:
        recipe = CreatedRecipe.query.get_or_404(id)
        user = User.query.get_or_404(user_id)
        analysisIngr = []

        form = CreateRecipeForm(obj=recipe)

        if form.validate_on_submit():
            recipe.title = form.title.data
            recipe.servings = form.servings.data
            recipe.cooking_time = form.cooking_time.data
            recipe.summary = form.summary.data
            recipe.weight_watchers_pts = form.weight_watchers_pts.data
            image = form.image.data
            filename = secure_filename(image.filename)
            if filename:
                image.save(os.path.join("static", 'images', filename))
                recipe.image = image.filename
            else:
                recipe.image

            if '[' in form.ingredients.data:
                print('running as list')
                analysisIngr = ast.literal_eval(form.ingredients.data)
            else:
                print('running as string')
                analysisIngr = form.ingredients.data.split(',\r\n')
               
            recDir = form.directions.data

            if recipe.ingredients != analysisIngr:
                print('recalling edamam api for updated recipe')
                recipeUpdate = {
                "title": form.title.data,
                "yield": form.servings.data,
                "ingr": analysisIngr
                }

                recipeAnalysis = requests.post(f"{EDAMAM_URL}?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}",  data = json.dumps(recipeUpdate), headers = {"Content-Type": "application/json", "Accept": "application/json"})

                analysisRes = recipeAnalysis.json()
            
                healthLabels = analysisRes["healthLabels"] + analysisRes["dietLabels"]
            
                recipe.calories=analysisRes["calories"] 
                recipe.healthLabels=healthLabels
                recipe.fat=analysisRes["totalNutrients"]["FAT"]["quantity"]
                recipe.sat_fat=analysisRes["totalNutrients"]["FASAT"]["quantity"]
                recipe.trans_fat=analysisRes["totalNutrients"]["FATRN"]["quantity"]
                recipe.poly_fat=analysisRes["totalNutrients"]["FAPU"]["quantity"]
                recipe.mono_fat=analysisRes["totalNutrients"]["FAMS"]["quantity"]
                recipe.carbs=analysisRes["totalNutrients"]["CHOCDF"]["quantity"]
                recipe.fiber=analysisRes["totalNutrients"]["FIBTG"]["quantity"]
                recipe.sugar=analysisRes["totalNutrients"]["SUGAR"]["quantity"]
                recipe.protein=analysisRes["totalNutrients"]["PROCNT"]["quantity"]
                recipe.cholesterol=analysisRes["totalNutrients"]["CHOLE"]["quantity"]
                recipe.sodium=analysisRes["totalNutrients"]["NA"]["quantity"]
                recipe.vit_D=analysisRes["totalDaily"]["VITD"]["quantity"]
                recipe.calcium=analysisRes["totalDaily"]["CA"]["quantity"]
                recipe.iron=analysisRes["totalDaily"]["FE"]["quantity"]
                recipe.potassium=analysisRes["totalDaily"]["K"]["quantity"]
                recipe.vit_A=analysisRes["totalDaily"]["VITA_RAE"]["quantity"]
                recipe.vit_C=analysisRes["totalDaily"]["VITC"]["quantity"]

            recipe.ingredients = analysisIngr
            recipe.directions = recDir
                
            db.session.commit()

            if "created_recipes" in session:
                del session["created_recipes"]

            flash("You successfully edited this recipe", 'success')

            return redirect(f"/users/{user_id}/created-recipe/{id}")
        
        return render_template("users/edit_recipe.html", user=user, form=form)

       
    else: 
        flash("You must be logged in to edit this recipe!", 'danger')
        return redirect("/login") 


@app.route("/delete_recipe/<int:id>")
def delete_recipe(id):
    ID = id
    if "curr_user" in session:
        userId= session["curr_user"]
        recipe = FaveSavedRecipes.query.filter(FaveSavedRecipes.user_id == userId, FaveSavedRecipes.recipes_id == ID).delete()

        db.session.commit()

        for item in session['saved_recipes']:
            if item['id'] == ID:
                session["saved_recipes"].remove(item)

        flash("You successfully deleted this recipe from your library", 'success')

        return redirect("/")
    else: 
        flash("You must be logged in to do this!", 'danger')
        return redirect("/login") 

@app.route("/users/<int:user_id>/created-recipe/<int:id>/delete")
def delete_created_recipe(user_id, id):
    if "curr_user" in session:
        userId= user_id
        faveRecipe = FaveCreatedRecipes.query.filter(FaveCreatedRecipes.user_id == userId, FaveCreatedRecipes.recipes_id == id).delete()
        createdRecipe = CreatedRecipe.query.filter_by(id=id).delete()

        db.session.commit()

        if 'created_recipes' in session:
            del session["created_recipes"]

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

@app.route("/users/<int:user_id>/created-recipe/<int:recipe_id>/editLibraryTags", methods=["POST"])
def recipe_tags_created_recipes(user_id, recipe_id):
    if CURR_USER_KEY in session or "curr_user" in session:
        user = User.query.get_or_404(user_id)
        createdRecipe = CreatedRecipe.query.get_or_404(recipe_id)
        currentCreatedRecipeCuisines = UserCreatedRecipesCuisine.query.filter(UserCreatedRecipesCuisine.user_id == user.id, UserCreatedRecipesCuisine.recipe_id == createdRecipe.id).all()
        currentCreatedRecipeDiets = UserCreatedRecipesDiet.query.filter(UserCreatedRecipesDiet.user_id == user.id, UserCreatedRecipesDiet.recipe_id == createdRecipe.id).all()
        currentCreatedRecipeCustomTags = UserCreatedRecipesCustom.query.filter(UserCreatedRecipesCustom.user_id == user.id, UserCreatedRecipesCustom.recipe_id == createdRecipe.id).all()

        cuisineIDs = []
        dietIDs = []
        customIDs = []

        for item in currentCreatedRecipeCuisines:
            cuisineIDs.append(item.cuisine_id)

        for item in currentCreatedRecipeDiets:
            dietIDs.append(item.diet_id)

        for item in currentCreatedRecipeCustomTags:
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
                    deleted = UserCreatedRecipesCuisine.query.filter(UserCreatedRecipesCuisine.cuisine_id==cuisine, UserCreatedRecipesCuisine.user_id==user.id, UserCreatedRecipesCuisine.recipe_id==recipe_id).delete()

            for cuisine in recipe_cuisine_tags:
                if cuisine not in cuisineIDs:
                    newCuisine = UserCreatedRecipesCuisine(user_id=user.id, recipe_id=recipe_id, cuisine_id=cuisine)
                    db.session.add(newCuisine)

            for diet in dietIDs:
                if diet not in recipe_diet_tags:
                    deleted = UserCreatedRecipesDiet.query.filter(UserCreatedRecipesDiet.diet_id==diet, UserCreatedRecipesDiet.user_id==user.id, UserCreatedRecipesDiet.recipe_id==recipe_id).delete()

            for diet in recipe_diet_tags:
                if diet not in dietIDs:
                    newDiet = UserCreatedRecipesDiet(user_id=user.id, recipe_id=recipe_id, diet_id=diet)
                    db.session.add(newDiet)

            for tag in customIDs:
                if tag not in recipe_custom_tags:
                    deleted = UserCreatedRecipesCustom.query.filter(UserCreatedRecipesCustom.custom_id==tag, UserCreatedRecipesCustom.user_id==user.id, UserCreatedRecipesCustom.recipe_id==recipe_id).delete()

            for tag in recipe_custom_tags:
                if tag not in customIDs:
                    newCustom = UserCreatedRecipesCustom(user_id=user.id, recipe_id=recipe_id, custom_id=tag)
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

@app.route("/users/<int:user_id>/created-recipe/<int:recipe_id>/newTag")
def create_new_tags_created_recipe(recipe_id):
    user = User.query.get_or_404(user_id)
    recipe = CreatedRecipe.query.filter_by(id=recipe_id).all()
    newTagRequest = request.args.get("newCustomTag")

    newTag = CustomTag(name=newTagRequest)
    db.session.add(newTag)
    db.session.commit()

    currentTag = CustomTag.query.filter_by(name=newTagRequest).all()
    userTag = UserCustomTags(user_id=user.id, custom_id=currentTag[0].id)
    userRecipeTag = UserCreatedRecipesCustom(user_id=user.id, recipe_id=recipe[0].id, custom_id=currentTag[0].id)
    db.session.add(userTag)
    db.session.add(userRecipeTag)
    db.session.commit()

    return redirect(f"/users/{user_id}/created-recipe/{recipe_id}#editLibraryTags")


@app.route('/users/<int:user_id>/hub')
def user_hub(user_id):
    page = {}

    if CURR_USER_KEY in session or "curr_user" in session:
        user = User.query.get_or_404(user_id)
       
        saved_recipes = user.saved_recipes
        created_recipes = user.created_recipes
        recipeLinkedCuisines = UserSavedRecipesCuisine.query.filter(UserSavedRecipesCuisine.user_id==user.id).all()
        recipeLinkedDiets = UserSavedRecipesDiet.query.filter(UserSavedRecipesDiet.user_id==user.id).all()
        createdRecipeLinkedCuisines = UserCreatedRecipesCuisine.query.filter(UserCreatedRecipesCuisine.user_id==user.id).all()
        createdRecipeLinkedDiets = UserCreatedRecipesDiet.query.filter(UserCreatedRecipesDiet.user_id==user.id).all()

        savedRecipes = []
        createdRecipes = []

        page["page"] = 1

        DBSavedRecipes = saved_recipes
        DBCreatedRecipes = created_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificResult = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY})
                print(f'total used: {specificResult.headers["X-API-Quota-Used"]}, this call:{specificResult.headers["X-API-Quota-Request"]}')

                specificRes = specificResult.json()
               
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes

        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        if not 'created_recipes' in session:
            print('calling db for created recipes')
            for item in created_recipes:
                createdRecipes.append(item)

            session['created_recipes'] = createdRecipes

        elif 'created_recipes' in session:
            print('calling session for created recipes')
            createdRecipes = session['created_recipes']

        return render_template("users/user_hub.html", user=user, createdRecipes=createdRecipes, savedRecipes=savedRecipes, page=page, DBSavedRecipes=DBSavedRecipes, DBCreatedRecipes=DBCreatedRecipes, recipeLinkedCuisines=recipeLinkedCuisines, recipeLinkedDiets=recipeLinkedDiets, createdRecipeLinkedCuisines=createdRecipeLinkedCuisines, createdRecipeLinkedDiets=createdRecipeLinkedDiets)

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
        DBCreatedRecipes = created_recipes

        if not 'saved_recipes' in session:
            print('calling api for saved recipes')
            for item in saved_recipes:
                specificResult = requests.get(f"{SPOONACULAR_RECIPES_URL}/{item.api_id}/information", params={"apiKey": APIKEY})
                
                print(f'total used: {specificResult.headers["X-API-Quota-Used"]}, this call:{specificResult.headers["X-API-Quota-Request"]}')

                specificRes = specificResult.json()
                savedRecipes.append(specificRes)

            session['saved_recipes'] = savedRecipes

        elif 'saved_recipes' in session:
            print('calling session for saved recipes')
            savedRecipes = session['saved_recipes']

        if not 'created_recipes' in session:
            print('calling api for created recipes')
            for item in created_recipes:
                createdRecipes.append(item)

            session['created_recipes'] = createdRecipes

        elif 'created_recipes' in session:
            print('calling session for created recipes')
            createdRecipes = session['created_recipes']

        return render_template("users/library.html", user=user, savedRecipes=savedRecipes, createdRecipes=createdRecipes, DBSavedRecipes=DBSavedRecipes, DBCreatedRecipes=DBCreatedRecipes, page=page)
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

    return render_template("users/library.html", user=user, savedRecipes=savedRecipes, DBSavedRecipes=DBSavedRecipes, page=page)


@app.route('/create-recipe', methods=['GET', 'POST'])
def create_recipe():
    if CURR_USER_KEY in session or "curr_user" in session:

        recipeArr = []
        user_id = session["curr_user"]
        user = User.query.get_or_404(user_id)

        form = CreateRecipeForm()

        if form.validate_on_submit():
            title = form.title.data
            servings = form.servings.data
            cooking_time = form.cooking_time.data
            summary = form.summary.data
            weight_watchers_pts = form.weight_watchers_pts.data
            image = form.image.data
            directions = form.directions.data
            filename = secure_filename(image.filename)
            if filename:
                image.save(os.path.join("static", 'images', filename))

            analysisIngr = form.ingredients.data.split(',\r\n')
            ingredients = analysisIngr

            recipe = {
                "title": form.title.data,
                "yield": form.servings.data,
                "ingr": analysisIngr
            }

            recipeAnalysis = requests.post(f"{EDAMAM_URL}?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}",  data = json.dumps(recipe), headers = {"Content-Type": "application/json", "Accept": "application/json"})

            analysisRes = recipeAnalysis.json()
            
            healthLabels = analysisRes["healthLabels"] + analysisRes["dietLabels"]

            source = f"{user.first_name} {user.last_name}"

            new_recipe = CreatedRecipe(title=title, source=source, directions=directions, ingredients=ingredients, servings=servings, cooking_time=cooking_time, summary=summary, weight_watchers_pts=weight_watchers_pts, image=image.filename, calories=analysisRes["calories"], healthLabels=healthLabels, fat=analysisRes["totalNutrients"]["FAT"]["quantity"], sat_fat=analysisRes["totalNutrients"]["FASAT"]["quantity"], trans_fat=analysisRes["totalNutrients"]["FATRN"]["quantity"], poly_fat=analysisRes["totalNutrients"]["FAPU"]["quantity"], mono_fat=analysisRes["totalNutrients"]["FAMS"]["quantity"], carbs=analysisRes["totalNutrients"]["CHOCDF"]["quantity"], fiber=analysisRes["totalNutrients"]["FIBTG"]["quantity"], sugar=analysisRes["totalNutrients"]["SUGAR"]["quantity"], protein=analysisRes["totalNutrients"]["PROCNT"]["quantity"], cholesterol=analysisRes["totalNutrients"]["CHOLE"]["quantity"], sodium=analysisRes["totalNutrients"]["NA"]["quantity"], vit_D=analysisRes["totalDaily"]["VITD"]["quantity"], calcium=analysisRes["totalDaily"]["CA"]["quantity"], iron=analysisRes["totalDaily"]["FE"]["quantity"], potassium=analysisRes["totalDaily"]["K"]["quantity"], vit_A=analysisRes["totalDaily"]["VITA_RAE"]["quantity"], vit_C=analysisRes["totalDaily"]["VITC"]["quantity"])

            db.session.add(new_recipe)

            db.session.commit()

            helper = FaveCreatedRecipes(user_id=user_id, recipes_id=new_recipe.id)
            
            db.session.add(helper)

            db.session.commit()

            recipeArr.append(new_recipe)

            if session["created_recipes"]:
                session["created_recipes"].append(new_recipe)
            else:
                session["created_recipes"] = recipeArr
        
            return redirect(f'users/{user_id}/created-recipe/{new_recipe.id}')

        return render_template("users/create_recipe.html", user=user, form=form)

    else:
        flash("You must be logged in to access this page", 'danger')

        return redirect('/login')

@app.route('/extract-recipe', methods=["GET", "POST"])
def extract_recipe():
    if "curr_user" in session:
        searchArgs = request.args.get("search")
        savedArgs = request.args.get("saved")
        user_id = session["curr_user"]
        user = User.query.get_or_404(user_id)
        recipeArr = []
        finalRecipe = {}

        if not savedArgs and searchArgs:
            print('about to extract')
            extracted_recipe = scrape_me(searchArgs,  wild_mode=True)

            title = extracted_recipe.title()
            total_time = extracted_recipe.total_time()
            yields_servings = extracted_recipe.yields()
            ingredients = extracted_recipe.ingredients()
            instructions = extracted_recipe.instructions()
            image = extracted_recipe.image()
            source = extracted_recipe.host()
            links = extracted_recipe.links()

            print(type(instructions))
            yields = yields_servings.split(' ')[0]

            getRecNutrition = {
                "title": title,
                "yield": yields,
                "ingr": ingredients
            }

            recipeAnalysis = requests.post(f"{EDAMAM_URL}?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}",  data = json.dumps(getRecNutrition), headers = {"Content-Type": "application/json", "Accept": "application/json"})

            analysisRes = recipeAnalysis.json()

            healthLabels = analysisRes["healthLabels"] + analysisRes["dietLabels"]
            calories = analysisRes["calories"] 
            fat=analysisRes["totalNutrients"]["FAT"]["quantity"] 
            sat_fat=analysisRes["totalNutrients"]["FASAT"]["quantity"]
            trans_fat=analysisRes["totalNutrients"]["FATRN"]["quantity"]
            poly_fat=analysisRes["totalNutrients"]["FAPU"]["quantity"]
            mono_fat=analysisRes["totalNutrients"]["FAMS"]["quantity"]
            carbs=analysisRes["totalNutrients"]["CHOCDF"]["quantity"]
            fiber=analysisRes["totalNutrients"]["FIBTG"]["quantity"]
            sugar=analysisRes["totalNutrients"]["SUGAR"]["quantity"]
            protein=analysisRes["totalNutrients"]["PROCNT"]["quantity"]
            cholesterol=analysisRes["totalNutrients"]["CHOLE"]["quantity"]
            sodium=analysisRes["totalNutrients"]["NA"]["quantity"]
            vit_D=analysisRes["totalDaily"]["VITD"]["quantity"]
            calcium=analysisRes["totalDaily"]["CA"]["quantity"]
            iron=analysisRes["totalDaily"]["FE"]["quantity"]
            potassium=analysisRes["totalDaily"]["K"]["quantity"]
            vit_A=analysisRes["totalDaily"]["VITA_RAE"]["quantity"]
            vit_C=analysisRes["totalDaily"]["VITC"]["quantity"]
            
            recipe = {
                "calories": calories,
                "healthLabels": healthLabels,
                "fat": fat,
                "sat_fat": sat_fat,
                "trans_fat": trans_fat,
                "poly_fat": poly_fat,
                "mono_fat": mono_fat,
                "carbs": carbs,
                "fiber": fiber,
                "sugar": sugar,
                "protein": protein,
                "cholesterol": cholesterol,
                "sodium": sodium,
                "vit_D": vit_D,
                "calcium": calcium,
                "iron": iron,
                "potassium": potassium,
                "vit_A": vit_A,
                "vit_C": vit_C
            }

            alltogether = {
                "title": title,
                "directions": instructions,
                "ingredients": ingredients,
                "servings": yields,
                "cooking_time": total_time,
                "image": image,
                "source": source,
                "nutrition": recipe
            }
            
            session["finalRecipe"] = alltogether
            
            return render_template('users/extracted_rec.html', user=user, title=title, total_time=total_time, yields=yields, ingredients=ingredients, instructions=instructions, image=image, source=source, links=links, recipe=recipe)
    
        elif savedArgs:
            print('about to save')
            if 'finalRecipe' in session:
                finalRecipe = session["finalRecipe"]

                print(finalRecipe["directions"])
                print(type(finalRecipe["directions"]))
                
                new_recipe = CreatedRecipe(title=finalRecipe["title"], directions=finalRecipe["directions"], ingredients=finalRecipe["ingredients"], servings=finalRecipe["servings"], cooking_time=finalRecipe["cooking_time"], image=finalRecipe["image"], calories=finalRecipe["nutrition"]["calories"], healthLabels=finalRecipe["nutrition"]["healthLabels"], fat=finalRecipe["nutrition"]["fat"], sat_fat=finalRecipe["nutrition"]["sat_fat"], trans_fat=finalRecipe["nutrition"]["trans_fat"], poly_fat=finalRecipe["nutrition"]["poly_fat"], mono_fat=finalRecipe["nutrition"]["mono_fat"], carbs=finalRecipe["nutrition"]["carbs"], fiber=finalRecipe["nutrition"]["fiber"], sugar=finalRecipe["nutrition"]["sugar"], protein=finalRecipe["nutrition"]["protein"], cholesterol=finalRecipe["nutrition"]["cholesterol"], sodium=finalRecipe["nutrition"]["sodium"], vit_D=finalRecipe["nutrition"]["vit_D"], calcium=finalRecipe["nutrition"]["calcium"], iron=finalRecipe["nutrition"]["iron"], potassium=finalRecipe["nutrition"]["potassium"], vit_A=finalRecipe["nutrition"]["vit_A"], vit_C=finalRecipe["nutrition"]["vit_C"])
                
                db.session.add(new_recipe)

                db.session.commit()

                helper = FaveCreatedRecipes(user_id=user_id, recipes_id=new_recipe.id)
                
                db.session.add(helper)

                db.session.commit()

                recipeArr.append(new_recipe)

                if session["created_recipes"]:
                    session["created_recipes"].append(new_recipe)
                else:
                    session["created_recipes"] = recipeArr
            
                return redirect(f'users/{user_id}/created-recipe/{new_recipe.id}')

        return render_template('extract.html')

    else:
        return redirect('/login')

