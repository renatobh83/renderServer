import os, re
from functools import wraps
import base64
from datetime import datetime
import requests
from time import time

import subprocess


def github_read_file(file_path):
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f'Bearer {os.environ.get("GIT_TOKEN")}',
        "Accept": "application/vnd.github+jso",
    }

    url = f"https://api.github.com/repos/renatobh83/listas/contents/{file_path}"

    r = requests.get(url, headers=headers)
    data = r.json()
    file_content = data["content"]
    file_content_encoding = data.get("encoding")
    if file_content_encoding == "base64":
        file_content = base64.b64decode(file_content).decode()

    return file_content


def encontrar_link_extm(lista, valor_procurado):
    
    links = [link["link"] for link in lista]
    pattern = rf"http://[^/]+(/live)?/\d+/[a-zA-Z0-9]+/{valor_procurado}+(\.m3u8|\.ts)?"

    for link in links:
        match = re.search(pattern, link)
        if match:
            return link
    return None


def transformar_link(link_original, action):
    
    # Definir o padrão de regex com 4 grupos
    padrao_regex = r"(http://[^/]+)/([^/]+)/([^/]+)/([^/]+)"
    # Procurar por correspondências no link original
    link_original = (
        link_original.replace("/live", "").replace(".m3u8", "").replace(".ts", "")
    )
    correspondencia = re.match(padrao_regex, link_original)

    if correspondencia:
        # Extrair os grupos encontrados
        host = correspondencia.group(1)
        username = correspondencia.group(2)
        password = correspondencia.group(3)
        stream_id = correspondencia.group(4)
        # Construir o novo link com os valores extraídos
        link_transformado = f"{host}/player_api.php?username={username}&password={password}&action={action}&stream_id={stream_id}"
        return link_transformado
    else:
        return None


def login(username, password, url):
    data_atual = datetime.now()
    data_obj = data_atual.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_now = int(data_atual.timestamp())
    return {
        "server_info": {
            "xui": True,
            "version": "1.5.5",
            "revision": 2,
            "url": f"{url}",
            "port": "80",
            "https_port": "443",
            "status": "Active",
            "rtmp_port": "8880",
            "server_protocol": "https",
            "timezone": "America/Sao_Paulo",
            "timestamp_now": timestamp_now,
            "time_now": data_obj,
        },
        "user_info": {
            "username": f"{username}",
            "password": f"{password}",
            "message": "Ola seja bem vindo!!!",
            "auth": 1,
            "status": "Active",
            "exp_date": "1718852399",
            "is_trial": "0",
            "active_cons": "1",
            "created_at": "1622142527",
            "max_connections": "100",
            "allowed_output_formats": ["m3u8", "ts", "rtmp"],
        },
    }

def get_redirect_chain(url):
    curl_command = ["curl", "-s", "-i", url]
    result = subprocess.run(curl_command, capture_output=True, text=True)
    if result.returncode == 0:
        headers = result.stdout
        # Use expressões regulares para encontrar o valor do cabeçalho Location
        match = re.search(r"location: (.+)", headers, re.IGNORECASE)
        if match:
            location_value = match.group(1).strip()
            return location_value
        return url


# Decorador de cache com timeout
def cache_with_timeout(timeout):
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            current_time = time()

            # Verifica se o cache está expirado ou não existe
            if key in cache:
                cached_result, timestamp = cache[key]
                if current_time - timestamp < timeout:
                    return cached_result

            # Executa a função e armazena o resultado no cache
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)

            return result

        return wrapper

    return decorator


class ChangeLink:
    def __init__(self, url, ext):
        self.url = url
        self.ext = ext

    def _toTs(self):
        pattern = re.compile(r"(https?://[^/]+/[^/]+/)(.+)(\.m3u8)$")
        match_1 = re.search(pattern, self.url)
        grup1 = match_1.group(1).replace("/live", "")
        return re.sub(pattern, grup1 + r"\2", self.url)

    def _toM3u8(self):
        pattern = re.compile(r"(https?://[^/]+)(.+)")
        self.url = self.url.replace(".ts", "")
        return re.sub(pattern, r"\1" + "/live" + r"\2" + ".m3u8", self.url)

    def change(self):
        if self.ext == "ts":
            return self._toTs()

        return self._toM3u8()


def change(url, ext):
    return ChangeLink(url, ext).change()

