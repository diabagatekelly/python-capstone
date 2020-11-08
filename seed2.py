"""Seed database with sample data from CSV Files."""

from app import db
from models import db, connect_db, User, SavedRecipe, CustomTag, Cuisine, Diet, Intolerance, FaveSavedRecipes, FaveCreatedRecipes, UserCustomTags, FaveCuisines, FaveDiets, FoodIntolerances, UserSavedRecipesCustom, UserSavedRecipesCuisine, UserCreatedRecipesCustom, UserCreatedRecipesCuisine, UserSavedRecipesDiet, UserCreatedRecipesDiet

db.create_all()

db.session.commit()