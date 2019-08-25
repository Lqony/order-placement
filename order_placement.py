import requests
import json
import sys
import ast
from pprint import pprint
import time
import random

auth_keys = ["",""]
api = "https://tradeogre.com/api/v1/"

def stringify(d):
    return "%.8f" % d


class api_requests:
    buy="order/buy"
    sell = "order/sell"
    cancel = "order/cancel"
    get_order="account/order/"
    market="ticker/FROM-TO"

def do_request(request, dPostData=None, CheckKey=None):
    time.sleep(2)
    print(api+request)
    print(json.dumps(dPostData))
    try:
        r = None
        if dPostData is None:
            r = requests.get(api+request, auth=(auth_keys[0], auth_keys[1]))
        else:
            r = requests.post(api+request, data=dPostData, auth=(auth_keys[0], auth_keys[1]))

        if r.status_code != 200:
            return None

        r = json.loads(r.text)
        if CheckKey != None and CheckKey not in r:
            return None
        return r
    except:
        return None

class Market:
    data=None

    def __init__(self):
        self.data=None

    def get(self):
        data = do_request(api_requests.market, CheckKey='success')
        if data == None:
            return False
        self.data = data
        return True

class Order:
    submit_data=None
    state_data=None
    sell=None
    amount=None
    price=None
    time=0

    def __init__(self, sell=True, amount=0.1, price=0.1):
        self.submit_data=None
        self.state_data = None
        self.sell = sell
        self.amount = amount
        self.price = price
        self.time=0

    def get_state(self, refresh=False):
        if self.submit_data == None:
            print('Order not placed')
            return False

        if self.state_data == None or refresh == True:
            res = do_request(api_requests.get_order+self.submit_data['uuid'], CheckKey='success')
        print(res)
        if res == None:
            return False

        self.state_data = res
        return True

    def place(self):
        res = None
        if self.submit_data != None:
            print('Order already placed, cant use twice')
            return False

        if self.sell:
            res = do_request(api_requests.sell, {'market': 'FROM-TO', 'quantity': stringify(self.amount), 'price': stringify(self.price)}, CheckKey='success')
        print(res)
        if res == None or res['success'] == False:
            return False

        self.submit_data = res
        return  True

    def cancel(self):
        if self.submit_data == None:
            print('Order not placed, cant cancel')
            return 0
        if self.get_state(refresh=True) == False:
            return 0

        self.amount = self.amount - float(self.state_data['fulfilled'])
        res = do_request(api_requests.cancel, {'uuid' : self.submit_data['uuid']})

        if res == None or res['success'] == False:
            return 0

        return self.amount


#MAIN
if len(sys.argv) < 2:
    print('Specyfi amount')
    exit(0)

if len(sys.argv) >= 4:
    auth_keys = [str(sys.argv[2]), sys.argv[3]]

amount = float(sys.argv[1])
amount_per_order = amount/12.0
orders = []

try:
    market = Market()
    while True:
        attempts=0

        print('Retrieving market data')
        while True:
            if market.get() == False:
                attempts+=1
                if attempts == 5:
                    raise BaseException
            else:
                break

        price = ((float(market.data['high'])+float(market.data['low'])) / 2) - 0.00000010
        price_ask = float(market.data['ask'])
        if price_ask > price:
            price = price_ask

        if amount < amount_per_order:
            amount_per_order = amount

        print('New price:', stringify(price))
        print('Amount:', amount_per_order)


        print('Placing new orders')
        attempts=0

        while True:
            attempts+=1
            new_order = Order(sell=True, amount=amount_per_order, price=price)
            if new_order.place() == True:
                orders.append(new_order)
                amount -= new_order.amount
                break
            if attempts > 10:
                break
            time.sleep(60)

        print('Placed', len(orders),'orders, amount left', amount)

        if amount <= 0:
            exit(0)

        time.sleep(60*60)

except BaseException as e:
    print('Some exception occured, canceling orders and exiting')
    print(e)
    for order in orders:
        order.cancel()
exit(0)
