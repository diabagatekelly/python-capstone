"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db
from models import User, Recipe, Cuisine, Diet, Intolerance, Recipe_Cuisine, Recipe_Diet, Recipe_Intolerance


db.drop_all()
db.create_all()

with open('generator/cuisines.csv') as cuisines:
    db.session.bulk_insert_mappings(Cuisine, DictReader(cuisines))

with open('generator/diets.csv') as diets:
    db.session.bulk_insert_mappings(Diet, DictReader(diets))

with open('generator/intolerances.csv') as intolerances:
    db.session.bulk_insert_mappings(Intolerance, DictReader(intolerances))

db.session.commit()