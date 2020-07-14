import json
import pymongo
import re
import requests
import urllib3

from bs4 import BeautifulSoup
from datetime import datetime
from html.parser import HTMLParser
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def connection():
    client=MongoClient("mongodb://localhost:27017/")
    db=client["superseis"]
    return db

def super6():
    try:
        soup=BeautifulSoup(
            requests.get("http://www.superseis.com.py/Ofertas.aspx", timeout=10,
            headers={'user-agent': 'Mozilla/5.0'}, verify=False).text, "html.parser")     
        tags = soup.find("div",{'class': "product-pager"})
        for a in tags.findAll('a'):
            if a.text=="Último":
                pageindex=a.get("href")[a.get("href").index("=")+1:]

        return pageindex
        
    except requests.ConnectionError:
        print("error al conectar")
    except Exception as e:
        print(e)

def getAllProducts():
    pageindex=super6()
    body=[]
    for i in range(int(pageindex)):
        index=i+1
        link="http://www.superseis.com.py/ofertas.aspx?pageindex="+str(index)
        print(link)
        soup=BeautifulSoup(
                requests.get(link, timeout=10,
                headers={'user-agent': 'Mozilla/5.0'}, verify=False).text, "html.parser")
        body+=(soup.findAll("div",{"class":"producto"}))


    return body

def getProducts():
    products=getAllProducts()
    body=[]
    db=connection()
    for product in products:
        name = product.find("a", {"class":"product-title-link"})
        price = product.find("span", {"class":"price-label"})
        

        body.append({
            "productName": name.text,
            "productPrice": price.text.replace('.',''),
        })

    try:
        for i in body:
            product = db.produtos.find({'productName':i['productName']})
            if product.count()!=0:
                if i['productPrice'] != product['productPrice']:
                    db.history.insert_one(product)
                    db.products.update(product, {'$set': {'productPrice': i['productPrice']}})
            else:
                db.products.insert_one(i)
    except pymongo.errors.DuplicateKeyError:
            pass
 
#getProducts()