import os
import threading
import datetime
# server module
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# kodi module
import xbmc
import xbmcaddon
# youtube-dl control
import YDStreamUtils
import YDStreamExtractor
import YoutubeDLWrapper
from YoutubeDLWrapper import youtube_dl


__addon__       = xbmcaddon.Addon(id='plugin.service.youtube-dl-rcv')
__addonname__   = __addon__.getAddonInfo('name')
__icon__        = __addon__.getAddonInfo('icon')

def build_name(info,path="",template='%(title)s-%(id)s.%(ext)s'):
    """
    Download the selected video in vidinfo to path.
    Template sets the youtube-dl format which defaults to TITLE-ID.EXT.
    """
    # build name
    info = YDStreamExtractor._convertInfo(info) #Get the right format
    try:
        YDStreamExtractor._completeInfo(info) #Make sure we have the needed bits
    except TypeError:
        print 'STRANGE ERROR FROM YOUTUBE DL CONTROL WHEN TRYING TO COMPLETE VIDEO INFO'
    path_template = os.path.join(path,template)
    ytdl = YoutubeDLWrapper._getYTDL()
    ytdl.params['quiet'] = True
    ytdl.params['outtmpl'] = path_template    
    name = ytdl.prepare_filename(info)
    name = name.encode('utf8')
    return name

def play(url):
    '''play media in given page url'''
    # get parameters
    quality = __addon__.getSetting('quality')
    qualities = {'SD': 0, '720p': 1, '1080p': 2} 
    quality = qualities[quality]

    # build media representation from url
    info = YDStreamExtractor.getVideoInfo(url,quality=quality)
    if info is None:
        return False
    
    name = build_name(info)
    stream_url = info.streamURL()

    web_player = xbmc.Player()
    print 'LAUNCHING DISTANT VIDEO', name
    web_player.play(stream_url)
    
    #keep trace of watching activty
    write_log(name, url)
    
    return True

def write_log(name, url):
    '''add watched video info in lof file'''
    log_path = __addon__.getSetting('logfile')
    if log_path != "":
        with open(log_path,'a') as log:
            time = str(datetime.datetime.now())
            log.write(time+'\t'+name+'\t'+url+'\n')

class MyHandler(BaseHTTPRequestHandler):
    '''simple server to get watching requests'''
    def do_GET(self):
        # if receiving watch instruction
        if self.path.startswith('/watch?url='):
            url = self.path[11:]
            
            # send http response
            self.send_response(200)
            self.send_header('Content-type',	'text/html')
            self.end_headers()
            self.wfile.write("""<html>
            <head>
            <title>""" + url + """</title>
            </head>
            <body>
            Trying to play """ + url + """ ...</body>
            </html>""")
            
            # try and dl media at url
            play(url)
        else:
            self.send_error(404,'File Not Found: %s' % self.path)

# Interface listenning for web playing events
host = ''
port = int(__addon__.getSetting('port'))
# Start the server
server = HTTPServer((host, port), MyHandler)
print "Starting http server for web media requests on port " + str(port)
server.serve_forever()

#~ url = "http://www.youtube.com/watch?v=_yVv9dx88x0"
#~ url = "http://www.dailymotion.com/video/x29ejto_master-of-the-universe-replay_shortfilms"
#~ url = "http://www.dailymotion.com/video/x2j23bs_watermelon-in-30-seconds-or-less_lifestyle"
