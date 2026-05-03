on(release){
   counter = so.data.counter = 1;
   games = so.data.games = 0;
   hs = so.data.highscore = 0;
   ts = so.data.totalscore = 0;
   hssent = so.data.highscoresent = 0;
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
   var temp = attachMovie("stats","stats",32);
   temp.gotoAndStop(2);
   temp._x = 65;
   temp._y = 24;
   temp.highscore = Math.floor(hs) * 100;
   temp.counter = counter;
   temp.games = games;
   temp.score = Math.floor(ts) * 100;
   temp.time = Math.floor(ttime / 30) + " seconds";
   temp.bhelis = bhelis;
   if(besttime == 0)
   {
      temp.besttime = "None";
   }
   else
   {
      temp.besttime = Math.floor(besttime / 30) + " seconds";
   }
   if(worsttime == Infinity)
   {
      temp.worsttime = "None";
   }
   else
   {
      temp.worsttime = Math.floor(worsttime / 30) + " seconds";
   }
   temp.shots = tshots;
   temp.hits = thits;
   if(tshots > 0)
   {
      temp.accuracy = Math.floor(thits / tshots * 100) + "%";
   }
   else
   {
      temp.accuracy = "0%";
   }
   var maxi = 0;
   var maxs = -Infinity;
   var i = 1;
   while(i < so.data.tweapon.length)
   {
      if(so.data.tweapon[i] > maxs)
      {
         maxs = so.data.tweapon[i];
         maxi = i;
      }
      i++;
   }
   if(maxs <= 0)
   {
      maxi = 0;
   }
   if(so.data.tweapon[maxi] != 0 && so.data.tweapon[maxi] != undefined)
   {
      temp.weapon = guns[maxi].name;
   }
   else
   {
      temp.weapon = "None";
   }
   temp.helis = thelis;
   temp.hjumps = thjumps;
   temp.btime = Math.floor(tbtime / 30) + " seconds";
   temp.label = "Click for main menu";
   temp.onRelease = function()
   {
      this.removeMovieClip("");
      gotoAndStop(20);
   };
}
