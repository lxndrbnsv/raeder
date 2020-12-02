import string
import random

import pymysql.cursors


class GenerateRefCode:
    def __init__(self):
        def generate():
            letters = string.ascii_letters
            digits = string.digits

            with open("./files/ref_codes.txt", "r") as txt_file:
                text_data = txt_file.readlines()

            existing_codes = []
            for t in text_data:
                existing_codes.append(t.replace("\n", ""))

            char_num = 1
            ref_code = "".join(
                random.choice(digits) for __ in range(char_num)
            )
            while ref_code in existing_codes:
                char_num = char_num + 1
                ref_code = "".join(
                    random.choice(digits) for __ in range(char_num)
                )

            return int(ref_code)

        value = generate()
        with open("./files/ref_codes.txt", "a+") as text_file:
            text_file.write(f"{value}\n")

        self.value = value


class ReadDB:
    def __init__(self, value):
        # Подключаемся к БД.
        connection = pymysql.connect(
            host="downlo04.mysql.tools",
            user="downlo04_parseditems",
            password="cu2%&52NzS",
            db="downlo04_parseditems",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connection.cursor() as cursor:
                sql = (
                    "SELECT * FROM parsed_products WHERE "
                    "shop_id LIKE %s "
                )
                cursor.execute(sql, value)
                result = cursor.fetchall()

        finally:
            connection.close()
        self.result = result


class GenerateName:
    def __init__(self, charnum):
        def generate():
            letters = string.ascii_letters
            digits = string.digits

            char_num = charnum
            ref_code = "".join(
                random.choice(letters + digits) for __ in range(char_num)
            )

            return ref_code

        value = generate()

        self.value = value


class ReadLinksFromDB:
    def __init__(self):
        links = []
        # Подключаемся к БД.
        connection = pymysql.connect(
            host="downlo04.mysql.tools",
            user="downlo04_parseditems",
            password="cu2%&52NzS",
            db="downlo04_parseditems",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connection.cursor() as cursor:
                sql = (
                    "SELECT * FROM parsed_products WHERE "
                    "shop_id=1"
                )
                cursor.execute(sql)
                result = cursor.fetchall()

        finally:
            connection.close()
        for r in result:
            links.append(r["url"])
        self.links = links
