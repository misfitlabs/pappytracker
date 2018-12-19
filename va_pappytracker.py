import json
import os
import smtplib
import time
from email.mime.text import MIMEText

import requests
import resources.credentials as cred
from resources import constants as const
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

productString = None
filepath = os.path.dirname(os.path.abspath(__file__))
filename = filepath + "/data_dumps/" + str(time.strftime('%b%d-%Y-%H%M%S')) + '.txt'

for product_name, product_id in const.products.iteritems():
    if productString is None:
        productString = product_id
    else:
        productString = productString + "," + product_id

f = open(filename, 'a+')
with open(filepath + '/resources/local_stores.json') as file:
    data = json.load(file)
    for store in data:
        try:
            headers = {'Accept': 'application/json'}
            r = requests.get("https://www.abc.virginia.gov/webapi/inventory/mystore?storeNumbers=" +
                             str(store["StoreId"]) + "&productCodes=" + productString, timeout=10, verify=False, headers=headers)
            print "REQUEST_URL: " + r.url
            resp = r.json()
        except (IOError, ValueError) as err:
            print err
            print 'Store ' + str(store["StoreId"]) + " timed out for products " + productString
            continue

        if r.status_code == requests.codes.ok:
            products = resp["products"]
            for bottle in products:
                if bottle["storeInfo"]["quantity"] > 0:
                    f.write("Store " + str(store["StoreId"]) + ":\n")
                    f.write("\tAddress: " + store["Address"]["Address1"] + ", " + store["Address"]["City"] + store["Address"]["Zipcode"] + "\n")
                    f.write("\tPhone: " + store["PhoneNumber"]["FormattedPhoneNumber"] + "\n")
                    break

            for bottle in products:
                product_id = bottle["productId"]
                bottle_name = next(key for key, value in const.products.items() if value == product_id)

                if bottle["storeInfo"]["quantity"] > 0:
                    f.write("\t" + str(bottle["storeInfo"]["quantity"]) + " bottle(s) of " + bottle_name + "\n")
        else:
            f.write("Inventory request on store #" + str(resp["products"][0]["storeInfo"]["storeId"]) + " failed.")
            f.write("\n")
            continue
f.close()

if os.stat(filename).st_size > 0:
    fp = open(filename, 'rb')
    msg = MIMEText(fp.read())
    fp.close()

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(cred.email_addr, cred.email_pwd)

    msg['Subject'] = 'Virginia Rare Bourbons: ' + str(time.strftime('%b%d-%Y-%H%M%S'))
    msg['To'] = 'Bourbon Ninjas'

    server.sendmail(cred.email_addr, cred.recipients, msg.as_string())
