import requests
import shutil
import time
import json
import math
import urllib3
import progressbar
import os, sys
import re
from optparse import OptionParser
from config import get_from_config

urllib3.disable_warnings() # disable ssl InsecurePlatform warning...

PREFIX='posts'

parser = OptionParser()
parser.add_option('-u', '--user', dest='user', help='The name of the user whose tumblr you are going to scrape.')

(options, args) = parser.parse_args()


def generate_edit_url_for_post(post_url):
    # input: https://seatsafetyswitch.com/post/720388323541172224/theres-something-that-we-all-can-learn-from-stage
    # output: https://www.tumblr.com/edit/seat-safety-switch/720388323541172224
    number_parts = re.search('(\/([0-9]+)\/)', post_url).groups()
    return f'https://www.tumblr.com/edit/{options.user}/{number_parts[1]}'

# the API URL of the tumblr blog,
# e.g. https://api.tumblr.com/v2/blog/seat-safety-switch.tumblr.com/posts/
if not options.user:
    url = get_from_config('url')
    options.user = 'seat-safety-switch' # hack
else:
    url = f'https://api.tumblr.com/v2/blog/{options.user}.tumblr.com/posts/text'

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
    def __init__(self, title, body, url, tags, photos, note_count, date):
        self.title = self.maybeUtf8(title)
        self.body = self.maybeUtf8(body)
        self.url = self.maybeUtf8(url)
        self.note_count = note_count
        self.date = self.maybeUtf8(date)
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
            entry = TumblrEntry(post['title'], post['body'], post['post_url'], post['tags'], [], post['note_count'], post['date'])
            result.append(entry)
        elif post['type'] == 'photo':
            # maybe a photo set
            entry = TumblrEntry(post['caption'], '', post['post_url'], post['tags'], post['photos'], post['note_count'], post['date'])
            result.append(entry)
        elif post['type'] == 'link':
            # A link
            header = '<a href="' + post['url'] + '">' + post['title'] + '</a>'
            body = header + "<br/>" + post['description']
            entry = TumblrEntry(post['title'], body, post['post_url'], post['tags'], [], post['note_count'], post['date'])
            result.append(entry)
        elif post['type'] == 'quote':
            body = '&#8220;' + post['text'] + '&#8221;<br/> ~' + post['source'] + '<br/>'
            entry = TumblrEntry('', body, post['post_url'], post['tags'], [], post['note_count'], post['date'])
            result.append(entry)
        elif post['type'] == 'chat':
            # There is also the 'dialogue' array, which is good for formatting,
            # but I don't think I need to reformat
            body = ''
            for entry in post['dialogue']:
                if len(entry['name']) > 0:
                    body += '<b class="chat-name">' + entry['name'] + '</b>: ' + '<span class="chat-phrase">' + entry['phrase'] + '</span>'
                else:
                    # just text, no name
                    body += '<span class="chat-phrase">' + entry['phrase'] + '</span>'
                body += '<br/>'
            entry = TumblrEntry(post['title'], body, post['post_url'], post['tags'], [], post['note_count'], post['date'])
            result.append(entry)
        else:
            print('unhandled post type: ' + post['type'])
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
    print('downloading image at ' + image_url)
    local_filename = image_url.split('/')[-1]
    local_filename = os.path.join(PREFIX, local_filename)
    # TODO: prefix soon, so we can package this?
    r = requests.get(image_url, stream=True)
    panic_on_bad_status(r)
    with open(local_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    return local_filename

# make a directory to use to store
if not os.path.exists(PREFIX):
    os.makedirs(PREFIX)

# begin scrape
all_posts = []

progress_bar = progressbar.ProgressBar()

for i in progress_bar(range(0, pages)):
    posts_this_page = get_entries(i, page_size)
    all_posts.extend(posts_this_page)
    # don't be a dick, sleep between hits
    time.sleep(1)

# check for posts that should be tagged 'best of' but aren't
BEST_OF_THRESHOLD = 1000
for post in all_posts:
    if post.note_count >= BEST_OF_THRESHOLD and ('best of' not in post.tags):
        print(f'Post {generate_edit_url_for_post(post.url)} has {post.note_count} notes, but is not marked best-of')

# all posts downloaded, write them to file
posts_file_path = os.path.join(PREFIX, 'posts.html')
with open(posts_file_path, "w") as f:
    f.write("<head><meta charset='UTF-8'/></head>\n")
    f.write("<body>\n")
    for post in all_posts:
        f.write('<div class="post">\n')
        title = '<null>' if post.title is None else post.title
        f.write("<H1>" + title + "</H1>\n")
        f.write("<h3>" + post.date + "</h3>\n")
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
        f.write('</div>\n')
    f.write("</body>\n")
