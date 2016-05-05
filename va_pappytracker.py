import json
import os
import smtplib
import time
from email.mime.text import MIMEText

import requests
import resources.credentials as cred
from resources import constants as const

filepath = os.path.dirname(os.path.abspath(__file__))
filename = filepath + "/data_dumps/" + str(time.strftime('%b%d-%Y-%H%M%S')) + '.txt'
f = open(filename, 'a+')
with open(filepath + '/resources/va_stores.json') as file:
    data = json.load(file)
    count = 0
    for store in data:

        for product_name, product_id in const.products.iteritems():
            try:
                r = requests.get("https://www.abc.virginia.gov/api/stores/inventory/" + str(store["StoreId"]) + "/" + product_id)
            except IOError as err:
                continue

            resp = r.json()
            if r.status_code == requests.codes.ok:
                if resp["products"][0]["storeInfo"]["quantity"] > 0:
                    f.write(str(count) + " of 352: Store " + str(resp["products"][0]["storeInfo"]["storeId"]) + " has " +
                            str(resp["products"][0]["storeInfo"]["quantity"]) + " bottle(s) of " + product_name + "\n")
                    f.write("Address: " + store["Address"]["Address1"] + ", " + store["Address"]["City"] + store["Address"]["Zipcode"] + "\n")
                    f.write("Phone: " + store["PhoneNumber"]["FormattedPhoneNumber"] + "\n")
                    f.write("\n")
            else:
                f.write("Inventory request on store #" + str(resp["products"][0]["storeInfo"]["storeId"]) + " failed.")
                f.write("\n")
                continue
        count += 1
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
