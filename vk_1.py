import requests
import tqdm
import json

class VK_Photos:
    API_BASE_URL = 'https://api.vk.com/method'
    
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        
    def get_common_params(self):
        return {
            'access_token': self.token,
            'v': '5.131'
        }
        
    def get_photos(self, photo_count=5):
        params = self.get_common_params()
        params.update({
            'owner_id': self.user_id, 
            'album_id': 'profile', 
            'extended': '1',
            'count': photo_count
            })
        
        try:
            response = requests.get(f'{self.API_BASE_URL}/photos.get', params=params, timeout=10)
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            print("Время ожидания запроса истекло. Повторите попытку позже.")
        except requests.exceptions.ConnectionError:
            print("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
        except requests.exceptions.HTTPError as err:
                print(f"HTTP error {err}")
                
        
        photos = []
        try:
            data = response.json()
                
        except json.JSONDecodeError:
            print("Не удалось проанализировать ответ JSON.")
            return []
            
        if 'response' in data and 'items' in data['response']:
            for item in data['response']['items']:
                max_size = max(item['sizes'], key=lambda size: size['height'] * size['width'])
                filename = f"{item['likes']['count']}.jpg"
                photos.append({'url': max_size, 'filename': filename})
                
        return photos
    
    
class Yandex_disk:
    def __init__(self, token):
        self.headers = {'Authorization': f'OAuth {token}'}
        self.url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        
    def create_folder(self, folder_name):
        try:
            response = requests.put(self.url_create_folder,
                                headers=self.headers,
                                params={'path': folder_name}, 
                                timeout=10)
            
            response.raise_for_status()
        
        except requests.exceptions.Timeout:
            print("Время ожидания запроса истекло. Повторите попытку позже.")
        except requests.exceptions.ConnectionError:
            print("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
        except requests.exceptions.HTTPError as err:
                print(f"HTTP error {err}")
        
        if response.status_code == 201:
            print(f'Папка {folder_name} создана')
        elif response.status_code == 409:
            print(f'Папка с таким названием {folder_name} уже существует')
        else:
            print(f'Error: {response.status_code}')
        
        return True
    
    def upload_photos_to_Yandex_disk(self, folder_name, photos):
        self.create_folder(folder_name)
        uploaded_photos_info = []
        
        for photo in tqdm.tqdm(photos, desc="Загружаются фотографии"):
            params = {
                'path': f"/{folder_name}/{photo['filename']}",
                'overwrite': 'true'
                }
            try:
                response = requests.get(self.upload_url,
                                    params=params,
                                    headers=self.headers,
                                    timeout=10)
                
                response.raise_for_status()
            
            except requests.exceptions.Timeout:
                print("Время ожидания запроса истекло. Повторите попытку позже.")
                continue
            except requests.exceptions.ConnectionError:
                print("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
                continue
            except requests.exceptions.HTTPError as err:
                    print(f"HTTP error {err}")
                    continue
            
            try:
                upload_href = response.json().get('href')  
                
            except json.JSONDecodeError:
                print("Не удалось проанализировать ответ JSON.")
                continue 
            except KeyError:
                print("Ожидаемый ключ «href» в ответе не найден.")
                continue
                    
            if upload_href:
                try:
                    photo_response = requests.get(photo['url'])
                    photo_response.raise_for_status()
                    if photo_response.status_code == 200:
                        upload_response = requests.put(upload_href, files={'file': photo_response.content})
                        upload_response.raise_for_status()
                            
                except requests.exceptions.Timeout:
                    print("Время ожидания запроса истекло. Повторите попытку позже.")
                except requests.exceptions.ConnectionError:
                    print("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
                except requests.exceptions.HTTPError as err:
                    print(f"HTTP error {err}")
                        
                if upload_response.status_code == 201:
                    print(f"Файл {photo['filename']} загружен в папку {folder_name} на Яндекс.Диск")
                    uploaded_photos_info.append({
                        'file_name': photo['filename'],
                        'size': photo['size']})
                else:
                    print(f"Ошибка при загрузке файла: {upload_response.status_code}")
            else:
                print(f"Ошибка получения ссылки для загрузки: {response.status_code}")
                
        return uploaded_photos_info

    
vk_token = input("Введите VK токен: ")
yadex_token = input("Введите яндекс токен: ")
vk_user_id = input("ID пользователя VK: ")

vk_photos = VK_Photos(vk_token, vk_user_id)
yandex_disk = Yandex_disk(yadex_token)

photos = vk_photos.get_photos()
uploaded_photos_info = yandex_disk.upload_photos_to_Yandex_disk('Images', photos)
    
with open('uploaded_photos_info.json', 'w') as json_file:
    json.dump(uploaded_photos_info, json_file, indent=4)
        
        
