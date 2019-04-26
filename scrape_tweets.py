"""
Scrape data from the Twitter page
"""

import sys
import os
import requests
import re
from time import sleep
from bs4 import BeautifulSoup as bs
import bs4
from translate import *

base_url = "https://twitter.com/i/profiles/show/{}/timeline/tweets"

params = {"include_available_features":1,
          "include_entities":1,
          "reset_error_state":False}

def remove_link(text):
    reg_exp = 'pic.twitter.com/\S*'
    return re.sub(reg_exp, '', text)

def download_image(images_dict, filename):
    """
    Params: images_dict: Dict object - Map of image name and image url
            filename: String - Twitter Account handle
    Download images and store it in images/ folder
    """
    for name, url in images_dict.items():
        print('Downloading {}'.format(name))
        path = '{}/no_images/{}'.format(filename, name)
        while(True):
            try:
                res = requests.get(url, stream=True)
                with open(path, 'wb') as f:
                    f.write(res.content)
                break
            except:
                print('Downloading {} failed'.format(name))
                sleep(5)

def extract_memes(_buffer, filename):
    """
    Extract text/images from the raw HTML data
    Params: _buffer: String - Raw HTML data
            filename: String - Twitter Account handle
    """
    images_dict = {}
    try:
        os.makedirs(filename+'/no_images')
    except:
        pass


    print('Making soup for {}...'.format(filename))
    soup = bs(_buffer, 'html.parser')
    soup.ignore_links = True
    print('Done\n')

    items = [i for i in list(soup.children) if isinstance(i, bs4.element.Tag)]
    print('Total items: {}\n'.format(len(items)))

    print('Reading tweets content..',)

    raw_tweet_content = ''
    tweet_id_image_list = []

    translate_flag = False

    with open('{}/{}_data.txt'.format(filename, filename), 'a') as fp2:
        for counter, html in enumerate(items):
            tweet_id = html.find('div').get('data-item-id')
            try:
                tweet_content = html.find('div').find('div', {'class': 'js-tweet-text-container'}).find('p').text.strip().replace('\n', ' ')
                tweet_content = remove_link(tweet_content)
                if not tweet_content:
                    tweet_content = 'NO_TWEET_TEXT'
            except AttributeError:
                tweet_content = None

            try:
                image_url = html.find('div').find('div', {'class': 'AdaptiveMediaOuterContainer'}).find('img').get('src')
                extension = image_url.split('.')[-1]
                image = 'Media_{}.{}'.format(counter+1, extension)
                images_dict[image] = image_url
            except AttributeError:
                image = 'NO_IMAGE'

            _tweet_text = tweet_content
            try:
                if not detect_language(_tweet_text) == 'en':
                    raw_tweet_content += 'x_yz_xy_z' + _tweet_text
                    tweet_id_image_list.append((str(tweet_id), str(image)))
                    translate_flag = True
                else:
                    fp2.write(str(tweet_id)+','+_tweet_text+','+str(image)+'\n')
            except:
                print(_tweet_text)
                pass

        if translate_flag:
            translated_tweets = get_translated_tweets(raw_tweet_content)
            for tweet_id_image, tweet in zip(tweet_id_image_list, translated_tweets):
                fp2.write(tweet_id_image[0]+','+tweet+','+tweet_id_image[1]+'\n')

    print('Done\n')
    download_image(images_dict, filename)

if __name__ == '__main__':
    n_twitter_handles = len(sys.argv)
    if not n_twitter_handles >= 2:
        print('Error: No twitter handle found\nUsage: python scrape_tweets.py <handle1> <handle2> ...')
        sys.exit()
    else:
        for i in range(1, len(sys.argv)):
            filename = '' + sys.argv[i]
            raw_data = ''
            count = 0
            has_more_items = True
            print('Collecting raw data of {}...'.format(filename))
            while(has_more_items and count <= 2):
                count2 = 0
                while(True):
                    if (count2 == 3):
                        has_more_items = False
                        with open('temp.txt', 'a') as fp:
                            fp.write(filename + ' ')
                        break
                    try:
                        print("Reading page {}".format(count))
                        res = requests.get(base_url.format(filename), params=params).json()
                        break
                    except:
                        print('Exception: sleeping for 10 sec\n')
                        sleep(10)
                        count2 += 1
                min_position = res['min_position']
                has_more_items = res['has_more_items']
                params['max_position'] = min_position
                raw_data += res['items_html']
                count += 1
        extract_memes(raw_data, filename)
