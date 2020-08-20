"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db
from models import db, connect_db, User, CreatedRecipe, SavedRecipe, Cuisine, Diet, Intolerance, FaveSavedRecipes, FaveCreatedRecipes, FaveCuisines, FaveDiets, FoodIntolerances, Saved_Recipe_Cuisine, Saved_Recipe_Diet, Saved_Recipe_Intolerance, Created_Recipe_Cuisine, Created_Recipe_Diet, Created_Recipe_Intolerance


db.drop_all()
db.create_all()

with open('generator/cuisines.csv') as cuisines:
    db.session.bulk_insert_mappings(Cuisine, DictReader(cuisines))

with open('generator/diets.csv') as diets:
    db.session.bulk_insert_mappings(Diet, DictReader(diets))

with open('generator/intolerances.csv') as intolerances:
    db.session.bulk_insert_mappings(Intolerance, DictReader(intolerances))

db.session.commit()