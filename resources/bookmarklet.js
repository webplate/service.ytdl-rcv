javascript:(function(){
    var target_url;
    target_url=document.URL;
    target_url="http://127.0.0.1:8282/watch?url=" + target_url;
    window.open(target_url);
})();
