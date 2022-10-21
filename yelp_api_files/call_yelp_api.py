import json
import requests
import datetime

if __name__ == '__main__':
    MY_API_KEY = "JbUWqM_Gp8ucYm6C-yRiTRtZ_gPQRwZl6xbLUAzUk1l009FNXjV-u9ANqW6g0EitkAxse_EJdJ4M4svft2sFFb8OK8HrLHSqoxC_Rx1zJKAGX_Og-KklVgpiPm1PY3Yx"
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': f"Bearer {MY_API_KEY}"}
    categories = ['french', 'italian', 'asian', 'breakfast_brunch', 'mxican']
    json_file = {'businesses':[]}
    unique_id = 0

    for i, category in enumerate(categories):
        for offset in range(0, 20):
            params = {'term': 'restaurants', 'location': 'Manhattan', 'limit': 50, 'offset': offset, 'categories': category}
            resp = requests.get(url, headers=headers, params=params)
            resp_json = json.loads(resp.text)
            for restaurant in resp_json['businesses']:
                restaurant['cuisine'] = category
                restaurant.pop('url')
                restaurant.pop('image_url')
                restaurant.pop('is_closed')
                restaurant['insertedAtTimestamp'] = datetime.datetime.now().isoformat() + 'NO' + f"{unique_id:04}"
                unique_id += 1
            json_file['businesses'] += resp_json['businesses']

    '''
    # delete duplicate
    for i, restaurant in enumerate(json_file['businesses']):
        length = len(json_file['businesses'])
        j = i + 1
        while j < length:
            if restaurant['id'] == json_file['businesses'][j]['id']:
                json_file['businesses'].pop(j)
                length -= 1
            else:
                j += 1
    '''

    print(len(json_file['businesses']))
    with open("yelp_restaurants.json", "w") as outfile:
        json.dump(json_file, outfile)

