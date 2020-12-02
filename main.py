import sys
import argparse

from raeder.product import ReadProducts, GetProducts, WriteProducts, UpdateProducts
from raeder.category import ScrapeCategoryProducts, AssignCategory, UpdateFetchedProducts
from raeder.misc import ReadLinksFromDB


sys.stdout = open("logs.log", "w")
sys.stderr = open("logs.log", "w")

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--full', action='store_true')
group.add_argument('--update', action='store_true')
args = parser.parse_args()


if __name__ == "__main__":
    # Первый парсинг
    if args.full:
        GetProducts()
        AssignCategory()
        products = ReadProducts().products
        ScrapeCategoryProducts(product_links=products)
        WriteProducts()
    # Обновление данных
    if args.update:
        UpdateFetchedProducts(links=ReadLinksFromDB().links)
        UpdateProducts()
