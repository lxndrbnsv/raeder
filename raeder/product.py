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
    def __init__(self, data):

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
        for r in results:
            with connection.cursor() as cursor:
                sql = "INSERT INTO parsed_products (" \
                      " shop_id," \
                      " product_ref," \
                      " parsed," \
                      " updated," \
                      " url," \
                      " name," \
                      " art," \
                      " old_price," \
                      " current_price," \
                      " currency," \
                      " description," \
                      " material," \
                      " color," \
                      " dimensions," \
                      " length," \
                      " height," \
                      " width," \
                      " volume," \
                      " images," \
                      " category" \
                      f") VALUES ({r['results']['shop_id']}," \
                      f"{r['results']['product_ref']}," \
                      f"{round(datetime.datetime.now().timestamp())}," \
                      f"{round(datetime.datetime.now().timestamp())}," \
                      f"{r['results']['url']}," \
                      f"{r['results']['name']}," \
                      f"{r['results']['art']}," \
                      f"{r['results']['price']['old_price']}," \
                      f"{r['results']['price']['current_price']}," \
                      f"{r['results']['currency']}," \
                      f"{r['results']['description']}," \
                      f"{r['results']['material']}," \
                      f"{r['results']['color']}," \
                      f"{r['results']['dimensions']}," \
                      f"{r['results']['length']}," \
                      f"{r['results']['height']}," \
                      f"{r['results']['width']}," \
                      f"{r['results']['volume']}," \
                      f"{r['results']['images']}," \
                      f"{r['cat_id']} " \
                      "'test2', 'test2') "
            cursor.execute(sql)
            connection.commit()
