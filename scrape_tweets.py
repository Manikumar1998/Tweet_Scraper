"""
Scrape data from the Twitter page
"""
import sys
import requests
import re
from bs4 import BeautifulSoup as bs
import bs4
import os

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
        print 'Downloading {}'.format(name)
        path = '{}/images/{}'.format(filename, name)
        while(True):
            try:
                res = requests.get(url, stream=True)
                with open(path, 'wb') as f:
                    f.write(res.content)
                break
            except:
                print 'Downloading {} failed'.format(name)
                sleep(5)
            
def extract_memes(_buffer, filename):
    """
    Extract text/images from the raw HTML data
    Params: _buffer: String - Raw HTML data
            filename: String - Twitter Account handle
    """
    images_dict = {}
    try:
        os.makedirs(filename+'/images')
    except:
        pass
    fp2 = open('{}/{}_data.txt'.format(filename, filename), 'a')
    
    print 'Making soup for {}..\n'.format(filename)
    soup = bs(_buffer, 'html.parser')
    soup.ignore_links = True
    print 'Done making soup..\n'

    items = [i for i in list(soup.children) if isinstance(i, bs4.element.Tag)]
    print 'Total items: {}\n'.format(len(items))

    print 'Reading tweets content..',

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
        fp2.write(str(tweet_id)+','+str(tweet_content.encode('utf-8'))+','+str(image)+'\n')
    fp2.close()
    print 'Done\n'
    download_image(images_dict, filename)

if __name__ == '__main__':
    n_twitter_handles = len(sys.argv)
    if not n_twitter_handles >= 2:
        print 'Error: No twitter handle found\nUsage: python scrape_tweets.py <handle1> <handle2> ...'
        sys.exit()
    else:
        for i in xrange(1, len(sys.argv)):
            filename = sys.argv[i]
            raw_data = ''
            count = 0
            has_more_items = True
            print 'Collecting raw data of {}...'.format(filename)
            while(has_more_items):
                count += 1
                while(True):
                    try:
                        print "Reading page {}".format(count)
                        res = requests.get(base_url.format(filename), params=params).json()
                        break
                    except:
                        print 'Exception: sleeping for 10 sec\n'
                        sleep(10)
                min_position = res['min_position']
                has_more_items = res['has_more_items']
                params['max_position'] = min_position
                raw_data += res['items_html']
        extract_memes(raw_data, filename)
