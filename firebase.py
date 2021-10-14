from chefkoch import ChefKochAPI, DataParser
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


if __name__ == '__main__':
    categories = ChefKochAPI.get_categories()
    amount = 300
    catname = "Hauptspeise"

    category = None

    for cat in categories:
        if cat.title == catname:
            category = cat
            break

    recipes = ChefKochAPI.parse_recipes(category, amount)

    firestre = db.collection(category.title).get()
    
    counter = 0
    for recipe in recipes:
        if recipe.id not in firestre:
            counter += 1
            db.collection(category.title).document(recipe.id).set(
                {
                    "id": int(recipe.id),
                    "name": recipe.name,
                    "img": recipe.img,
                    "categories": [cat for cat in recipe.categories],
                    "description": recipe.descrip,
                    "hints": [hint for hint in recipe.hints],
                    "ingredients": [ingredient.__dict__ for ingredient in recipe.ingredients],
                }
            )
    print("Done uploading " + counter + " Recipes to Firestore!")
