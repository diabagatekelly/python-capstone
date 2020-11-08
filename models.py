from flask_sqlalchemy import SQLAlchemy

from flask_bcrypt import Bcrypt

db = SQLAlchemy()

def connect_db(app):
    db.app = app
    db.init_app(app)

# MAIN TABLES

class User(db.Model):
    """User."""

    __tablename__ = "users"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    username = db.Column(db.String(20), 
                        nullable=False)
    password = db.Column(db.Text, 
                        nullable=False)
    email = db.Column(db.String(50),
                        nullable=False,
                        unique=True)
    first_name = db.Column(db.String(30),
                        nullable=False)
    last_name = db.Column(db.String(30),
                        nullable=False)
    new_user = db.Column(db.Boolean,
                        default=True)

    created_recipes = db.relationship('CreatedRecipe', secondary="user_fave_created_recipes")
    saved_recipes = db.relationship('SavedRecipe', secondary="user_fave_saved_recipes")

    fave_cuisines = db.relationship('Cuisine', secondary="user_fave_cuisines")
    diets = db.relationship('Diet', secondary="user_diets")
    intolerances = db.relationship('Intolerance', secondary="user_food_intolerances")
    custom_tags = db.relationship('CustomTag', secondary="user_custom_tags")

    created_recipes_cuisine_tags = db.relationship('Cuisine', secondary="user_created_recipes_cuisine")
    saved_recipes_cuisine_tags = db.relationship('Cuisine', secondary="user_saved_recipes_cuisine")
    created_recipes_diet_tags = db.relationship('Diet', secondary="user_created_recipes_diet")
    saved_recipes_diet_tags = db.relationship('Diet', secondary="user_saved_recipes_diet")
    created_recipes_custom_tags = db.relationship('CustomTag', secondary="user_created_recipes_custom")
    saved_recipes_custom_tags = db.relationship('CustomTag', secondary="user_saved_recipes_custom")



    # start_register
    @classmethod
    def register(cls, first_name, last_name, email, username, password):
        """Register user w/hashed password & return user."""

        hashed = Bcrypt.generate_password_hash(cls, password, 14)
        # turn bytestring into normal (unicode utf8) string
        hashed_utf8 = hashed.decode("utf8")

        # return instance of user w/username and hashed pwd
        user = User(first_name=first_name, last_name=last_name, email=email, username=username, password=hashed_utf8)
        db.session.add(user)
        return user
    # end_register

    # start_authenticate
    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists & password is correct.

        Return user if valid; else return False.
        """

        u = User.query.filter_by(username=username).first()

        if u and Bcrypt.check_password_hash(cls, u.password, password):
            # return user instance
            return u
        else:
            return False
    # end_authenticate    


class SavedRecipe(db.Model):
    """Recipe."""

    __tablename__ = "saved_recipes"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    api_id = db.Column(db.Integer,
                        nullable=False, 
                        unique=True)
    
    user_saved_recipes = db.relationship('User', secondary="user_fave_saved_recipes")

    saved_recipes_linked_cuisine = db.relationship('Cuisine', secondary="user_saved_recipes_cuisine")
    saved_recipes_linked_diet = db.relationship('Diet', secondary="user_saved_recipes_diet")
    saved_recipes_linked_custom = db.relationship('CustomTag', secondary="user_saved_recipes_custom")



class CreatedRecipe(db.Model):
    """Recipe."""

    __tablename__ = "created_recipes"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    title = db.Column(db.Text,
                        nullable=False)
    directions = db.Column(db.Text,
                        nullable=False)
    ingredients = db.Column(db.ARRAY(db.String()),
                        nullable=False)
    servings = db.Column(db.Text,
                        nullable=False)
    cooking_time = db.Column(db.Text,
                        nullable=True)
    summary = db.Column(db.Text,
                        nullable=True)
    source = db.Column(db.Text,
                        nullable=True)
    weight_watchers_pts = db.Column(db.Text,
                        nullable=True)
    image = db.Column(db.Text,
                        nullable=True)
    calories = db.Column(db.Integer,
                        nullable=True)
    healthLabels = db.Column(db.ARRAY(db.String()),
                        nullable=True)
    fat = db.Column(db.Integer,
                        nullable=True)
    sat_fat = db.Column(db.Integer,
                        nullable=True)
    trans_fat = db.Column(db.Integer,
                        nullable=True)
    poly_fat = db.Column(db.Integer,
                        nullable=True)
    mono_fat = db.Column(db.Integer,
                        nullable=True)
    carbs = db.Column(db.Integer,
                        nullable=True)
    fiber = db.Column(db.Integer,
                        nullable=True)
    sugar = db.Column(db.Integer,
                        nullable=True)
    protein = db.Column(db.Integer,
                        nullable=True)
    cholesterol = db.Column(db.Integer,
                        nullable=True)
    sodium = db.Column(db.Integer,
                        nullable=True)
    vit_D = db.Column(db.Integer,
                        nullable=True)
    calcium = db.Column(db.Integer,
                        nullable=True)
    iron = db.Column(db.Integer,
                        nullable=True)
    potassium = db.Column(db.Integer,
                        nullable=True)
    vit_A = db.Column(db.Integer,
                        nullable=True)
    vit_C = db.Column(db.Integer,
                        nullable=True)

    user_created_recipes = db.relationship('User', secondary="user_fave_created_recipes")

    created_recipes_linked_cuisine = db.relationship('Cuisine', secondary="user_created_recipes_cuisine")
    created_recipes_linked_diet = db.relationship('Diet', secondary="user_created_recipes_diet")
    created_recipes_linked_custom = db.relationship('CustomTag', secondary="user_created_recipes_custom")


class CustomTag(db.Model):
    """Custom Tag"""

    __tablename__="custom_tags"

    id = db.Column(db.Integer, 
                    primary_key=True,
                    autoincrement=True)
    name = db.Column(db.Text, 
                        nullable=False)
    
    user = db.relationship('User', secondary="user_custom_tags")

    linked_saved_recipe = db.relationship('SavedRecipe', secondary="user_saved_recipes_custom")
    linked_created_recipe = db.relationship('CreatedRecipe', secondary="user_created_recipes_custom")

class Cuisine(db.Model):
    """Cuisine"""

    __tablename__="cuisines"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    name = db.Column(db.Text, 
                        nullable=False)
    
    user = db.relationship('User', secondary="user_fave_cuisines")

    linked_saved_recipe = db.relationship('SavedRecipe', secondary="user_saved_recipes_cuisine")
    linked_created_recipe = db.relationship('CreatedRecipe', secondary="user_created_recipes_cuisine")
    

class Diet(db.Model):
    """Diet"""

    __tablename__="diets"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    name = db.Column(db.Text, 
                        nullable=False)
    
    user = db.relationship('User', secondary="user_diets")

    linked_saved_recipe = db.relationship('SavedRecipe', secondary="user_saved_recipes_diet")
    linked_created_recipe = db.relationship('CreatedRecipe', secondary="user_created_recipes_diet")


class Intolerance(db.Model):
    """Intolerance"""

    __tablename__="intolerances"

    id = db.Column(db.Integer, 
                        primary_key=True,
                        autoincrement=True)
    name = db.Column(db.Text, 
                        nullable=False)

    user = db.relationship('User', secondary="user_food_intolerances")


# HELPER TABLES - USER

class FaveSavedRecipes(db.Model):
    __tablename__ = 'user_fave_saved_recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    recipes_id = db.Column(db.Integer, db.ForeignKey('saved_recipes.api_id', ondelete="CASCADE"))

class FaveCreatedRecipes(db.Model):
    __tablename__ = 'user_fave_created_recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    recipes_id = db.Column(db.Integer, db.ForeignKey('created_recipes.id', ondelete="CASCADE"))

class UserCustomTags(db.Model):
    __tablename__ = 'user_custom_tags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    custom_id = db.Column(db.Integer, db.ForeignKey('custom_tags.id', ondelete="CASCADE"))


class FaveCuisines(db.Model):
    __tablename__ = 'user_fave_cuisines'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    cuisines_id = db.Column(db.Integer, db.ForeignKey('cuisines.id', ondelete="CASCADE"))


class FaveDiets(db.Model):
    __tablename__ = 'user_diets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    diets_id = db.Column(db.Integer, db.ForeignKey('diets.id', ondelete="CASCADE"))


class FoodIntolerances(db.Model):
    __tablename__ = 'user_food_intolerances'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    intolerances_id = db.Column(db.Integer, db.ForeignKey('intolerances.id', ondelete="CASCADE"))


#HELPER TABLES - RECIPES

class UserSavedRecipesCustom(db.Model):
    """Recipe_Custom Link"""

    __tablename__ = "user_saved_recipes_custom"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('saved_recipes.id'))
    custom_id = db.Column(db.Integer, db.ForeignKey('custom_tags.id'))

class UserCreatedRecipesCustom(db.Model):
    """Recipe_Cuisine Link"""

    __tablename__="user_created_recipes_custom"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('created_recipes.id'))
    custom_id = db.Column(db.Integer, db.ForeignKey('custom_tags.id'))


class UserSavedRecipesCuisine(db.Model):
    """Recipe_Cuisine Link"""

    __tablename__="user_saved_recipes_cuisine"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('saved_recipes.id'))
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisines.id'))


class UserCreatedRecipesCuisine(db.Model):
    """Recipe_Cuisine Link"""

    __tablename__="user_created_recipes_cuisine"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('created_recipes.id'))
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisines.id'))


class UserSavedRecipesDiet(db.Model):
    """Recipe_Diet Link"""

    __tablename__="user_saved_recipes_diet"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('saved_recipes.id'))
    diet_id = db.Column(db.Integer, db.ForeignKey('diets.id'))


class UserCreatedRecipesDiet(db.Model):
    """Recipe_Diet Link"""

    __tablename__="user_created_recipes_diet"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('created_recipes.id'))
    diet_id = db.Column(db.Integer, db.ForeignKey('diets.id'))


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
