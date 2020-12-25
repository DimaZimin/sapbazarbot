import requests
import json

class QuestionsAPI:

    def __init__(self):
        self.source = 'https://qa.sapbazar.com/api/'
        self.headers = {
            'Content-Type': 'application/json'
        }

    def get_questions(self):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETQUESTIONS"
            },
            "requestBody": {
                "userid": "11"
            }
        }
        response = requests.request("GET", self.source, data=params)
        return response.text

    async def create_question(self, user_email, title, content, category_id, tags):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "CREATEQUESTION"
            },
            "requestBody": {
                "userid": str(user_email),
                "title": str(title),
                "content": str(content),
                "categoryid": str(category_id),
                "tags": str(tags)
            }
        }
        response = requests.request("POST", self.source, headers=self.headers, json=params)
        return response.json()

    def delete_post(self, post_id):
        data = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "DELETEPOST"},
            "requestBody": {
                "postid": str(post_id)
            }
        }
        response = requests.request('POST', self.source, headers=self.headers, data=json.dumps(data))
        return response.text

    def get_categories(self):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETCATEGORIES"
            }
        }
        response = requests.request("GET", self.source, data=json.dumps(params))
        response_body = response.json()['responseBody']
        response_categories = response_body['categories']
        return [item['title'] for item in response_categories]

    async def get_category_id(self, title):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETCATEGORIES"
            }
        }
        response = requests.request("GET", self.source, data=json.dumps(params))
        categories_from_response = response.json()['responseBody']['categories']
        category_id = [item['categoryid'] for item in categories_from_response if item['title'] == title]
        return category_id[0]

    async def get_category_tag(self, title):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETCATEGORIES"
            }
        }
        response = requests.request("GET", self.source, data=json.dumps(params))
        categories_from_response = response.json()['responseBody']['categories']
        tag = [item['tags'] for item in categories_from_response if item['title'] == title]
        return tag[0]

    async def write_answer(self, user, post_id, content):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "WRITEANSWER"
            },
            "requestBody": {
                "userid": str(user),
                "content": content,
                "parentpostid": str(post_id)

            }
        }
        response = requests.request("POST", self.source, headers=self.headers, json=params)
        return response.text

    async def get_question_title(self, question_id):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETQUESTIONDETAIL"
            },
            "requestBody": {
                "questionid": str(question_id)
            }
        }
        response = requests.request("GET", self.source, headers=self.headers, data=json.dumps(params))
        question_title = response.json()['responseBody']['question'][0]['title']
        return question_title
