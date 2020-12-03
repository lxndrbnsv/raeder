import re
import os
import json
import datetime

import requests
from bs4 import BeautifulSoup

from raeder.misc import GenerateRefCode, GenerateName


class GetCategories:
    def __init__(self):
        """Рекурсивный сбор категорий с сайта. Запись категорий в файл."""
        url = "https://www.raeder-onlineshop.de/"
        html = requests.get(url).text

        print("Launched")

        bs = BeautifulSoup(html, "html.parser")

        nav_bar = bs.find("ul", {"id": "navigation"})

        # Получаем категории.
        categories = []

        # Первая ссылка - новинки, последняя - акции. Эти ссылки мы игнорируем.
        nav_links = nav_bar.find_all("a")[1:-1]

        print("Iterating through categories...")

        for n in nav_links:
            print(f"Parsing category: {n.attrs['href']}")
            # Далее переходим по ссылкам категорий и получаем подгатегории.
            subcat_url = n.attrs["href"]
            subcat_html = requests.get(subcat_url).text
            subcat_bs = BeautifulSoup(subcat_html, "html.parser")

            sidebar = subcat_bs.find("div", {"class": "sidebar-menu"})
            subcat_links = sidebar.find_all("a")

            # Получаем категории, находящиеся внутри подкатегорий.
            print("Iterating through subcategories...")
            for s in subcat_links:
                print(f"Parsing subcategory {s.attrs['href']}")
                sub_sub_url = s.attrs["href"]
                sub_sub_html = requests.get(sub_sub_url).text
                sub_sub_bs = BeautifulSoup(sub_sub_html, "html.parser")
                category_list = sub_sub_bs.find(
                    "div", {"class": "category-list"}
                )

                # Если внутри подкатегории нет категории, то к списку категорий
                # добавляем ссылку на категорию.
                try:
                    for p in category_list.find_all(
                        "p", {"class": "item-title"}
                    ):
                        print("Parsing inner categories.")
                        categories.append(p.find("a").attrs["href"])
                        print("Inner category collected.")
                except AttributeError:
                    categories.append(sub_sub_url)
                    print(
                        "No inner categories. "
                        "Subcategory link has been collected."
                    )

        # Записываем категории в файл.
        with open("./files/categories.txt", "a+") as text_file:
            for c in categories:
                text_file.write(f"{c}\n")

        print("Written!")


class ReadCategories:
    def __init__(self):
        """Возвращает список категорий из файла."""
        with open("./files/categories.txt", "r") as text_file:
            text_data = text_file.readlines()

        cats = []

        for t in text_data:
            if t.replace("\n", "") not in cats:
                cats.append(t.replace("\n", ""))

        self.categories = cats


class AssignCategory:
    def __init__(self):
        with open("./files/categories.json", "r") as json_file:
            json_data_cats = json.load(json_file)

        with open("./files/products.json") as json_file:
            json_data_products = json.load(json_file)

        for jp in json_data_products:
            for jc in json_data_cats:
                if jp["category"] == jc["cat"]:
                    jp["cat_id"] = jc["cat_id"]

        json_data = json.dumps(json_data_products)

        with open("./files/products.json", "w") as json_file:
            json_file.write(json_data)


class ScrapeCategoryProducts:
    def __init__(self, product_links):
        """Сбор данных товаров, принадлежащих к определенной категории."""

        def if_available():
            additional_info_div = bs.find(
                "div", {"class": "additionalInfo clear"}
            )
            if additional_info_div.find(
                    "span", {"class": "notOnStock"}
            ) is not None:
                return 0
            else:
                return 1

        def get_name():
            """Возвращает название товара."""
            return bs.find("h1").get_text().strip()

        def get_art():
            """Возвращает артикул товара."""
            return bs.find("input", {"id": "artid"}).attrs["value"]

        def get_product_ref():
            return GenerateRefCode().value

        def get_price():
            """Возвращает стоимость товара: стоимость
            со скидкой и старую цену."""
            product_price = (
                bs.find("span", {"itemprop": "price"}).attrs["content"].strip()
            )
            try:
                old_price = (
                    bs.find("p", {"class": "oldPrice"})
                    .find("del")
                    .get_text()
                    .replace(" €", "")
                    .strip()
                )

            except AttributeError:
                old_price = None

            price_data = dict(price=product_price, old_price=old_price)
            return price_data

        def get_currency():
            """Возвращает валюту стоимости товара."""
            return "EUR"

        def get_description():
            """Возвращает описание товара."""
            # Тег, внутри которого содержится первая часть характеристик
            # товара, является следующим по отношению к родительскому тегу
            # тега input, в котором расположен артикул.
            description_p = (
                bs.find("input", {"id": "artid"})
                .find_parent("p")
                .find_next_sibling("p")
            )

            # Разбиваем на две части: до br и после. Это нужно для грамотного
            # форматирования текста.
            text_1 = description_p.find("br").previous.strip()
            text_2 = description_p.find("br").next.strip()

            # Данные о материале находятся в отдельном диве.
            material = bs.find("div", {"id": "material"}).get_text().strip()

            rating = (
                bs.find("div", {"id": "rating"}).get_text().replace("\n", " ")
            )

            #  Объединяем все данные.
            desc = f"{text_1}\n{text_2}\n{material}\n{rating}"

            return desc

        def get_parameters():
            """Возвращает словарь с характеристиками товара."""
            # Данные получаем из текста описания.
            product_text = description

            try:
                material = (
                    product_text.split("Material: ", 1)[1]
                    .split("\n", 1)[0]
                    .strip()
                )
            except IndexError:
                material = None
            try:
                color = (
                    product_text.split("Farbe: ", 1)[1]
                    .split("\n", 1)[0]
                    .strip()
                )
            except IndexError:
                color = None
            try:
                dimensions = (
                    product_text.split("Maße: ", 1)[1]
                    .split("\n", 1)[0]
                    .split("cm", 1)[0]
                    .strip()
                )
            except IndexError:
                dimensions = None
            if dimensions is not None:
                if "x" not in dimensions:
                    dimensions = None
            try:
                diameter = (
                    product_text.split("Durchmesser: ", 1)[1]
                    .split("\n", 1)[0]
                    .split("cm", 1)[0]
                    .strip()
                )
            except IndexError:
                diameter = None
            try:
                volume = (
                    product_text.split("Füllmenge: ", 1)[1]
                    .split("\n", 1)[0]
                    .split("ml", 1)[0]
                    .replace("ca.", "")
                    .strip()
                )
            except IndexError:
                volume = None
            try:
                hgt = product_text.split(
                    "Höhe: ", 1
                )[1].split("\n", 1)[0].split("cm", 1)[0].strip()
            except IndexError:
                hgt = None
            try:
                lgt = product_text.split(
                    "Länge: ", 1
                )[1].split("\n", 1)[0].split("cm", 1)[0].strip()
            except IndexError:
                lgt = None

            params = dict(
                material=material,
                dimensions=dimensions,
                chars=dict(
                    volume=volume,
                    diameter=diameter,
                    add_hgt=hgt,
                    add_lgt=lgt,
                ),
                color=color,
            )

            return params

        def get_height():
            non_decimal = re.compile(r"[^\d.]+")
            try:
                dims = []
                params_data = parameters["dimensions"].split("x", 3)
                for pd in params_data:
                    try:
                        dims.append(
                            float(
                                non_decimal.sub(
                                    "", pd.strip().replace(",", ".")
                                )
                            )
                        )
                    except ValueError:
                        pass
                dims.sort()
                try:
                    h = dims[-1]
                except IndexError:
                    h = None

            except AttributeError:
                h = None

            if h is not None:
                h = str(h)

            return h

        def get_length():
            non_decimal = re.compile(r"[^\d.]+")
            try:
                dims = []
                params_data = parameters["dimensions"].split("x", 3)
                for pd in params_data:
                    try:
                        dims.append(
                            float(
                                non_decimal.sub(
                                    "", pd.strip().replace(",", ".")
                                )
                            )
                        )
                    except ValueError:
                        pass
                dims.sort()
                if len(dims) == 3:
                    lngt = dims[1]
                else:
                    try:
                        lngt = dims[0]
                    except IndexError:
                        lngt = None
            except AttributeError:
                lngt = None

            if lngt is not None:
                lngt = str(lngt)

            return lngt

        def get_width():
            non_decimal = re.compile(r"[^\d.]+")
            try:
                dims = []
                params_data = parameters["dimensions"].split("x", 3)
                for pd in params_data:
                    try:
                        dims.append(
                            float(
                                non_decimal.sub(
                                    "", pd.strip().replace(",", ".")
                                )
                            )
                        )
                    except ValueError:
                        pass
                dims.sort()
                if len(dims) == 3:
                    w = dims[0]
                else:
                    w = None
            except AttributeError:
                w = None

            if w is not None:
                w = str(w)

            return w

        def download_pictures():
            """Сохраняет изображения товара. Возвращает ссылку
            на путь к изображениям товара."""
            pics = []

            # Если у товара доступны несколько изображений,
            # берем ссылки на оригиналы изображений из блока предпросмотра.
            try:
                pics_div = bs.find("div", {"class": "otherPictures"})
                for span in pics_div.find_all("span", {"class": "artIcon"}):
                    pics.append(span.find("img").attrs["data-zoom-image"])
            except AttributeError:
                try:
                    pics.append(
                        bs.find("div", {"class": "product-picture"})
                        .find("a")
                        .attrs["href"]
                    )
                except AttributeError:
                    pics = []

            if not os.path.exists(f"./files/pics/{str(shop_id)}/"):
                os.makedirs(f"./files/pics/{str(shop_id)}/")

            image_files = os.listdir(f"./files/pics/{str(shop_id)}/")
            image_names = []
            for i in image_files:
                image_names.append(i.split(".", 1)[0])

            char_num = 1
            image_name = GenerateName(charnum=char_num).value
            while image_names in image_names:
                char_num = char_num + 1
                image_name = GenerateName(charnum=char_num).value

            pic_names = []

            for pic in pics:
                r = requests.get(pic, allow_redirects=True)
                open(
                    f"./files/pics/{shop_id}/{image_name}.jpg", "wb"
                ).write(r.content)
                pic_names.append(f"{image_name}.jpg")


            return {"pics_all": pics, "pic_names": pic_names}

        def manage_pics():
            additional_pic_urls = []
            for p in pictures["pic_names"]:
                additional_pic_urls.append(
                    f"http://3.127.139.108/api/images/{shop_id}/{p}"
                )
            if len(pictures["pics_all"]) == 1:
                return dict(
                    main_pic=pictures["pics_all"][0],
                    additional_pics=[],
                    main_pic_url=f"http://3.127.139.108/api/images/{shop_id}/"
                                 f"{pictures['pic_names'][0]}",
                    additional_pic_urls=additional_pic_urls
                )
            if len(pictures["pics_all"]) >= 2:
                return dict(
                    main_pic=pictures["pics_all"][0],
                    additional_pics=pictures["pics_all"][1:],
                    main_pic_url=f"http://3.127.139.108/api/images/{shop_id}/"
                                 f"{pictures['pic_names'][0]}",
                    additional_pic_urls=additional_pic_urls
                )
            if len(pictures["pics_all"]) == 0:
                return dict(
                    main_pic=[],
                    additional_pics=[],
                    main_pic_url=[],
                    additional_pic_urls=additional_pic_urls
                )

        def get_language():
            """Возвращает язык, на котором опубликована информация
            о товаре."""
            return "DE"

        def get_additional_attrs():
            data = parameters
            additional_params = []
            if data["chars"]["diameter"] is not None:
                dmtr = data["chars"]["diameter"]
                additional_params.append(
                    "Diameter:" + dmtr
                )
            if data["chars"]["add_hgt"] is not None:
                hgt = data["chars"]["add_hgt"]
                additional_params.append(
                    "Height:" + hgt
                )
            if data["chars"]["add_lgt"] is not None:
                lgt = data["chars"]["add_lgt"]
                additional_params.append(
                    "Length:" + lgt
                )

            if len(additional_params) > 0:
                return "\n".join(additional_params)
            else:
                return None

        results = dict(
            first_parsed=round(datetime.datetime.now().timestamp()),
            updated=round(datetime.datetime.now().timestamp()),
            results=[],
        )
        for product_link in product_links:
            for pr in product_link["products"]:

                print(pr)
                shop_id = "1"

                html = requests.get(pr).text
                bs = BeautifulSoup(html, "html.parser")

                available = if_available()
                name = get_name()
                art = get_art()
                product_ref = get_product_ref()
                price = get_price()
                currency = get_currency()
                description = get_description()
                parameters = get_parameters()
                height = get_height()
                length = get_length()
                width = get_width()
                pictures = download_pictures()
                pic_dict = manage_pics()
                language = get_language()
                try:
                    result = dict(
                        shop_id=shop_id,
                        available=available,
                        timestamp=round(datetime.datetime.now().timestamp()),
                        cat_id=product_link["cat_id"],
                        url=pr,
                        name=name,
                        art=art,
                        product_ref=product_ref,
                        price=price,
                        currency=currency,
                        description=description,
                        parameters=parameters,
                        height=height,
                        length=length,
                        width=width,
                        pictures=pictures,
                        img_main=pic_dict["main_pic"],
                        img_additional=pic_dict["additional_pics"],
                        img_main_url=pic_dict["main_pic_url"],
                        img_additional_url=pic_dict["additional_pic_urls"],
                        language=language,
                        additional_attrs=get_additional_attrs()
                    )

                    results["results"].append(result)

                    print("--- --- ---")
                except AttributeError:
                    pass

        res = json.dumps(results)
        with open("./results.json", "w+") as json_file:
            json_file.write(res)


class UpdateFetchedProducts:
    def __init__(self, links):
        """Сбор данных товаров, принадлежащих к определенной категории."""

        def if_available():
            additional_info_div = bs.find(
                "div", {"class": "additionalInfo clear"}
            )
            if additional_info_div.find(
                    "span", {"class": "notOnStock"}
            ) is not None:
                return 0
            else:
                return 1

        def get_price():
            """Возвращает стоимость товара: стоимость
            со скидкой и старую цену."""
            product_price = (
                bs.find("span", {"itemprop": "price"}).attrs["content"].strip()
            )
            try:
                old_price = (
                    bs.find("p", {"class": "oldPrice"})
                    .find("del")
                    .get_text()
                    .replace(" €", "")
                    .strip()
                )

            except AttributeError:
                old_price = None

            price_data = dict(price=product_price, old_price=old_price)
            return price_data


        results = dict(
            first_parsed=round(datetime.datetime.now().timestamp()),
            updated=round(datetime.datetime.now().timestamp()),
            results=[],
        )
        for product_link in links:

            print(product_link)

            html = requests.get(product_link).text
            bs = BeautifulSoup(html, "html.parser")
            try:
                available = if_available()
                price = get_price()
            

                result = dict(
                    available=available,
                    price=price,
                )

                results["results"].append(result)

                print("--- --- ---")
            except AttributeError:
                result = dict(
                    available=5,
                    price=dict(price="0", old_price="0"),
                )
                results["results"].append(result)

        res = json.dumps(results)
        with open("./updates.json", "w+") as json_file:
            json_file.write(res)
