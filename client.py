import requests
import argparse
import os

# URL сервера
SERVER_URL = 'http://127.0.0.1:5000'

# Функция для загрузки файла на сервер с использованием потоковой передачи
def upload_file(file_path):
    file_size = os.path.getsize(file_path)  # Получаем размер файла
    headers = {'File-Name': os.path.basename(file_path), 'File-Size': str(file_size)}  # Устанавливаем заголовки с именем и размером файла

    print("Заголовки запроса:", headers)  # Проверяем заголовки перед отправкой

    with open(file_path, 'rb') as f:
        response = requests.post(f"{SERVER_URL}/upload", data=f, headers=headers, stream=True)
        print(response.json())  # Печатаем ответ сервера

# Функция для скачивания файла с сервера
def download_file(filename):
    response = requests.get(f"{SERVER_URL}/download/{filename}", stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):  # Скачиваем файл по частям
                if chunk:
                    f.write(chunk)
        print(f"File {filename} downloaded successfully.")
    else:
        print(response.json())

# Функция для получения списка файлов на сервере
def list_files():
    response = requests.get(f"{SERVER_URL}/files")
    if response.status_code == 200:
        files = response.json().get("files", [])
        if files:
            print("Files on server:")
            for idx, file in enumerate(files, 1):
                print(f"{idx}. {file}")
        else:
            print("No files found on the server.")
    else:
        print("Failed to retrieve file list.")

if __name__ == '__main__':
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description='Client for uploading, downloading, and listing files.')
    parser.add_argument('command', choices=['upload', 'download', 'list'], help='Command to execute: upload, download, or list.')
    parser.add_argument('file', nargs='?', help='File path for upload or filename for download.')

    args = parser.parse_args()

    if args.command == 'upload':
        if args.file:
            upload_file(args.file)
        else:
            print("Please provide the file path to upload.")
    elif args.command == 'download':
        if args.file:
            download_file(args.file)
        else:
            print("Please provide the filename to download.")
    elif args.command == 'list':
        list_files()
