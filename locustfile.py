import os
from locust import HttpUser, task, between, tag

# URLs reais dos posts e imagens no seu WordPress
POST_150KB = os.getenv("POST_150KB", "/post-150kb/")
POST_300KB = os.getenv("POST_300KB", "/post-300kb/")
POST_400KB = os.getenv("POST_400KB", "/post-400kb/")

IMG_150KB_URL = os.getenv("IMG_150KB_URL", "/wp-content/uploads/2026/10/HH_w07gWsAAZJJq.jpg")
IMG_300KB_URL = os.getenv("IMG_300KB_URL", "/wp-content/uploads/2026/10/300kb.jpg")

HEADERS = {"Host": "localhost"}


class WordPressUser(HttpUser):
    wait_time = between(0.5, 1.0)

    @tag("img-150kb")
    @task
    def post_150kb_image(self):
        self.client.get(POST_150KB, headers=HEADERS, name="GET post-150kb")
        self.client.get(IMG_150KB_URL, headers=HEADERS, name="GET img-150kb")

    @tag("text-400kb")
    @task
    def post_400kb_text(self):
        self.client.get(POST_400KB, headers=HEADERS, name="GET post-400kb")

    @tag("img-300kb")
    @task
    def post_300kb_image(self):
        self.client.get(POST_300KB, headers=HEADERS, name="GET post-300kb")
        self.client.get(IMG_300KB_URL, headers=HEADERS, name="GET img-300kb")