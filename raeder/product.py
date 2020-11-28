import json
import datetime

import pymysql.cursors
import requests
from bs4 import BeautifulSoup

from raeder.category import ReadCategories


class GetProducts:
    def __init__(self):
        """Сбор ссылок на товары и запись их в json-файлы."""

        links = []

        categories = ReadCategories().categories
        for category in categories:
            print("*** *** ***")
            cat_data = {
                "category": category,
                "products": []
            }
            pages = [category]
            for page in pages:
                print(f"Loading page:\n{page}")
                html = requests.get(page).text
                bs = BeautifulSoup(html, "html.parser")

                # Ссылка на товар находится внутри блока с изображением.
                link_tags = bs.find_all(
                    "a", {"class": "sliderHover"}
                )

                for lt in link_tags:
                    if lt.attrs["href"] not in cat_data["products"]:
                        cat_data["products"].append(lt.attrs["href"])

                # Добавляем ссылки на следующие страницы к списку страниц.
                try:
                    pagination_div = bs.find("div", {"id": "itemsPagerbottom"})
                    page_links = pagination_div.find_all("a")
                    for pl in page_links:
                        if pl.attrs["href"] not in pages:
                            pages.append(pl.attrs["href"])
                except AttributeError:
                    # Для категорий, где всего одна страница с товарами.
                    pass

            links.append(cat_data)

        json_data = json.dumps(links)
        with open("./files/products.json", "w+") as json_file:
            json_file.write(json_data)

        print("Done!")


class ReadProducts:
    def __init__(self):
        with open("./files/products.json", "r") as json_file:
            json_data = json.load(json_file)

        self.products = json_data


class WriteProducts:
    def __init__(self):

        with open("./results.json", "r") as json_data:
            results = json.load(json_data)

        # Подключаемся к БД.
        connection = pymysql.connect(
            host="downlo04.mysql.tools",
            user="downlo04_parseditems",
            password="cu2%&52NzS",
            db="downlo04_parseditems",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        
        for r in results["results"]:
            with connection.cursor() as cursor:
                sql = f"INSERT INTO parsed_products (product_ref, parsed, updated, url, name, art, old_price, current_price, currency, description, material, color, dimensions, length, height, width, volume, images, category) VALUES ({r['product_ref']}, {round(datetime.datetime.now().timestamp())}, {round(datetime.datetime.now().timestamp())}, {r['url']}, {r['name']}, {r['art']}, {r['price']['old_price']}, {r['price']['price']}, {r['currency']}, {r['description']}, {r['parameters']['material']}, {r['parameters']['color']}, {r['parameters']['dimensions']}, {r['length']}, {r['height']}, {r['width']}, {r['parameters']['chars']['volume']}, {r['pictures']}, {r['cat_id']})"
            cursor.execute(sql)
            break
        connection.commit()
