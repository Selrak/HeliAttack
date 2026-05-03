mcYourScore.position = mcHighScoreData.positionWeekly;
var i = 0;
while(i < mcHighScoreData.high)
{
   this["txtUserName" + i] = mcHighScoreData["userNameWeekly" + i];
   this["txtScore" + i] = mcHighScoreData["scoreWeekly" + i];
   this["txtDate" + i] = mcHighScoreData["dateWeekly" + i];
   i++;
}
stop();
