"""Application for transforming long articles into given length audio files.

This Python application could transform given long articles into audio files
with online Text-to-Speech APIs. It could be used to help people, especially who
do not have enough time to read a long article, by generating handy smaller
length audio files which could listen during commuting.
"""

import future
import re


# NLP based article extractor
# Please refer to installation
# https://pypi.python.org/pypi/newspaper3k/0.2.6
import newspaper

# Google 3rd-party Text to Speech lib
from gtts import gTTS


def get_articles():
    """Crawl news from given static URL.

    This function returns a list of URLs to the news which displayed on the given page.
    The URLs are extract from the HTML code. Tested on CNN, NYTimes, NBC, and Fox News.

    Returns:
        A list of strings. Each string is a URL to a news article.
    """
    pages = newspaper.build("https://www.nytimes.com/section/politics")

    urls = []
    for article in pages.articles:
        urls.append(article.url)

    return urls


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
    print("Total words: " + str(len(re.findall('\w+', article.text))))
    return article.text, article.title


def split_article(text, word_limit):
    """Split the text with given length.

    The function would split the text into a few segments, each segment has a word count
    equal or less than the given limitation.

    Args:
        text (str): A string of plain text, usually the news article body.
        word_limit (int): the longest length that a segment could be.

    Returns:
        A list of strings, each string is a segment that has a length less than the word_limit.
    """
    paragraphs = re.split(r"\n+", text)

    segments = []
    segment_builder = ""
    current_wordcount = 0

    # construct segments use helpers
    for paragraph in paragraphs:
        paragraph_length = len(re.findall('\w+', paragraph))
        if paragraph_length + current_wordcount < word_limit:
            segment_builder = segment_builder + " " + paragraph
            current_wordcount += paragraph_length
        else:
            segments.append(segment_builder)
            segment_builder = paragraph
            current_wordcount = paragraph_length

    segments.append(segment_builder)
    return segments


def download_audio(segments):
    """Download audio form of the article content; using google's Text-to-Speech API

    Args:
        segments (list of strings): chunks of text to read.

    Returns:
        mp3 files
    """
    # Use gTTS to transform text into audio files.
    for seg in range(len(segments)):
        # Generate the TTS stream
        tts = gTTS(text=segments[seg], lang='en', slow=False)

        # Save to current terminal location
        tts.save("static/audio/" + str(seg) + ".mp3")


from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

# NOT USED
@app.route("/listen/<chunks>/<article>/<audioList>", methods=['GET'])
def listen(chunks, article, audioList):
    """return to another template page
    Returns:
        a template that display the chunks of information and audio files
    """
    print (len(chunks))
    print (audioList[0])
    # return render_template('read.html', chunks = chunks, article = article, audioList = audioList)
    return "he"
# NOT USED
@app.route("/audio/<file>", methods=['GET'])
def api_articles():
    """API for getting the audio file
    Returns:
        audio file
    """

    articles = get_articles()
    return articles


@app.route("/read", methods=['GET','POST'])
def read():
    """API for transforming articles from text to Speech
    Parameters: article url
    Returns:
        A piece of long string that is the article in text form.
    """
    # url = request.form.get('url_to_clean')
    url = request.args.get('user_url')
    print (url)
    text, article_title = download_article(url)
    ch = split_article(text, 300)
    print (len(ch))
    download_audio(ch)
    directory = os.fsencode('./static/audio')
    audios = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        audios.append(filename)
        print (filename)
    return jsonify(article=article_title, chunks=ch, audioList=audios)
    # return render_template('read.html', chunks = ch, article = article_title, audioList = audios)
    # return redirect(url_for('listen', chunks= ch, article = article_title, audioList = audios))


if __name__ == '__main__':
    app.run()
