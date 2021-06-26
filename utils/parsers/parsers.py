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


class JsonManager:
    """JSON Manager operates on json file"""

    def __init__(self, file):
        self.file = file
        self.blog_parser = BlogParser()
        self.xml_parser = XMLParser()

    def write_json(self, data):
        with open(self.file, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def new_ads(self):
        try:
            urls = [url for url in self.xml_parser.get_urls() if url not in self.get_values('job_urls')]
            return urls
        except KeyError:
            self.write_json(data={"job_urls": []})

    def get_values(self, key: str):
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            return data.get(key) if data.get(key) else []

    def update_job_urls(self):
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            data['job_urls'] = self.xml_parser.get_urls()
            self.write_json(data)

    def new_blog_post(self, json_keys):
        return [post for post in self.blog_parser.blog_posts() if post not in self.get_values(json_keys)]

    def update_blog_urls(self, json_keys):
        with open(self.file, 'r') as json_file:
            data = json.load(json_file)
            data[json_keys] = self.blog_parser.blog_posts()
            self.write_json(data)


class HTMLParser:

    def __init__(self, url):
        self.url = url
        try:
            self.source = requests.get(self.url).text
        except requests.exceptions.ConnectionError:
            self.source = ''
        self.soup = BeautifulSoup(self.source, 'html.parser')
        self.prettysoup = self.soup.prettify()
        try:
            self.category_tag = self.soup.find('h2').text
        except AttributeError:
            self.category_tag = 'SAP ABAP'

    def category(self):
        return self.category_tag.split('>')[1].strip()

    def location(self):
        return self.soup.find_all('ul', class_='control-panel')[1].li.text.strip()

    def job_title(self):
        return self.soup.find('h2', class_='jobd-title').text


class BlogParser(HTMLParser):
    def __init__(self):
        super().__init__('https://sapbazar.com/sap-blogs/')
        self.blog_category = self.soup.find_all(class_="allmode-category", )
        self.blog_post_links = self.soup.find_all(class_="allmode-title")

    def get_urls(self):
        return [("https://sapbazar.com" + BeautifulSoup(str(link), 'html.parser').a['href'])
                for link in self.blog_post_links]

    def get_titles(self):
        return [BeautifulSoup(str(link), 'html.parser').get_text()
                for link in self.blog_post_links]

    def get_categories(self):
        return [self.check_str(BeautifulSoup(str(string), 'html.parser').text) for string in self.blog_category]

    def blog_posts(self):
        return [[link, category, title] for link, category, title in zip(self.get_urls(), self.get_categories(), self.get_titles())]

    @staticmethod
    def check_str(string):
        if string.startswith('SAP'):
            return string
        elif string == 'S/4 HANA':
            return 'SAP S/4HANA'
        else:
            return 'SAP ' + string
