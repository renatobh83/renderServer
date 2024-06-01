import re


class ExtinfParser:
    def __init__(self, file):
        self.id_mapping = {}
        self.channels_data = []
        self.file = file

    def parse_extinf_to_json(self, extinf_str):
        # Regex para extrair as informações relevantes da string #EXTINF
        # EXTINF:-1 tvg-id="" tvg-name="CAZE 1 4K" tvg-logo="" group-title="ESPORTES ONLINE",CAZE 1 4K
        pattern = r'#EXTINF:-1\s{0,2}tvg-id="([^"]*)"\s{0,2}tvg-name="([^"]*)"\s{0,2}tvg-logo="([^"]*)"\s{0,2}group-title="([^"]*)",(.*?$)'
        match = re.match(pattern, extinf_str)

        if match:
            # Extrair os grupos correspondentes aos dados
            tvg_id, tvg_name, tvg_logo, group_title, name = match.groups()
            # Gerar o ID para o tvg-id
            category_id = self.id_mapping.get(group_title)

            if category_id is None:
                category_id = len(self.id_mapping) + 1
                self.id_mapping[group_title] = category_id
            # Criar um dicionário com os dados extraídos
            data = {
                "tvg-id": tvg_id,
                "category_id": category_id,
                "tvg-name": tvg_name,
                "tvg-logo": tvg_logo,
                "category_name": group_title,
                "parent_id": 0,
                "name": name,
            }

            # Retornar o dicionário

            return data
        else:
            return None

    def process_file_content(self):
        # Separar as linhas do arquivo
        lines = self.file.strip().split("\n")

        # Processar cada linha e converter em um dicionário
        for i in range(
            0, len(lines), 2
        ):  # Iterar de 2 em 2 para pegar cada linha #EXTINF e seu link subsequente
            extinf_data = self.parse_extinf_to_json(lines[i])
            if extinf_data:
                extinf_data["link"] = lines[i + 1]  # Adicionar o link ao dicionário
                self.channels_data.append(extinf_data)

        return self.channels_data

    def to_list(self):
        return [item["link"].strip() for item in self.file]

    def get_live_categories(self):
        tvg_id_counts = {}
        for item in self.file:
            tvg_id = item["category_id"]
            category_name = item["category_name"]
            parent_id = item["parent_id"]
            if tvg_id not in tvg_id_counts:
                tvg_id_counts[tvg_id] = {
                    "category_id": tvg_id,
                    "category_name": category_name,
                    "parent_id": parent_id,
                }
                # Converter o resultado em uma lista de dicionários
        result_list = list(tvg_id_counts.values())
        return result_list

    def get_live_streams(self, categoria=None):
        live_streams = []
        count = 1
        for item in self.file:
            try:
                data = {
                    "num": count,
                    "name": item["tvg-name"],
                    "stream_type": "live",
                    "stream_id": re.search(r"/(\d+)(\.[a-zA-Z0-9]+)?$", item["link"]).group(1),
                    "stream_icon": item["tvg-logo"],
                    "epg_channel_id": item["tvg-id"],
                    "added": "1704409062",
                    "category_id": item["category_id"],
                    "custom_sid": "",
                    "tv_archive": 0,
                    "direct_source": "",
                    "tv_archive_duration": 0,
                    "ext": "ts",
                }
            except Exception as e:
                print(e)
            live_streams.append(data)
            count += 1
        if categoria:
            live_filter = [
                live for live in live_streams if live["category_id"] == int(categoria)
            ]
            return live_filter
    
        return live_streams


def file_content(file):
    return ExtinfParser(file).process_file_content()


def get_categories(file):
    # return encode_list(ExtinfParser(file).get_live_categories())
    return ExtinfParser(file).get_live_categories()


def get_streams(file, categoria=None):
    return ExtinfParser(file).get_live_streams(categoria)
    # return encode_list(ExtinfParser(file).get_live_streams(categoria))


def list_file(file):

    return ExtinfParser(file).to_list()

