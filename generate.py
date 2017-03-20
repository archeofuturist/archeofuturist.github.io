#!/usr/bin/env python2.7

import re
import os
import json
import time
import urllib
import collections

BASE_URL = 'https://a.4cdn.org/pol/'

STYLE = """
    html {
        background: black;
        color: #ddd;
        font-size: 18px;
        background-image: url('logo.png');
        background-repeat: no-repeat;
        background-size: 20%;
        font-weight: 400;
    }
    a {
        color: red;
    }
    .controls {
        float: left;
        width: 100%;
        height: 15%;
        text-align: center;
        padding-bottom: 5px;
    }
    i {
        font-size: 10px;
        color: #aaa;
    }
"""

TEMPLATE = """
<html>
   <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
    <head>
        <style>
            {style}
        </style>
        <div class='logo'></div>
        <div class='controls'>
            <a href='{prev_no}.html'>&lt; prev</a>
            thread no.<a href='http://boards.4chan.org/pol/thread/{thread_no}'>{thread_no}</a>
            <a href='{next_no}.html'>next &gt;</a>
            <br/>
            <i>last updated: {ts}</i>
        </div>
    </head>
    <center>
        <iframe id='ytplayer' type='text/html' width='60%' height='60%'
          src='https://www.youtube.com/embed/{video_id}?autoplay=1'
          frameborder='0'/>
    </center>
</html>"""

youtube_re = r'.*(https://www.youtube\.com/watch[/\a-zA-Z0-9<>?=)]+) '


def cached_get(url, cache_dir='.cache', timeout=1800):
    if os.path.exists(cache_dir) is False:
        os.mkdir(cache_dir)

    fname = cache_dir + '/' + ''.join([c for c in url if c.isalnum()])

    if os.path.exists(fname) is True:
        if (time.time() - os.stat(fname).st_ctime) <= timeout:
            with open(fname, 'r') as f:
                return f.read()

    data = urllib.urlopen(url).read()
    with open(fname, 'w') as f:
        f.write(data)
    return data


def get_video_id(url):
    br = re.search('<br', url)
    if br is not None:
        url = url[:br.start()]
    open_tag = 0
    clean_url = ''
    for c in url:
        if c == '<':
            open_tag += 1
        if c == '>':
            open_tag -= 1
            continue
        elif open_tag > 0:
            continue
        clean_url += c
    return re.match('.*v=([a-zA-Z0-9\-_]+)', clean_url).group(1)


def get_video_urls_from_page(start, end):
    videos = collections.defaultdict(set)
    for page_num in range(start, end + 1):
        print('fetching from page {}/{}'.format(page_num, end))
        raw_page = cached_get(BASE_URL + str(page_num) + '.json')
        page_data = json.loads(raw_page)
        thread_numbers = [t['posts'][0]['no'] for t in page_data['threads']]
        for no in thread_numbers:
            raw_t = cached_get(BASE_URL + '/thread/' + str(no) + '.json')
            t_data = json.loads(raw_t)
            for p in t_data['posts']:
                matches = re.match(youtube_re, p.get('com', ''))
                if matches is not None:
                    for m in matches.groups():
                        videos[no].add(get_video_id(m))
    return videos


if __name__ == '__main__':
    import sys
    import datetime

    page_num = int(sys.argv[1])
    videos = get_video_urls_from_page(1, page_num)
    videos_total = 0
    for s in videos.values():
        videos_total += len(s)
    count = 1
    for thread_no, video_ids in videos.items():
        for video_id in video_ids:
            prev_no = count - 1
            if prev_no <= 0:
                prev_no = videos_total

            next_no = count + 1
            if next_no > videos_total:
                next_no = 1

            with open(str(count) + '.html', 'w') as out:
                out.write(TEMPLATE.format(**{
                    'style': STYLE,
                    'thread_no': thread_no,
                    'video_id': video_id,
                    'prev_no': prev_no,
                    'next_no': next_no,
                    'ts': datetime.datetime.now(),
                }))
            count += 1
