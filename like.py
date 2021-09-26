from flask import Blueprint, request, jsonify
from pymongo import MongoClient

client = MongoClient('localhost',27017)
db = client.todaylaw

bp = Blueprint('like', __name__, url_prefix='/')

@bp.route('/api/like', methods=['GET'])
def get_like():
    like_list = list(db.ranking.find({}, {'_id': False}))
    print(like_list)
    return jsonify({'like_list':like_list})


@bp.route('/api/like', methods=['POST'])
def like_star():
    id_receive = request.form['id_give']
    print(id_receive)
    likes = db.ranking.find_one({'id':id_receive})
    current_like = likes['like']
    new_like = current_like + 1

    db.ranking.update_one({'id':id_receive}, {'$set': {'like': new_like}})
    return jsonify({'msg': '좋아요를 선택해주셨습니다.'})


@bp.route('/api/hate', methods=['POST'])
def delete_star():
    id_receive = request.form['id_give']
    likes = db.ranking.find_one({'id': id_receive})
    current_hate = likes['hate']
    new_hate = current_hate + 1

    db.ranking.update_one({'id': id_receive}, {'$set': {'hate': new_hate}})
    return jsonify({'msg': '싫어요를 선택해주셨습니다.'})