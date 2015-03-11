import os
import threading
import time
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



# called by each thread
def blocking_dl(downloader, name, info):
    result = downloader.download(name, info)
    return result

def build_name(info,path,template='%(title)s-%(id)s.%(ext)s'):
    """
    Download the selected video in vidinfo to path.
    Template sets the youtube-dl format which defaults to TITLE-ID.EXT.
    """
    ytdl = YoutubeDLWrapper._getYTDL()
    
    # build name
    info = YDStreamExtractor._convertInfo(info) #Get the right format
    try:
        YDStreamExtractor._completeInfo(info) #Make sure we have the needed bits
    except TypeError:
        print 'STRANGE ERROR FROM YOUTUBE DL CONTROL WHEN TRYING TO COMPLETE VIDEO INFO'
    path_template = os.path.join(path,template)
    ytdl.params['quiet'] = True
    ytdl.params['outtmpl'] = path_template    
    name = ytdl.prepare_filename(info)
    return name
    

def launch_download(info, ytdl):
    fd = youtube_dl.downloader.get_suitable_downloader(info)(ytdl, ytdl.params)

    t = threading.Thread(target=blocking_dl, args = (fd, name, info))
    t.start()

    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%("Downloading", name, 5000, __icon__))

def play(url):
    print '########################################################################################################'
    info = YDStreamExtractor.getVideoInfo(url,quality=quality)
    if info is None:
        return False
    
    print 'INFO', info
    name = build_name(info, save_path)
    print 'NAME',name
    print 'CACHE',make_cache


    # Should we cache ?
    if make_cache:
        # check if already downloaded
        if os.path.exists(name):
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%("Local", ":)", 1000, __icon__))
            no_dl = True
        else:
            no_dl = False
            launch_download(info, ytdl)
            name = name + '.part'
    else:
        no_dl = True
        name = info.streamURL()

    if not no_dl:
        # wait to buffer
        time.sleep(delay)

    # check if dowload finished
    short_name = name[:-5]
    if not os.path.exists(name) and os.path.exists(short_name):
        print "DL ALREADY FINISHED"
        # get rid of extension
        name = short_name
    print 'OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO'

    web_player = xbmc.Player()
    if make_cache:
        if os.path.exists(name):
            # insist on playing
            for i in range(10):
                if web_player.isPlaying():
                    played = web_player.getPlayingFile()
                else:
                    played = None
                print played, name
                if played != name:
                    print 'LAUNCHING LOCAL VIDEO'
                    web_player.play(name)
                time.sleep(2)
    else:
        print 'LAUNCHING DISTANT VIDEO'
        web_player.play(name)
    return True

class MyHandler(BaseHTTPRequestHandler):

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
            <title>Success</title>
            </head>
            <body>
            Trying to play """ + url + """ ...</body>
            </html>""")
            
            # try and dl media at url
            play(url)
            return
                
        else:
            self.send_error(404,'File Not Found: %s' % self.path)


caching = __addon__.getSetting('caching')
if caching == 'true':
    make_cache = True
else:
    make_cache = False

# Interface listenning for web playing events
host = ''
port = int(__addon__.getSetting('port'))

quality = __addon__.getSetting('quality')
qualities = {'SD': 0, '720p': 1, '1080p': 2} 
quality = qualities[quality]

delay = float(__addon__.getSetting('delay'))

save_path = __addon__.getSetting('save_path')

# Start the server
server = HTTPServer((host, port), MyHandler)
print "Starting http server for web media requests."
server.serve_forever()

#~ url = "http://www.youtube.com/watch?v=_yVv9dx88x0"
#~ url = "http://www.dailymotion.com/video/x29ejto_master-of-the-universe-replay_shortfilms"
#~ url = "http://www.dailymotion.com/video/x2j23bs_watermelon-in-30-seconds-or-less_lifestyle"
