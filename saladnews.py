import future
import re
import requests
import chardet
import html

# NLP based article extractor
# Please refer to installation
# https://pypi.python.org/pypi/newspaper3k/0.2.6
import newspaper
from multiprocessing.dummy import Pool as ThreadPool
# Google news API
from newsapi import NewsApiClient

# Flesch Reading Ease calculator
from textstat.textstat import textstat

# Link to modified files
from IPython.display import FileLink
from IPython.core.display import display, HTML

newsapi = NewsApiClient(api_key='db86173c27ee4c31a0894b5adb00fc84')

# How many words in each segment. Usually Google TTS speaks 150 words per mintues
word_limit = 200

# The topic to query
topic = "gun"

# The source to query
resources = ["BLOOMBERG", "CNN"]

def get_score_multi(topic, resources):
    pool = ThreadPool(16)

    pending = []
    for resource in resources:
        top_headlines = newsapi.get_everything(q=topic, sources=resource, page=1, language='en')
        for article in top_headlines['articles']:
            pending.append([resource, article])

    result = pool.starmap(download, pending)
    pool.close()
    pool.join()

    score = []
    for entry in result:
        if entry != None:
            score.append(entry)

    return score

def download(resource, article):
    article_text = download_article(article['url'])
    if article['title']!= None and article_text != None:
        print(article['url'])
        print(textstat.automated_readability_index(article_text))
        norm_score = int(textstat.automated_readability_index(article_text)/15*100)

        vote = 0
        req = requests.get('http://localhost:3000/posts?title=' + article['title'])
        if len(req.json()) is 0:
            res = requests.post('http://localhost:3000/posts', data={'title': article['title'], 'vote': 0})
        else:
            vote = req.json()[0]['vote']

        if norm_score < 75:
            easiness = "easy"
        elif norm_score > 90:
            easiness = "difficult"
        else:
            easiness = "medium"

        if article['urlToImage'] != '':
            return {'score': norm_score,
                'resource': resource.upper().replace("-", " ").replace("THE",""),
                'title': article['title'],
                'url': article['url'],
                'img': article['urlToImage'],
                'snippet': article['description'],
                'easiness':easiness,
                'vote': vote}



def get_score(topic, resources):
    score = []

    for resource in resources:
        top_headlines = newsapi.get_everything(q=topic, sources=resource, page=1, language='en')
        for article in top_headlines['articles']:
            article_text = download_article(article['url'])
            if article['title']!= None and article_text != None:
                print(article['url'])
                print(textstat.automated_readability_index(article_text))
                norm_score = textstat.automated_readability_index(article_text)/15*100

                vote = 0
                req = requests.get('http://localhost:3000/posts?title=' + article['title'])
                if len(req.json()) is 0:
                    res = requests.post('http://localhost:3000/posts', data={'title': article['title'], 'vote': 0})
                else:
                    vote = req.json()[0]['vote']

                if norm_score < 75:
                    easiness = "easy"
                elif norm_score > 90:
                    easiness = "difficult"
                else:
                    easiness = "medium"


                if article['urlToImage'] != '':
                    score.append({'score': int(norm_score),
                     'resource': resource.upper().replace("-", " "),
                     'title': article['title'],
                     'url': article['url'],
                     'snippet': article['description'],
                     'img': article['urlToImage'],
                     'easiness':easiness,
                     'vote': vote})
    return score


def download_article(url):
    """Download and parse the article content from given URL.

    This function uses regular express to count the words for the article,
    and returns the whole article as plain text.

    Args:
        url (str): URL to the news article.

    Returns:
        A string of plain text, without HTML tags.
    """
    article = newspaper.Article(url)
    article.download()

    try:
        article.parse()
    except Exception:
        print("Failed to extract article from given page.")
        return

    print("Find Article: " + article.title)

    word_count = len(re.findall('\w+', article.text))
    # print("Total words: " + str(word_count))
    if word_count < word_limit:
        print("Short Article, skip.\n")
        return
    return article.text



from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
app = Flask(__name__)


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')

@app.route("/articles", methods=['GET','POST'])
def articles():
    """API that takes in searching query and returns information on relevant articles
    Returns:
        json object of search topic
    """
    searchTerm = request.args.get('search')
    resource = request.args.get('resource')
    print (resource)
    resources = ["BLOOMBERG", "CNN"]
    if len(resource) > 0:
        resources = resource.split(',')
    print (resources)
    level = request.args.get('level')

    # data = get_score(searchTerm, resources)
    data = get_score_multi(searchTerm, resources)
    return render_template('articles.html', data = data, level = level)

# on the home page, when put into search bar
@app.route("/search", methods=['GET','POST'])
def search():
    """API that takes in searching query and returns information on relevant articles
    Returns:
        json object of search topic
    """
    searchTerm = request.args.get('search')
    # data = get_score(searchTerm, resources)
    resources = ["BLOOMBERG", "CNN"]
    data = get_score_multi(searchTerm, resources)
    return render_template('articles.html', data = data, level = 0)
    
    # return redirect(url_for('listen', chunks= ch, article = article_title, audioList = audios))


if __name__ == '__main__':
    app.run()
