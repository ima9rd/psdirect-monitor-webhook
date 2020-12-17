import requests
import json
import time
from datetime import datetime
import typing
import pytz


SETTINGS = {
    'webhook': '',
    'url': 'https://api.direct.playstation.com/commercewebservices/ps-direct-us/users/anonymous/products/productList/?fields=BASIC&productCodes=',
    'suffix': '&format=json',
    'UPCs': {'PS5 Digital': '3005817', 'PS5 Disc': '3005816'},
    'labels': {'outOfStock': ['Out of Stock', 13632027], 'inStock': ['In Stock', 8311585]},
    'tz': 'US/Central'
    }

def now(tz: str) -> datetime:
    return datetime.now(pytz.timezone(tz))

def send_webhook_message(webhook: str, embeds: list) -> None:
    requests.post(webhook, data=json.dumps({'embeds': embeds}), headers={'Content-Type': 'application/json'})

def generate_embed(stock_status: dict, settings: dict) -> dict:
    embeds = list()
    ts = now(settings['tz']).strftime('[%H:%M:%S %Z]')
    for item in stock_status:
        status = settings['labels'][stock_status[item]][0]
        embeds.append({
            'title': item,
            'description': f'{ts} {status}',
            'color': settings['labels'][stock_status[item]][1]
            })
    return embeds

def check_stock(settings, last_stock: typing.Optional[dict]=None, last_send: typing.Optional[datetime]=None) -> tuple:
    output = {}
    for UPC in settings['UPCs']:
        r = requests.get(settings['url'] + settings['UPCs'][UPC] + settings['suffix'])
        text = json.loads(r.text)
        status = text['products'][0]['stock']['stockLevelStatus']
        output[UPC] = status
    send = False
    if last_send:
        if (now(settings['tz']) - last_send).seconds > 60:
            send = True 
            last_send = now(settings['tz'])
    else:
        send = True
        last_send = now(settings['tz'])
    if last_stock and not send:
        if last_stock != output:
            send = True
    if send:
        send_webhook_message(settings['webhook'], generate_embed(output, settings))
    return output, last_send

last_send = None
last_stock = None

while True:
    last_stock, last_send = check_stock(SETTINGS, last_stock=last_stock, last_send=last_send)
    time.sleep(5)
