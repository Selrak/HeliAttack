l = Math.floor(getBytesLoaded() / getBytesTotal() * 100);
lb._xscale = l;
l = "Loading " + l + "%...";
if(getBytesLoaded() < getBytesTotal())
{
   gotoAndPlay(_currentframe - 1);
}
else
{
   delete l;
   gotoAndStop(15);
}
