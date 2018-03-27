import requests
import shutil
import time
import json
import math
import urllib3
import progressbar
from config import get_from_config

urllib3.disable_warnings() # disable ssl InsecurePlatform warning...

# the API URL of the tumblr blog,
# e.g. https://api.tumblr.com/v2/blog/seat-safety-switch.tumblr.com/posts/
url = get_from_config('url')

class TumblrEntry:
    def maybeUtf8(self, input):
        if input is not None and type(input) is not str:
            return input.encode('utf-8') # python 2
        return input # python 3
    def get_photo_urls(self, photos):
        photo_blobs = map(lambda p: p['alt_sizes'], photos)
        # fetch the best-quality (biggest) version of the pic
        photo_urls = map(lambda p: max(p, key=(lambda t: t['width']))['url'], photo_blobs)
        return map(lambda p: self.maybeUtf8(p), photo_urls)
    def __init__(self, title, body, url, tags, photos):
        self.title = self.maybeUtf8(title)
        self.body = self.maybeUtf8(body)
        self.url = self.maybeUtf8(url)
        self.tags = list(map(lambda t: self.maybeUtf8(t), tags))
        self.photos = self.get_photo_urls(photos)

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
        if post['type'] == 'text':
            # probably text
            entry = TumblrEntry(post['title'], post['body'], post['post_url'], post['tags'], [])
            result.append(entry)
        elif post['type'] == 'photo':
            # maybe a photo set
            entry = TumblrEntry(post['caption'], '', post['post_url'], post['tags'], post['photos'])
            result.append(entry)
        else:
            print 'unhandled post type: ' + post['type']
    return result

def panic_on_bad_status(resp):
    if resp.status_code != 200:
        print('Unexpected status code: {0:d}'.format(resp.status_code))

api_key = get_from_config('api_key')
total_posts = get_post_count()
page_size = 20 # default of tumblr api, probably a reasonable limit
pages = int(math.ceil(total_posts/page_size)) + 1
print('Expecting to download {0:d} pages'.format(pages))

def download_image(image_url):
    print 'downloading image at ' + image_url
    local_filename = image_url.split('/')[-1]
    # TODO: prefix soon, so we can package this?
    r = requests.get(image_url, stream=True)
    panic_on_bad_status(r)
    with open(local_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    return local_filename

all_posts = []

progress_bar = progressbar.ProgressBar()

for i in progress_bar(range(0, pages)):
    posts_this_page = get_entries(i, page_size)
    all_posts.extend(posts_this_page)
    # don't be a dick, sleep between hits
    time.sleep(1)

# all posts downloaded, write them to file
with open("posts.html", "w") as f:
    f.write("<head><meta charset='UTF-8'/></head>\n")
    f.write("<body>\n")
    for post in all_posts:
        title = '<null>' if post.title is None else post.title
        f.write("<H1>" + title + "</H1>\n")
        if len(post.body) > 0:
            f.write(post.body + "\n")
        else:
            for photo in post.photos:
                local_photo = download_image(photo)
                f.write('<img src="' + local_photo + '"/>\n')
        f.write("<a href='" + post.url + "'>#</a> \n")
        if len(post.tags) > 0:
            f.write("tags: ")
            f.write(", ".join(post.tags))
            f.write("\n")
        f.write("<hr/>\n")
    f.write("</body>\n")
