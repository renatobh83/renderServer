from modules.MongoClient import mongoClient
from modules.utils import (
    github_read_file,
    encontrar_link_extm,
    transformar_link,
    cache_with_timeout   
)
from modules.parse import file_content, get_categories, get_streams


# @cache_with_timeout(timeout=20)  # 5 minutos de timeout
@cache_with_timeout(timeout=300)  # 5 minutos de timeout
def valid_login(username="", password=""):
    if not all([username, password]):
        return None, None

    _user = username
    _pass = password
    mongo_client = mongoClient()

    col_users = mongo_client["iptv"]["users"]

    user = col_users.find_one(
        {"username": _user, "password": _pass}, {"_id": 0, "password": 0}
    )

    if not user:
        mongo_client.close()
        return None, None

    file_path = user["liveLink"]

    file_git = github_read_file(file_path) 
    
    file = file_content(file_git)
    
    mongo_client.close()
    return user, file


def get_response(url):
    import requests
    HEADERS_WEB  = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}

    
    response = requests.get(url, headers=HEADERS_WEB).json()
    
    return response


def action_redirect(request_arguments, user, file):

    try:
        if "get_live_streams" in request_arguments["action"]:
            if "category_id" in request_arguments:
                return get_streams(file, request_arguments["category_id"])
            return get_streams(file)
        elif "get_live_categories" in request_arguments["action"]:
            return get_categories(file)
        elif user["serieVod"]:
            if "category_id" in request_arguments:
                url = f'{user["serieVod"]}&action={request_arguments["action"]}&category_id={request_arguments["category_id"]}'
                return get_response(url)
            elif "series_id" in request_arguments:
                url = f'{user["serieVod"]}&action={request_arguments["action"]}&series_id={request_arguments["series_id"]}'
                return get_response(url)
            elif "vod_id" in request_arguments:
                url = f'{user["serieVod"]}&action={request_arguments["action"]}&vod_id={request_arguments["vod_id"]}'
                return get_response(url)
            elif "stream_id" in request_arguments:
                link_encontrado = encontrar_link_extm(
                    file, request_arguments["stream_id"]
                )
                if link_encontrado is None:
                    return {"epg_listings": []}
                link_transformado = transformar_link(
                    link_encontrado, request_arguments["action"]
                )
                url = link_transformado
                
                return get_response(url)
            else:
                url = f'{user["serieVod"]}&action={request_arguments["action"]}'

                return get_response(url)
        return {}, 200
    except Exception as e:
        return {"message": str(e)}, 500
