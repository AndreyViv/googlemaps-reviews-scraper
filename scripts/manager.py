# -*- coding: utf8 -*-
import time
import csv

# CSV file columns names
COLUMNS = ['user name', 'user link', 'company name', 'company address', 'reviewed stars']

# File paths
URLS_FILE_PATH = 'data/'
RESULT_FILE_PATH = 'data/results/'


class DataManager:
    def __init__(self):
        self.urls_file = f'{URLS_FILE_PATH}urls.txt'
        self.result_file = f'{RESULT_FILE_PATH}DataSet_{time.strftime("%Y%m%d%H%M%S", time.localtime())}.csv'

        with open(self.result_file, 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(COLUMNS)

    def get_urls(self) -> list:
        with open(self.urls_file, 'r') as file:
            urls_list = file.readlines()
        return urls_list

    def write_data(self, data: list):
        with open(self.result_file, 'a', newline='', encoding='utf8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(data)

