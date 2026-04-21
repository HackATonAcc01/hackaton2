import sys
from io import BytesIO  # Этот класс поможет нам сделать картинку из потока байт
import json

import requests
from PIL import Image

def get_spn(toponym):
    envelope = toponym["boundedBy"]["Envelope"]
    l_x, l_y = envelope["lowerCorner"].split()
    u_x, u_y = envelope["upperCorner"].split()
    delta = str(max(float(u_x) - float(l_x), float(u_y) - float(l_y)))
    return delta

# Пусть наше приложение предполагает запуск:
# python search.py Москва, ул. Ак. Королева, 12
# Тогда запрос к геокодеру формируется следующим образом:
# toponym_to_find = " ".join(sys.argv[1:])
toponym_to_find = input()

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)
print(response)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
with open('data.json', 'w') as f:
    json.dump(json_response, f)
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

delta = get_spn(toponym)
print(delta)
apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"

# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    "ll": ",".join([toponym_longitude, toponym_lattitude]),
    "spn": ",".join([delta, delta]),
    "apikey": apikey,
    "pt": ",".join([toponym_longitude, toponym_lattitude])

}

map_api_server = "https://static-maps.yandex.ru/v1"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)
im = BytesIO(response.content)
opened_image = Image.open(im)
opened_image.show()  # Создадим картинку и тут же ее покажем встроенным просмотрщиком операционной системы