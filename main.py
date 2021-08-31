import requests
from datetime import datetime
import time
import os
from tqdm import tqdm

vk_token = os.getenv('TOKEN_VK', '')
yandex_token = os.getenv('TOKEN_YA', '')
ins_token = os.getenv('TOKEN_INST', '')


def check_the_answer(response, type):
    """Функция проверяет ответы request"""
    if type == 'vk':
        try:
            return response['response']['items']
        except KeyError:
            print('Ошибка получения данных из VK...')
            return False
    elif type == 'inst':
        try:
            result = response.json()
            return result['data']
        except ValueError:
            print('Ошибка получения данных из Instagram...')
            return False


class VkUser:

    def __init__(self, token_vk, version):
        self.API_VK_BASE_URL = 'https://api.vk.com/method/'
        self.params = {
            'access_token': token_vk,
            'v': version,
            '': 1,
        }

    def my_fotos(self, album_id, extended=0, count=5):
        """Метод получает список фото указанного альбома"""
        my_fotos_url = self.API_VK_BASE_URL + 'photos.get'
        my_fotos_params = {
            'album_id': album_id,
            'extended': extended,
            'count': count,
        }

        res = requests.get(my_fotos_url, params={**self.params, **my_fotos_params}).json()

        result = check_the_answer(res, 'vk')

        list_foto = []

        if not result:
            return list_foto

        for item_foto in result:
            list_temp_dict = {}
            list_temp_dict['name'] = item_foto['likes']['count']
            list_temp_dict['url'] = item_foto['sizes'][-1]['url']
            list_temp_dict['size'] = str(item_foto['sizes'][-1]['height'])+'x'+str(item_foto['sizes'][-1]['width'])

            if list_temp_dict in list_foto:
                list_temp_dict['name'] = str(item_foto['likes']['count']) + '_' \
                                         + str(datetime.fromtimestamp((item_foto['date'])).strftime('%Y-%m-%d'))

            list_foto.append(list_temp_dict)

        return list_foto


class InstUser:
    def __init__(self, token):
        self.token = token

    def my_foto_inst(self):

        list_foto = []

        my_foto_inst_params = {
            'fields': 'id, caption, media_url',
            'access_token': self.token
        }

        res = requests.get('https://graph.instagram.com/me/media', params=my_foto_inst_params)

        result = check_the_answer(res, 'inst')

        if not result:
            return list_foto

        for item_foto in result:
            list_temp_dict = {}
            list_temp_dict['name'] = item_foto['id']
            list_temp_dict['url'] = item_foto['media_url']

            list_foto.append(list_temp_dict)

        return list_foto


class YaUploader:

    def __init__(self, token: str, ):
        self.token = token
        self.API_YANDEX_BASE_URL = "https://cloud-api.yandex.net/"

    def upload(self, files_list_dir, dir_files=''):
        """Метод загружает файлы по списку file_list на яндекс диск"""
        self.dir_files = dir_files

        list_log_files = []

        headers = {
            'accept': 'application/json',
            'authorization': f'OAuth {self.token}'
        }

        list_error_files = ''

        for file_name_item in tqdm(files_list_dir):
            file_name = str(file_name_item['name']) + '.jpg'
            r = requests.post(self.API_YANDEX_BASE_URL + "v1/disk/resources/upload",
                              params={'path': 'Soc_Foto/'+self.dir_files+file_name, 'url': file_name_item['url']},
                              headers=headers)

            if r.status_code == 202:
                temp_dict_log_file = {}
                temp_dict_log_file['file_name'] = file_name
                if 'size' in file_name_item:
                    temp_dict_log_file['size'] = file_name_item['size']
                else:
                    temp_dict_log_file['size'] = 'размер не получен'

                list_log_files.append(temp_dict_log_file)

            elif r.status_code == 401:
                list_error_files += str(file_name+' ошибка загрузки...\n')

            time.sleep(1)

        with open('log_download.json', 'a', encoding='utf=8') as log_file:
            log_file.writelines(str(list_log_files))

        if list_error_files:
            print(list_error_files)


if __name__ == "__main__":
    my_vk = VkUser(vk_token, '5.131')

    ya_disk = YaUploader(yandex_token)

    list_vk_foto = my_vk.my_fotos('profile', 1)
    if list_vk_foto:
        ya_disk.upload(list_vk_foto, 'vk/')

    my_inst = InstUser(ins_token)
    list_inst_foto = my_inst.my_foto_inst()
    if list_inst_foto:
        ya_disk.upload(list_inst_foto, 'inst/')
