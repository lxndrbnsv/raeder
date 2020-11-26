import json

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
