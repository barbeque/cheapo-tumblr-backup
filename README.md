# Cheapo Tumblr Backup
A scraper for largely-text tumblr blogs.

## What you need
 * A working Python 2.x (or 3.x) installation.
 * A [Tumblr API key](https://www.tumblr.com/oauth/apps). You'll use the consumer key for this utility (see below)
 * The [API URL](https://www.tumblr.com/docs/en/api/v2#overview) for the blog you want to scrape.

## Running
 * Use [pip](https://pip.pypa.io/en/stable/installing/) to install the contents of requirements.txt: `pip install -r requirements.txt`. Ideally you should use virtualenv to prevent installing these packages globally, where they may conflict with future/past Python software.
 * Create a `config.yml` file in the same directory as the scrape.py script. It should contain the keys:
   * `api_key`: Must be a quoted string equalling the API consumer key you got from Tumblr.
   * `url`: The API URL for the blog you want to scrape.
 * Run the scrape.py script. It will go away for awhile and generate a huge html file called `posts.html` containing all text content of your posts. The content of all photo posts will be dumped into the same directory.
