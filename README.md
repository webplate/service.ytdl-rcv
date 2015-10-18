# Kodi addon to cast web content to Kodi.

à la Chromecast but with plenty more sites !

Install youtube_dl

    sudo pip install youtube_dl

Keep it updated

    sudo pip install --upgrade youtube_dl

Install this addon :
    - dowload as ZIP
    - use KODI install addon from zip functionnality

Customize and save the bookmarklet:

    javascript:(function(){location.href='http://KODI_IP:8282/watch?url='+location.href;})();

Then just click on it to trigger a web media request to KODI.
