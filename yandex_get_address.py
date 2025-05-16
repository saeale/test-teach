import sys
import requests

API_KEY_GEOCODE = '8013b162-6b42-4997-9691-77b7074026e0'
API_KEY_STATIC = 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13'


def geocode(address):
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey={API_KEY_GEOCODE}" \
                       f"&geocode={address}&format=json"

    response = requests.get(geocoder_request)

    if response:
        json_response = response.json()
    else:
        raise RuntimeError(
            """Ошибка выполнения запроса:
            {request}
            Http статус: {status} ({reason})""".format(
                request=geocoder_request, status=response.status_code, reason=response.reason))

    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    return features[0]["GeoObject"] if features else None


def get_coordinates(address):
    top = geocode(address)
    if not top:
        return None, None

    top_coords = top["Point"]["pos"]
    longitude, lattitude = top_coords.split(" ")
    return float(longitude), float(lattitude)


def get_photo(address, path):
    long, lat = get_coordinates(address)
    if not long or not lat:
        return None
    ll_spn = f'll={long},{lat}&spn=0.001,0.001'

    map_request = f"https://static-maps.yandex.ru/v1?apikey={API_KEY_STATIC}&{ll_spn}"
    response = requests.get(map_request)

    try:
        with open(path, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка:", ex)


