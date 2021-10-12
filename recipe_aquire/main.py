from chefkoch import ChefKochAPI, DataParser

if __name__ == '__main__':
    categories = ChefKochAPI.get_categories()

    category = None

    for cat in categories:
        if cat.title == "Hauptspeise":
            category = cat
            break

    recipes = ChefKochAPI.parse_recipes(category, 5)

    DataParser.write_recipes_to_json(category.title, recipes)
