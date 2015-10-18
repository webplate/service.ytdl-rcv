# Kodi addon to cast web content to Kodi.

à la Chromecast but with plenty more sites !

Install youtube_dl

    sudo pip install youtube_dl

Keep it updated

    sudo pip install --upgrade youtube_dl

And just customize and save the bookmarklet:
    
    javascript:(function(){window.open("http://KODI_SERVER_IP:8282/watch?url="+document.URL);})();
