# youtube_dl needs unicode
from __future__ import unicode_literals
# standard lib
import os
import io
import sys
import time
import datetime
import threading
import Queue
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# kodi module
import xbmc
import xbmcaddon
import xbmcgui

# hack to make youtube_dl work with xbmc redirected stderr
sys.stderr.isatty = lambda: True

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__icon__        = __addon__.getAddonInfo('icon')

class extractor(threading.Thread):
    """deamon extracting information from a media page url
    and putting it in a queue"""
    
    def __init__(self, url, q):
        self.url = url
        self.q = q
        self.t = time.time()
        threading.Thread.__init__(self)

    def run(self):
        ydl_opts = {
            'ignoreerrors': True,
            'noplaylist': True
            }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(self.url, download=False)
            except youtube_dl.utils.DownloadError:
                print 'Error while streaming from '+self.url
            else:
                if info != None:
                    try:
                        stream_url = info['url']
                    except KeyError:
                        if info['_type'] == 'playlist':
                            info = info['entries'][0]
                    stream_url = info['url']
                    name = info['title']+'-'+info['id']
                    self.q.put((name, self.url, stream_url, self.t))

class handler(BaseHTTPRequestHandler):
    '''simple handler reacting to requests'''
    
    def do_GET(self):
        # if receiving watch instruction
        if self.path.startswith('/watch?url='):
            url = self.path[11:]
            
            dialog = xbmcgui.Dialog()
            dialog.notification('Casting', url, xbmcgui.NOTIFICATION_INFO, 5000)
            
            # send http response
            self.send_response(200)
            self.send_header('Content-type',	'text/html')
            self.end_headers()
            self.wfile.write("""<html>
            <head><title>""" + url + """</title></head>
            <body>Trying to play """ + url + """ ...</body>
            </html>""")
            
            # send request to media info extractor
            ext = extractor(url, QUEUE)
            ext.start()
        else:
            self.send_error(404,'File Not Found: %s' % self.path)


class server(threading.Thread):
    """deamon http server for new media requests"""
    
    def run(self):
        # Interface listenning for web playing events
        host = ''
        port = int(__addon__.getSetting('port'))
        # Start the server
        server = HTTPServer((host, port), handler)
        print "Starting http server for web media requests on port " + str(port)
        server.serve_forever()

def write_log(name, url):
    '''add watched video info in log file'''
    
    log_path = __addon__.getSetting('logfile')
    if log_path != "":
        with io.open(log_path,'a', encoding='utf-8') as log:
            time = str(datetime.datetime.now())
            log.write(time+'\t'+name+'\t'+url+'\n')

    
try:
    # native youtube dl
    import youtube_dl
except ImportError:
    print "Missing youtube_dl in python path (sudo pip install youtube_dl)"
else:
    # the player to control
    web_player = xbmc.Player()
    # global queue for multithreading
    QUEUE = Queue.Queue()
    # http server to watch for requests
    httpd = server(QUEUE)
    httpd.start()
    # main loop
    flip = time.time()
    last_request = 0
    while True:
        # watch for requests and launch player
        if not QUEUE.empty():
            name, url, stream_url, t = QUEUE.get()
            # accept only last request
            if t > last_request:
                last_request = t
                # send media url to kodi player
                web_player.play(stream_url)
                # keep trace of watching activty
                write_log(name, url)
        # reload ytdl module as it may have been updated by cron
        period = 15*60
        if time.time() > flip + period:
            flip = time.time()
            youtube_dl = reload(youtube_dl)
        # sleep to preserve cpu
        time.sleep(0.5)
        
