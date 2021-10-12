import requests as rq
from bs4 import BeautifulSoup
import re
import json


class Category:
    id_pattern = re.compile("(/rs/s0)(g\d*)")

    def __init__(self, title, url=None, id=None):
        self.title = title.replace("&", "")
        if url is not None:
            self.id = Category.id_pattern.search(url).group(2)
        if id is not None:
            self.id = id

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)


class Ingredient:
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)


class Recipe:
    def __init__(self, name, img, id, category, ingredients):
        self.name = name
        self.img = img
        self.id = id
        self.category = category
        self.ingredients = ingredients

    @staticmethod
    def from_json(json_obj):
        name = json_obj['name']
        img = json_obj['img']
        id = json_obj['id']
        category = Category(json_obj['category']['title'], id=json_obj['category']['id'])
        ingredients = [Ingredient(ingredient['name'], ingredient['amount']) for ingredient in json_obj['ingredients']]
        return Recipe(name, img, id, category, ingredients)

    def __str__(self):
        return json.dumps({
            "name": self.name,
            "img": self.img,
            "id": self.id,
            "category": self.category.__dict__,
            "ingredients": [ingredient.__dict__ for ingredient in self.ingredients]
        }, ensure_ascii=False)


class ChefKochAPI:
    base_url = "https://www.chefkoch.de/"

    @staticmethod
    def get_categories():
        response = rq.get(ChefKochAPI.base_url + "rezepte/kategorien/")
        soup = BeautifulSoup(response.text, "html5lib")

        categories = []
        for category_column in soup.findAll("div", {"class": "category-column"}):
            for category_container in category_column.findChildren():
                category = category_container.find('a', href=True)
                try:
                    title = category.string
                    url = category["href"]
                except Exception:
                    continue
                categories.append(Category(title, url=url))

        return categories

    @staticmethod
    def parse_recipes(category, end_index=0, start_index=0):

        index = start_index
        while True:
            # Actual part before .html is irrelevant, but site wont serve any results if missing
            response = rq.get(ChefKochAPI.base_url + 'rs/' + 's' + str(index) + category.id + '/recipes.html')
            if response.status_code == 404:
                return
            soup = BeautifulSoup(response.text, "html5lib")

            for recipe_list_item in soup.find_all("a", {"class": "rsel-recipe"}):

                index += 1

                recipe_id = recipe_list_item['href'].replace("https://www.chefkoch.de/rezepte/", "")
                recipe_id = recipe_id[0: recipe_id.index('/')]
                recipe_url = recipe_list_item['href']
                recipe_response = rq.get(recipe_url)

                if recipe_response.status_code != 200:
                    continue

                recipe_soup = BeautifulSoup(recipe_response.text, "html5lib")
                all_imgs = recipe_soup.find_all("img")
                recipe_img_url = all_imgs[0]['src']
                recipe_name = recipe_soup.find("h1").contents[0]
                ingredients_table = recipe_soup.find("table", {"class": "ingredients"})
                ingredients_table_body = ingredients_table.find("tbody")

                recipe_ingredients = []
                for row in ingredients_table_body.find_all('tr'):
                    cols = row.find_all('td')
                    recipe_ingredients.append(
                        Ingredient(re.sub(' +', ' ', cols[1].text.strip().replace(u"\u00A0", " ")),
                                   re.sub(' +', ' ', cols[0].text.strip().replace(u"\u00A0", " "))))

                yield Recipe(recipe_name.replace(u"\u00A0", " "), recipe_img_url.replace(u"\u00A0", " "), recipe_id.replace(u"\u00A0", " "),
                             category, recipe_ingredients)

                if 0 < end_index < index:
                    return


class DataParser:

    @staticmethod
    def write_recipes_to_json(file_path, recipes, ):
        with open(file_path + ".json", "w") as txt_file:
            txt_file.write("[")
            for recipe in recipes:
                try:
                    txt_file.write(str(recipe))
                    txt_file.write(",")
                except Exception:
                    pass
            txt_file.write("{}]")

    @staticmethod
    def load_recipes_from_json(file_path):
        raw_text = ""
        with open(file_path) as file:
            raw_text = file.read()

        recipes = []
        for obj in json.loads(raw_text):
            if len(obj.keys()) > 0:
                recipes.append(Recipe.from_json(obj))
        return recipes
