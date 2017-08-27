import requests
import time
import json
import math
import urllib3
from config import get_from_config

urllib3.disable_warnings() # disable ssl InsecurePlatform warning...

# the API URL of the tumblr blog,
# e.g. https://api.tumblr.com/v2/blog/seat-safety-switch.tumblr.com/posts/text
url = get_from_config('url')

class TumblrEntry:
    def __init__(self, title, body, url):
        self.title = title
        self.body = body
        self.url = url

def get_post_count():
    r = requests.get(url, params = {'api_key': api_key})
    panic_on_bad_status(r)
    json = r.json()
    resp = json['response']
    return resp['total_posts']

def get_entries(page_number, page_size=20):
    r = requests.get(url, params = {'offset': page_number * page_size, 'limit': page_size, 'api_key': api_key})
    panic_on_bad_status(r)

    response = r.json()['response']
    posts = response['posts']
    result = []
    for post in posts:
        entry = TumblrEntry(post['title'], post['body'], post['post_url'])
        result.append(entry)
    return result

def panic_on_bad_status(resp):
    if resp.status_code != 200:
        print('Unexpected status code: {0:d}'.format(resp.status_code))

api_key = get_from_config('api_key')
total_posts = get_post_count()
page_size = 20 # default of tumblr api, probably a reasonable limit
pages = int(math.ceil(total_posts/page_size)) + 1
print('Expecting to download {0:d} pages'.format(pages))

all_posts = []

for i in range(0, pages):
    posts_this_page = get_entries(i, page_size)
    all_posts.extend(posts_this_page)
    print('scraped page {0:d}'.format(i + 1))
    # don't be a dick, sleep between hits
    time.sleep(1)

# all posts downloaded, write them to file
with open("posts.html", "w") as f:
    f.write("<head><meta charset='UTF-8'/></head>\n")
    f.write("<body>\n")
    for post in all_posts:
        # python2
        if type(post.url) is not str:
            title = '<null>' if post.title is None else post.title.encode('utf-8')
            f.write("<H1>" + title + "</H1>\n")
            f.write(post.body.encode('utf-8') + "\n".encode('utf-8'))
            f.write("<a href='" + post.url.encode('utf-8') + "'>#</a>\n")
        # python3
        else:
            title = '<null>' if post.title is None else post.title
            f.write("<H1>" + title + "</H1>\n")
            f.write(post.body + "\n")
            f.write("<a href='" + post.url + "'>#</a>\n")
        f.write("<hr/>\n")
    f.write("</body>\n")
