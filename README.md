# Kodi addon to cast web content to the media center.

à la Chromecast but supporting plenty more sites !

Install youtube_dl on the KODI machine:

    sudo pip install youtube_dl

Keep it updated:

    sudo pip install --upgrade youtube_dl

Install this addon :
- dowload as ZIP
- use KODI install addon from zip functionnality

Customize and save the bookmarklet on the clients:

    javascript:(function(){location.href='http://KODI_IP:8282/watch?url='+location.href;})();

Then, when visiting a web page with a media, just click on the bookmarklet to trigger a request to KODI.
