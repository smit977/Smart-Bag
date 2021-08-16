import math
import os

# from werkzeug import secure_filename
from flask import Flask, render_template, request, session, redirect, flash
import datetime
from flask_cors import CORS

# import mysql.connector
import json
import time
import requests
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from flask import jsonify

app = Flask(__name__)
CORS(app)

def manipulate(data):
    for i, col in enumerate(data.columns):
        data.iloc[:, i] = data.iloc[:, i].str.replace('"', '')
    # extracting data
    data["month"] = pd.DatetimeIndex(data["date"]).month

    # getting latest purchase data
    latest = data.loc[data.month == max(data.month)]

    latest["combine"] = latest["sub"] + latest["category"]

    all = data
    all["combine"] = data["sub"] + data["category"]

    lates_index = latest.index

    return [lates_index, all]


def recommedation(lates_index, all):
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(all["combine"])
    # creating a similarity score matrix
    similarity = cosine_similarity(count_matrix)

    l = []
    index = []
    if len(lates_index) < 5:
        for i in lates_index:
            lst = list(enumerate(similarity[i]))
            lst = sorted(lst, key=lambda x: x[1], reverse=True)

            lst = lst[1:8]  
            for i in range(len(lst)):
                a = lst[i][0]
                l.append(all["Product"][a])
                index.append(a)
    elif len(lates_index) < 20:
        for i in lates_index:
            lst = list(enumerate(similarity[i]))
            lst = sorted(lst, key=lambda x: x[1], reverse=True)

            lst = lst[1:4]  
            for i in range(len(lst)):
                a = lst[i][0]
                l.append(all["Product"][a])
                index.append(a)

    else:
        for i in lates_index:
            lst = list(enumerate(similarity[i]))

            lst = sorted(lst, key=lambda x: x[1], reverse=True)
            lst = lst[1:3]
            for i in range(len(lst)):
                a = lst[i][0]
                l.append(all["Product"][a])
                index.append(a)

    return [l, index]


@app.route("/smart_bag/<username>", methods=["GET"])
def home(username):
    # username=request.args.get('username')
    print("Fuck you", username)
    URL = f"https://smart-bag-rest-api.herokuapp.com/userdata/{username}"

    r = requests.get(url=URL)

    # extracting data in json format
    data = r.text

    new_data = data.split("\n")

    love = []

    for i in new_data:
        love.append(i.split('",'))

    love.pop()

    label = ["date", "Product_id", "Product", "Amount", "category", "sub"]

    myDict = {}
    for i in love:
        count = 0
        for j in i:
            myDict.setdefault(label[count], []).append(j)
            count += 1
    final = pd.DataFrame(myDict)

    latest_index, all = manipulate(final)
    # getting recommedation
    products, index = recommedation(latest_index, all)

    result = pd.DataFrame({"product": products, "index": index})
    result.index = index

    result.drop_duplicates(subset="index", inplace=True)


    final = pd.merge(result, all, how="left", left_index=True, right_index=True)
    product_ids = list(final.Product_id)
    product_name = list(final.Product)
    product_amount = list(final.Amount)
    re = []
    for i in range(len(product_ids)):
        val = {
            "pid": product_ids[i],
            "productName": product_name[i],
            "amount": product_amount[i],
        }
        re.append(val)



    return jsonify(re)


# app.run(debug=True)
