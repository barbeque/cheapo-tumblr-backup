import requests
import time
import json

url = "https://api.tumblr.com/v2/blog/seat-safety-switch.tumblr.com/posts/text"

# move offset parameter
# check response.posts.body, response.posts.title for content
# check response.total_posts for limit on offset parameter

class TumblrEntry:
    def __init__(self, title, body):
        self.title = title
        self.body = body

def get_post_count():
    r = requests.get(url)
    json = r.json()

    return json['response']['total_posts']

def get_entries(page_number, page_size=20):
    r = requests.get(url, params = {'offset': page_number * page_size, 'limit': page_size})

    if r.status_code != 200:
        print 'Weird status code', r.status_code

    response = r.json()['response']
    posts = response['posts']
    result = []
    for post in posts:
        entry = TumblrEntry(post['title'], post['body'])
        result.append(entry)
    return result
    
total_posts = get_post_count()
page_size = 20 # default of tumblr api, probably a reasonable limit
pages = int(round(total_posts / page_size))
print 'Expecting to download', pages, 'pages'

all_posts = []

for i in range(0, pages):
    posts_this_page = get_entries(i, page_size)
    all_posts.extend(posts_this_page)
    print 'scraped page', (i + 1)

    # don't be a dick, sleep between hits
    time.sleep(1)

# all posts downloaded, write them to file
with open("posts.html", "w") as f:
    for post in all_posts:
        if post != None:
            title = '<null>' if post.title == None else post.title
            f.write("<H1>" + title + "</H1>\n")
            f.write(post.body.encode('utf-8') + "\n")
        else:
            print "Weird, encountered a null post"
