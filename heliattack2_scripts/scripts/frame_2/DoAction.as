location = "http://www.miniclip.com/";
if(this._url.indexOf(location) != 0 && this._url.indexOf("file://") != 0)
{
   gotoAndPlay(_currentframe - 1);
}
if(getBytesLoaded() >= getBytesTotal())
{
   gotoAndStop(15);
}
