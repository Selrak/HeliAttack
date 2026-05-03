_quality = "low";
so = SharedObject.getlocal("heliattack");
if(so.data.highscore != undefined)
{
   sounds = so.data.sounds;
   counter = so.data.counter++;
   games = so.data.games;
   ts = so.data.totalscore;
   hs = so.data.highscore;
   hssent = so.data.highscoresent;
   name = so.data.name;
   tshots = so.data.totalshots;
   thits = so.data.totalhits;
   ttime = so.data.totaltime;
   besttime = so.data.besttime;
   worsttime = so.data.worsttime;
   thelis = so.data.totalhelis;
   bhelis = so.data.besthelis;
   thjumps = so.data.totalhjumps;
   tbtime = so.data.totalbtime;
   jumpkey = so.data.jumpKey;
   leftkey = so.data.leftKey;
   rightkey = so.data.rightKey;
   duckkey = so.data.duckKey;
   boostKey = so.data.boostKey;
   bulletTimeKey = so.data.bulletTimeKey;
   switchKey = so.data.switchKey;
   pauseKey = so.data.pauseKey;
   suicideKey = so.data.suicideKey;
   soundKey = so.data.soundKey;
}
else
{
   sounds = so.data.sounds = 1;
   counter = so.data.counter = 1;
   games = so.data.games = 0;
   hs = so.data.highscore = 0;
   ts = so.data.totalscore = 0;
   hssent = so.data.highscoresent = 0;
   name = so.data.name = "";
   tshots = so.data.totalshots = 0;
   thits = so.data.totalhits = 0;
   ttime = so.data.totaltime = 0;
   thelis = so.data.totalhelis = 0;
   bhelis = so.data.besthelis = 0;
   so.data.tweapon = new Array();
   besttime = so.data.besttime = 0;
   worsttime = so.data.worsttime = Infinity;
   thjumps = so.data.totalhjumps = 0;
   tbtime = so.data.totalbtime = 0;
   jumpkey = so.data.jumpKey = 38;
   leftkey = so.data.leftKey = 37;
   rightkey = so.data.rightKey = 39;
   duckkey = so.data.duckKey = 40;
   boostKey = so.data.boostKey = 17;
   bulletTimeKey = so.data.bulletTimeKey = 16;
   switchKey = so.data.switchKey = 35;
   pauseKey = so.data.pauseKey = 80;
   suicideKey = so.data.suicideKey = 75;
   soundKey = so.data.soundKey = 83;
}
if(sounds)
{
   smusic.start(0,9999999);
}
