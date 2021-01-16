from json.decoder import JSONDecodeError

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

    async def create_question(self, user_email, title, content, category_id, tags, photo=None):
        content = content if not photo else \
            f'''<p>{content}</p><p><img alt="{title}" src=" {photo}" style="height:1280px; width:960px"></p>'''
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "CREATEQUESTION"
            },
            "requestBody": {
                "userid": str(user_email),
                "title": str(title),
                "content": f"{content}",
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
        post_id = response.json()['responseBody']['postid']
        return str(post_id)

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
        response = requests.request("GET", self.source, headers=self.headers, data=json.dumps(params)).json()
        response_body = response['responseBody']
        try:
            question = response_body['question'][0]
            question_title = question['title']
        except TypeError or JSONDecodeError:
            question_title = 'Title is not available'
        return question_title

    async def set_best_answer(self, question_id, answer_id, user_id):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "SETBESTANSWER"
            },
            "requestBody": {
                "questionid": str(question_id),
                "answerid": str(answer_id),
                "userid": str(user_id)
            }
        }
        response = requests.request("GET", self.source, headers=self.headers, data=json.dumps(params))
        return response.json()

    async def vote_answer(self, user_id, post_id, vote):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "VOTE"
            },
            "requestBody": {
                "userid": str(user_id),
                "postid": str(post_id),
                "vote": str(vote)
            }
        }
        response = requests.request("POST", self.source, headers=self.headers, json=params)
        return response.text

    def get_all_questions(self):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETQUESTIONS"
            },
            "requestBody": {
                "userid": "2"
            }
        }
        response = requests.request("GET", self.source, json=params)
        # questions = json.dumps(response.json()['responseBody']['questions'], indent=2)
        # questions = json.loads(questions)
        # question_ids = [item['postid'] for item in questions]
        return response.text

    async def get_image_internal_link(self, image):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "SAVEIMAGE"
            },
            "requestBody": {
                "base64data": f"data:image/jpeg;base64,{image}"
            }
        }
        response = requests.request("POST", self.source, json=params)
        link = response.json()['responseBody']['Url']
        return link

    async def get_user_questions(self, user_email):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETUSERQUESTIONS",
                "user_id": f"{user_email}"
            }
        }
        response = requests.request("POST", self.source, json=params)
        try:
            response_body = response.json()['responseBody']
            questions = response_body['questions']
        except JSONDecodeError:
            questions = 'Error, no available questions created by provided user'
        return questions

    async def get_detailed_question(self, post_id):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode":
                    "GETQUESTIONDETAIL"},
            "requestBody": {
                "questionid": f"{post_id}"
            }
        }
        response = requests.request("GET", self.source, json=params)
        return response.json()
