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
import unicodedata
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

def format_log(message):
    # Add addon name before notification
    message = '[%s] %s' % (__addonname__, message)
    # Remove or convert non ascii characters (xbmc.log doesn't support them)
    message = unicodedata.normalize('NFKD', message)
    message = message.encode('ascii', 'ignore')
    return message

class MyLogger(object):
    def debug(self, msg):
        xbmc.log(format_log(msg), xbmc.LOGNOTICE)

    def warning(self, msg):
        xbmc.log(format_log(msg), xbmc.LOGNOTICE)

    def error(self, msg):
        xbmc.log(format_log(msg), xbmc.LOGERROR)

def log(message):
    """add message to kodi log"""
    MyLogger().warning(message)

class extractor(threading.Thread):
    """deamon extracting information from a media page url
    and putting it in a queue"""
    
    def __init__(self, url, q):
        self.url = url
        self.q = q
        self.t = time.time()
        self.monitor = xbmc.Monitor() # monitor xbmc status (exiting)
        self.running = True
        threading.Thread.__init__(self)

    def run(self):
        is_playlist = False # are we dealing with a single media or a playlist page ?
        launched = False # is a media yet launched by this thread ?
        i = 1 # playlist item index
        while self.running and not self.monitor.abortRequested() and i < 200:
            ydl_opts = {
                'ignoreerrors': True,
                'logger': MyLogger(),
                'playliststart': i,
                'playlistend': i #get only next item
                }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(self.url, download=False)
                except youtube_dl.utils.DownloadError:
                    log('Youtube_dl error while streaming from '+self.url)
                    info = None
            if info != None and '_type' in info and info['_type'] == 'playlist':
                is_playlist = True
                if len(info['entries']) > 0:
                    info = info['entries'][0]
                else:
                    log('End of playlist reached at '+self.url)
                    break
            if info != None and 'url' in info:
                stream_url = info['url']
                name = info['title']+' - '+info['id']
                if not launched:
                    self.q.put(('play', name, self.url, stream_url, self.t))
                    for e in EXTLIST:
                        if e.t < self.t:
                            e.stop()
                            EXTLIST.remove(e)
                    EXTLIST.append(self)
                    if not is_playlist:
                        break
                    launched = True
                else:
                    self.q.put(('add', name, self.url, stream_url, self.t))
            i += 1
        else:
            log('Extraction aborted before end for '+self.url)

    def stop(self):
        log('Stopping extraction from '+self.url)
        self.running = False

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
            ext = extractor(url, MEDIAQUEUE)
            ext.start()
        else:
            self.send_error(404,'File Not Found: %s' % self.path)


class server(threading.Thread):
    """deamon http server for new media requests"""
    def __init__(self):
        # Interface listenning for web playing events
        self.host = ''
        self.port = int(__addon__.getSetting('port'))
        self.server = HTTPServer((self.host, self.port), handler)
        threading.Thread.__init__(self)
        
    def run(self):
        log( "Starting http server for web media requests on port " + str(self.port))
        self.server.serve_forever()

    def stop(self):
        log('Shutting down http server')
        self.server.shutdown()

def write_log(name, url):
    '''add watched video info in log file'''
    log_path = __addon__.getSetting('logfile')
    if log_path != "":
        with io.open(log_path,'a', encoding='utf-8') as log:
            time = str(datetime.datetime.now())
            log.write(time+'\t'+name+'\t'+url+'\n')

if __name__ == '__main__':
    try:
        # native youtube dl
        import youtube_dl
    except ImportError:
        log( "Missing youtube_dl in python path (sudo pip install youtube_dl)")
    else:
        # global queue for multithreading
        MEDIAQUEUE = Queue.Queue()
        EXTLIST = []
        # monitor xbmc status (exiting)
        monitor = xbmc.Monitor()
        # the player and playlist to control
        web_player = xbmc.Player()
        video_playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        # http server to watch for requests
        httpd = server()
        httpd.start()
        # main loop
        flip = time.time()
        period = 15*60  #every 15 minutes
        last_request = 0
        while not monitor.abortRequested():
            # watch for requests and launch player
            if not MEDIAQUEUE.empty():
                mode, name, url, stream_url, t = MEDIAQUEUE.get()
                #are we dealing with a single item ?
                if mode == 'play':
                    # accept only last request
                    if t > last_request:
                        last_request = t
                        # clear playlist
                        video_playlist.clear()
                        # add entry to Kodi playlist
                        listitem = xbmcgui.ListItem()
                        listitem.setLabel(name)
                        video_playlist.add(stream_url, listitem)
                        # lets play
                        web_player.play(video_playlist)
                        # keep trace of watching activty
                        write_log(name, url)
                # or a playlist item to add ? BEWARE we do not log these
                elif mode == 'add':
                    # complete only currently active playlist
                    if t == last_request:
                        # add entry to Kodi playlist
                        listitem = xbmcgui.ListItem()
                        listitem.setLabel(name)
                        video_playlist.add(stream_url, listitem)
            # reload ytdl module as it may have been updated by cron
            if time.time() > flip + period:
                flip = time.time()
                youtube_dl = reload(youtube_dl)
            # sleep to preserve cpu
            time.sleep(0.5)
        else:
            httpd.stop()
            log('Stopping service')
