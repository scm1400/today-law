import os
from datetime import datetime, timedelta

import jwt
import requests
from flask import redirect, request, jsonify, Blueprint, make_response
from pymongo import MongoClient

TOKEN_KEY = os.environ['TOKEN_KEY']

MONGO_URL = os.environ['MONGO_URL']
MONGO_USERNAME = os.environ['MONGO_USERNAME']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
# 로컬 테스트를 위해 주석처리
client = MongoClient(MONGO_URL, 27017, username=MONGO_USERNAME, password=MONGO_PASSWORD)
#client = MongoClient(MONGO_URL, 27017)
db = client.todaylaw

bp = Blueprint("kakao_login", __name__, url_prefix='/')

kakao_client_key = os.environ['KAKAO_REST_API']
jwt_secret = os.environ['JWT_SECRET']
redirect_uri = "http://pythonapp-env.eba-pxmvppwj.ap-northeast-2.elasticbeanstalk.com/oauth/kakao/callback"
#redirect_uri = "http://localhost:5000/oauth/kakao/callback"


# 사용자가 카카오 로그인 요청시 카카오 로그인 페이지로 이동
# 사용자가 카카오에 인증 성공시 지정한 Redirect_URI로 Access_token을 요청할 수 있는 인증토큰(Authentication_code)를 응답받는다.
@bp.route('/oauth/kakao', methods=["GET"])
def redirect_kakao_login_page():
    kakao_redirect_url = f"https://kauth.kakao.com/oauth/authorize?client_id={kakao_client_key}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(kakao_redirect_url)


# 인증토큰을 응답받고 응답받은 인증토큰으로 Access_token을 요청한 후 응답받은 Access_token으로 사용자 정보를 요청
@bp.route('/oauth/kakao/callback')
def access():
    try:
        code = request.args.get('code')
        access_token_request_url = f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={kakao_client_key}&redirect_uri={redirect_uri}&code={code}"
        response_token = requests.get(access_token_request_url).json()
        token = response_token['access_token']

        user_info_request_url = "https://kapi.kakao.com/v2/user/me"
        user_info_response = requests.get(user_info_request_url, headers={"Authorization": f"Bearer {token}"})
        user_info = user_info_response.json()
        # DB에 user 정보를 넣어주고 jwt를 생성해서 쿠키에 넣어서 클라이언트에게 넘겨준다.
        kakao_account = user_info['kakao_account']

        id = str(user_info['id'])

        find_user = db.users.find_one({'user_id': id})

        if find_user == None:
            user_info_doc = {

                "user_id": id,
                "username": kakao_account['email'],
                "name": kakao_account['profile']['nickname'],
                "profile_image": kakao_account['profile']['profile_image_url'],
                "like_laws": [],
                "hate_laws": [],
                "bookmarks": [],
                "comments": [],
                "bio": "",
                "receive_mail": False,
                "recently_view": []

            }

            db.users.insert_one(user_info_doc)
    except:
        # return jsonify({"result":"fail"})
        return redirect('/')

    return login(id, kakao_account['profile']['nickname'])


def login(id, name):
    # JWT 토큰 구성
    payload = {
        "user_id": id,
        "name": name,
        "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 1)
        # "exp": datetime.utcnow() + timedelta(seconds=60) # 테스트용으로 10초만 유효한 토큰 생성
    }

    # JWT 토큰 생성
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')

    # 쿠키를 담은 response를 구성하기 위해 make_response 사용
    response = make_response(redirect('/'))
    # 쿠키에 토큰 세팅
    response.set_cookie(TOKEN_KEY, token)

    return response


# jwt 토큰 + 쿠키 테스트
@bp.route('/login-check')
def login_check():
    token = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        exp = payload['exp']
        user = db.users.find_one({'user_id': payload['user_id']}, {'_id': False})
        return jsonify({'result': 'success', 'name': user['name'], 'profile_image': user['profile_image'],
                        'email': user['username'], 'bio': user['bio'], 'receive_mail': user['receive_mail']})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/')
