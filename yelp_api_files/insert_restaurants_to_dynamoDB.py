import json
import boto3
from decimal import Decimal

if __name__ == '__main__':
    f = open('yelp_restaurants.json')
    event = json.load(f)
    client = boto3.resource('dynamodb')
    table = client.Table("yelp-restaurants")
    restaurants = event['businesses']
    for restaurant in restaurants:
        restaurant = json.loads(json.dumps(restaurant), parse_float=Decimal)
        response = table.put_item(Item = restaurant)

