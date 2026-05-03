function getHighScores(period, target)
{
   target.records = 0;
   if(saveScore)
   {
      target.score = localScore;
      target.username = txtUsername;
      target.notSentScore = localScore;
      target.notSentUsername = txtUsername;
   }
   target.gamename = gamename;
   target.low = 0;
   target.high = 10;
   target.formaction = "gethighscores";
   target.dwm = period;
   var preventCaching = getTimer() + random(100);
   target.loadVariables("http://www.miniclip.com/Flash/proxy.php?preventCashing=" + preventCaching,"GET");
   play();
}
function sendHighScore()
{
   if(txtUsername != "" && txtUsername != undefined)
   {
      getHighScores(2,mcHighScoreData);
   }
}
this.username = "";
this.score = 0;
position_d = 0;
position_w = 0;
position_m = 0;
mcHighScoreData.records = 0;
dailyLoaded = false;
weeklyLoaded = false;
monthlyLoaded = false;
dailyTabClicked = false;
weeklyTabClicked = false;
monthlyTabClicked = false;
timeOutVal = 30000;
completed = "false";
localScore = int(eval(scoreLocation));
this._x = int(this._x);
this._y = int(this._y);
if(gameName == undefined)
{
   trace("MINICLIP.COM HIGHSCORE COMPONENT WARNING");
   trace("========================================");
   trace("The \'gameName\' parameter has not been set. This parameter");
   trace("needs to be set for the highscore component to function.");
   error = true;
}
if(eval(scoreLocation) == undefined && saveScore)
{
   trace("MINICLIP.COM HIGHSCORE COMPONENT WARNING");
   trace("========================================");
   trace("The \'scoreLocation\' parameter does not contain any data.");
   trace("This parameter needs to be pointing to the game score variable");
   trace("set for the highscore component to function.");
   error = true;
}
if(error == true)
{
   _parent.stop();
   stop();
}
else if(saveScore && eval(scoreLocation) > 0)
{
   gotoAndPlay(2);
}
else
{
   getHighScores(2,mcHighScoreData);
   gotoAndPlay(15);
}
