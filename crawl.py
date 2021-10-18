import os
import re

import jwt
from flask import jsonify, request, Blueprint
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

MONGO_URL = os.environ['MONGO_URL']
MONGO_USERNAME = os.environ['MONGO_USERNAME']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
client = MongoClient(MONGO_URL, 27017)
# client = MongoClient(MONGO_URL, 27017, username=MONGO_USERNAME, password=MONGO_PASSWORD)
TOKEN_KEY = os.environ['TOKEN_KEY']
JWT_SECRET = os.environ['JWT_SECRET']
db = client.todaylaw

bp = Blueprint('crawl', __name__, url_prefix='/')


@bp.route('/api/laws/details', methods=['POST'])
def saving():
    url_receive = request.form['url_give']
    id_receive = request.form['id_give']
    title = request.form['title_give']
    proposer_name = request.form['proposer_name_give']
    proposer_names = request.form['proposer_names_give']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (HTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')
    content = soup.select_one('#summaryContentDiv').text
    date = soup.select_one(
        'body > div > div.contentWrap > div.subContents > div > div.contIn > div.tableCol01 > table > tbody > tr > td:nth-child(2)').text

    ranking = db.ranking.find_one({'id': id_receive}, {'_id': False})
    if ranking is not None:
        count = ranking['count']
        new_count = count + 1
        db.ranking.update_one({'id': id_receive}, {'$set': {'count': new_count}})
    else:
        doc = {
            'id': id_receive,
            'url': url_receive,
            'title': title,
            'proposer_name': proposer_name,
            'proposer_names': proposer_names,
            'date': date,
            'count': 1,
            'like': 0,
            'hate': 0
        }
        db.ranking.insert_one(doc)

    # 좋아요, 싫어요 DB에서 찾아서 보내주기
    like = db.ranking.find_one({'id': id_receive}, {'_id': False})
    like_like = like['like']
    hate = db.ranking.find_one({'id': id_receive}, {'_id': False})
    hate_hate = hate['hate']

    recently_view(id_receive, title, url_receive, proposer_name, proposer_names, content)

    return jsonify({'content': content, 'title': title, 'date': date, 'proposer_name': proposer_name,
                    'proposer_names': proposer_names, 'id': id_receive, 'like': like_like, 'hate': hate_hate})


def clean_text(text):
    content = text.get_text()
    cleaned_text = re.sub('[a-zA-Z]', '', content)
    return cleaned_text


def recently_view(id, title, url, proposer_name, proposer_names, content):
    try:
        mytoken = request.cookies.get(TOKEN_KEY)
        user = verify_token(mytoken)
        user = db.users.find_one({'user_id': user['user_id']}, {'_id': False})

        recently_list = list(db.users.find(
            {'user_id': user['user_id']}, {'recently_view': True, '_id': False}
        ))
        print(recently_list[0]['recently_view'])
        while (len(recently_list[0]['recently_view']) > 5):
            del recently_list[0]['recently_view'][0]
            db.users.update(
                {'user_id': user['user_id']},
                {'$pop': {'recently_view': -1}}
            )
        temp = True

        for i in range(len(recently_list[0]['recently_view'])):
            if (recently_list[0]['recently_view'][i]['recently_view_id'] == id):
                temp = False
                print('break')
                break

        if temp == True:
            db.users.update(
                {'user_id': user['user_id']},
                {'$push': {
                    'recently_view': {'recently_view_id': id, 'title': title, 'url': url,
                                      'proposer_name': proposer_name,
                                      'proposer_names': proposer_names, 'content': content}}}, upsert=True
            )
        return
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return


def verify_token(mytoken):
    # 인코딩된 토큰의 payload 부분 디코딩
    token = jwt.decode(mytoken, JWT_SECRET, algorithms=['HS256'])
    # 디코딩된 payload의 user_id가 users DB에 있는지 확인
    user = db.users.find_one({'user_id': token['user_id']}, {'_id': False})

    return user
