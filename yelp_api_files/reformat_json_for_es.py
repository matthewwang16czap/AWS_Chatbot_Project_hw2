import json

if __name__ == '__main__':
    es_index = 'restaurants'
    es_type = 'Restaurant'
    f = open('yelp_restaurants.json')
    data = json.load(f)
    restaurants = data['businesses']
    f2 = open("yelp_restaurants_es.json", "w")
    for restaurant in restaurants:
        f2.write('{"index":{"_index":\"' + es_index + '\","_id":\"' + restaurant['insertedAtTimestamp'] + '\"}}\n')
        restaurant.pop('insertedAtTimestamp')
        mod_restaurant = {'type':es_type}
        mod_restaurant.update(restaurant)
        f2.write(json.dumps(mod_restaurant) + '\n')
    f2.close()
    f.close()