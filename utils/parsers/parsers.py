import urllib
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
import requests


class XMLParser:
    """
    XML Parser. SOURCE: https://jobs.sapbazar.com/rss/all/
    """
    def __init__(self):
        self.url = 'https://jobs.sapbazar.com/rss/all/'
        self.response = urllib.request.urlopen(self.url)
        self.data = self.response.read()
        self.text = self.data.decode('utf-8')
        self.soup = BeautifulSoup(self.text, 'lxml')

    def get_urls(self) -> list:
        return [url['rdf:resource'] for url in self.soup.find_all('rdf:li')]

    @staticmethod
    def extract_id(link):
        return link.split('/')[-1]

    def get_ids(self):
        return [self.extract_id(url) for url in self.get_urls()]


class JSONContextManager:
    """JSON Context Manager operates on json file"""

    def __init__(self, file):
        self.file = file

    def write_json(self, data):
        with open(self.file, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def get_new_ads(self):
        xml = XMLParser()
        return [url for url in xml.get_urls() if url not in self.json_old_ads()]

    def json_new_ads(self):
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            return data['new']

    def json_old_ads(self) -> list:
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            return data['urls']

    def update_json(self):
        xml_parser = XMLParser()
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            data['new'] = self.get_new_ads()
            data['urls'] = xml_parser.get_urls()
            self.write_json(data)


class HTMLParser:

    def __init__(self, url):
        self.url = url
        self.source = requests.get(self.url).text
        self.soup = BeautifulSoup(self.source, 'html.parser')
        self.category_tag = self.soup.find('h2').text

    def category(self):
        return self.category_tag.split('>')[1].strip()

    def location(self):
        return self.soup.find_all('ul', class_='control-panel')[1].li.text.strip()

    def job_title(self):
        return self.soup.find('h2', class_='jobd-title').text