import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient

MONGO_URL = os.environ['MONGO_URL']
MONGO_USERNAME = os.environ['MONGO_USERNAME']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
# client = MongoClient(MONGO_URL, 27017, username=MONGO_USERNAME, password=MONGO_PASSWORD)
client = MongoClient(MONGO_URL, 27017)
db = client.todaylaw

bp = Blueprint('ranking', __name__, url_prefix='/')

@bp.route('/api/rank', methods=["GET"])
def get_ranking():
    rank_list = db.ranking.find({}).sort([('count',-1), ('title',1)]).limit(5)
    rank_result = []

    for idx, rank in enumerate(rank_list):
        title = title_row_check(rank['title'])
        doc = {
            'id':rank['id'],
            'rank':idx+1,
            'url':rank['url'],
            'title':title,
            'proposer_name': rank['proposer_name'],
            'proposer_names': rank['proposer_names'],
            'date':rank['date'],
            'count':rank['count'],
            'like':rank['like'],
            'hate':rank['hate']
        }

        rank_result.append(doc)
    return jsonify(rank_result)

@bp.route('/api/rank', methods=['POST'])
def increase_click_count():
    # 법안ID, 법안제목
    id = request.form['id']
    url = request.form['url']
    title = request.form['title']
    proposer_name = request.form['proposer_name']
    proposer_names = request.form['proposer_names']
    date = request.form['date']

    ranking = db.ranking.find_one({'id':id}, {'_id':0, 'title':0, 'id':0})
    if ranking is not None:
        count = ranking['count']
        new_count = count+1
        db.ranking.update_one({'id':id}, {'$set':{'count':new_count}})
    else:
        doc = {
            'id':id,
            'url':url,
            'title':title,
            'proposer_name': proposer_name,
            'proposer_names': proposer_names,
            'date':date,
            'count':1,
            'like': 0,
            'hate': 0
        }
        db.ranking.insert_one(doc)

    return jsonify({'result':'success'})


def title_row_check(title):
    title_max_length = 22
    if len(title) >= title_max_length:
        title = title[:title_max_length]
        title = title + " ..."
    return title


