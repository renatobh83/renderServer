import re, gzip, requests, json
from io import BytesIO
from datetime import datetime, timedelta
from flask import (
    Flask,
    request,
    redirect,
    make_response,
    Response,
)
from flask_cors import CORS

from modules.parse import list_file
from modules.controller import valid_login, action_redirect
from modules.MongoClient import mongoClient
from modules.utils import (
    login,
    change,
    get_redirect_live,
    get_redirect_vod_series,
)

app = Flask(__name__)

CORS(app)


@app.before_request
def init():
    print("Fi")


@app.errorhandler(404)
def page_not_found(e):
    return {"message": str(e)}, 404


@app.route("/")
def index_route():
    return {"message": "Server up"}, 200


def compress_and_stream(data):
    # Converte a lista de dicionários em uma string JSON
    json_d = json.dumps(data)

    # Converte a string JSON em bytes
    json_bytes = json_d.encode("utf-8")

    # Cria um buffer de bytes em memória
    buf = BytesIO()

    # Compacta os bytes usando gzip
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(json_bytes)

    # Move o ponteiro de volta para o início do buffer
    buf.seek(0)

    # Stream dos dados em chunks
    while chunk := buf.read(8192):
        yield chunk


@app.route("/player_api.php", methods=["GET"])
async def player_route():

    username = request.args.get("username", None)
    password = request.args.get("password", None)

    request_arguments = request.args.copy()

    user, file = valid_login(username, password)

    if not user:
        return {"user_info": {"auth": 0}}, 401

    mongo_client = mongoClient()
    col_users = mongo_client["iptv"]["users"]
    col_users.update_one(
        {"username": username, "password": password},
        {"$set": {"last_activity": datetime.now() - timedelta(hours=3)}},
    )
    mongo_client.close()

    if "action" in request_arguments:
        data = action_redirect(request_arguments, user, file)
        return Response(
            compress_and_stream(data),
            content_type="application/json",
            headers={"Content-Encoding": "gzip"},
        )
    return login(username, password, request.host), 200


@app.get("/<username>/<password>/<file_path>")
# A crutch for the work of an incomplete link to a list with video containers
def live_container(username, password, file_path):
    user, file = valid_login(username, password)

    if not user and not file:
        return {"user_info": {"auth": 0}}, 401

    link = getLink(file, file_path)
    if link.endswith("m3u8"):
        link = change(link, "ts")
    return redirect(get_redirect_live(link))


def getLink(file, stream):
    lista = list_file(file)
    link = next(
        (
            link
            for link in lista
            if re.search(rf"/{stream}(\.ts|\.m3u8)?$|^/{stream}$", link)
        ),
        None,
    )
    return link


@app.get("/live/<username>/<password>/<stream_id>.<ext>")
def live(username, password, stream_id, ext):
    try:
        user, file = valid_login(username, password)

        if not user and not file:
            return {"user_info": {"auth": 0}}, 401

        link = getLink(file, stream_id)
        if bool(link):
            if ext == "m3u8":
                if link.endswith(ext):
                    return redirect(get_redirect_live(link), 307)
                else:
                    link = get_redirect_live(change(link, ext))
                    return redirect(link, 307)
            elif ext == "ts":
                if link.endswith("m3u8"):
                    link = get_redirect_live(change(link, ext))
                    return redirect(link, 307)
                return redirect(get_redirect_live(link), 307)
            return {"message": []}
        return {"message": "Streaming not found"}, 404
    except Exception as e:
        return {"message": str(e)}, 500


@app.route("/xmltv.php", methods=["GET"])
def xmltv():
    try:
        username = request.args.get("username", None)
        password = request.args.get("password", None)

        user, _ = valid_login(username, password)
        if not user:
            return {"user_info": {"auth": 0}}, 401

        try:
            if user["serieVod"]:
                r = requests.get(
                    user["serieVod"].replace("player_api", "xmltv"), stream=True
                ).text
                content = gzip.compress(r.encode("utf-8"), 5)
                response = make_response(content)
                response.headers["Content-length"] = str(len(content))
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Type"] = "application/octet-stream"
                response.headers["Content-Disposition"] = (
                    'attachment; filename="epg.xml"'
                )
                return response
            return {}
        except Exception as e:
            return str(e), 500
    except:
        return {"Error"}, 500


@app.route("/movie/<username>/<password>/<stream_file>", methods=["GET"])
def movie_stream(username, password, stream_file):
    try:
        user, _ = valid_login(username, password)

        if not user:
            return {"user_info": {"auth": 0}}, 401

        if user["linkMovies"]:
            url = f'{user["linkMovies"]}{stream_file}'
            if url.endswith(".mkv"):
                url = url.replace(".mkv", ".mp4")
            link = get_redirect_vod_series(url)
            return redirect(link, code=307)
    except:
        return {}, 500


@app.route("/series/<username>/<password>/<stream_file>", methods=["GET"])
def series_stream(username, password, stream_file):
    try:
        user, file = valid_login(username, password)

        if not user and not file:
            return {"user_info": {"auth": 0}}, 401

        if user["linkSeries"]:
            url = f'{user["linkSeries"]}{stream_file}'
            if url.endswith(".mkv"):
                url = url.replace(".mkv", ".mp4")
            link = get_redirect_vod_series(url)

            return redirect(link, code=307)
            return {}
    except:
        return {}, 500


if __name__ == "__main__":
    app.run(debug=False)
