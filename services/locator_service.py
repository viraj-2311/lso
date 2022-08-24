import math

import requests

from config import Config


def get_drop_box_service_center(l1, g1, locator_type, miles):
    url = Config.LOCATOR_URL

    response = requests.get(url)
    deg_to_radians = math.pi / 180.0
    radius_of_earth = 3963.0

    l1 = float(l1) * deg_to_radians
    g1 = float(g1) * deg_to_radians

    final_list = []
    for i in response.json():
        if locator_type == "Both":
            lat = i.get('Lat')
            lon = i.get('Lon')
            if lat != 'None' and lon != 'None' and lat and lon:
                distance = (radius_of_earth * math.acos((math.sin(l1) * math.sin(float(lat) * deg_to_radians)) + (
                        math.cos(l1) * math.cos(float(lat) * deg_to_radians) * math.cos(
                    (float(lon) * deg_to_radians) - g1))))
                if distance <= miles:
                    i['distance'] = distance
                    final_list.append(i)
        elif i.get('Type') == locator_type:
            lat = i.get('Lat')
            lon = i.get('Lon')
            if lat != 'None' and lon != 'None' and lat and lon:
                distance = (radius_of_earth * math.acos((math.sin(l1) * math.sin(float(lat) * deg_to_radians)) + (
                        math.cos(l1) * math.cos(float(lat) * deg_to_radians) * math.cos(
                    (float(lon) * deg_to_radians) - g1))))
                if distance <= miles:
                    i['distance'] = distance
                    final_list.append(i)

    return final_list
