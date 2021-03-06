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
        questions = response.json()['responseBody']['questions']
        return questions

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
            response_json = response.json()
        except JSONDecodeError:
            return None
        if response_json and response_json.get("status") == '401':
            resp_body = None
        else:
            resp_body = response_json.get('responseBody')
        if resp_body:
            questions = resp_body.get('questions')
        else:
            questions = None
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
        question = response.json().get('responseBody')
        return question

    async def get_answers(self):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETANSWERS"
            }
        }

        response = requests.request("GET", self.source, json=params)
        answers = response.json()['responseBody']['answers']
        return answers

    async def get_comments(self, qid):
        question = await self.get_detailed_question(qid)
        return question.get("comments")

    async def write_comment(self, parent_id, user, content):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "WRITECOMMENT"},
            "requestBody": {
                "userid": f"{user}",
                "content": f"{content}",
                "parentpostid": f"{parent_id}"}
        }
        try:
            response = requests.request("POST", self.source, json=params)
        except JSONDecodeError:
            response = {"error": "invalid request"}
        #  response:
        #  {'responseHeader': {'serviceId': '111', 'status': '200', 'message': 'Answer added'},
        #  'responseBody': {'userid': '249', 'postid': 318}}
        return response

    async def get_user_points(self, user_id):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETUSERPOINTS",
                "user_id": f"{user_id}"
            }
        }
        response = requests.request("GET", self.source, json=params)
        try:
            json_response = response.json()
        except JSONDecodeError:
            json_response = {"error": "invalid request"}
        response_body = json_response.get("responseBody")
        if response_body:
            points = response_body.get("points")[0].get('points')
        else:
            return 0
        return points

    async def get_top_ten(self):
        params = {
            "requestHeader": {
                "serviceId": "111",
                "interactionCode": "GETTOPTEN"
            }
        }
        response = requests.request("GET", self.source, json=params)
        try:
            json_response = response.json()
        except JSONDecodeError:
            json_response = {"error": "invalid request"}
        response_body = json_response.get("responseBody")
        if response_body:
            points = response_body.get('points')
        else:
            points = None
        return points

    async def is_new_answers(self, file):
        current = await self.get_answers()
        previous = self.read_json(file)
        if previous[0] == current[0]:
            return False
        if len(previous) < len(current):
            difference = len(current) - len(previous)
            self.write_json(file, current)
            return current[:difference]
        return False

    @staticmethod
    def write_json(file, data):
        with open(file, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def read_json(file):
        with open(file, "r") as f:
            return json.load(f)
