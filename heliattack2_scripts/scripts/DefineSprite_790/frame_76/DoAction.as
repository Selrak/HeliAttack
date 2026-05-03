mcYourScore.position = mcHighScoreData.positionMonthly;
var i = 0;
while(i < mcHighScoreData.high)
{
   this["txtUserName" + i] = mcHighScoreData["userNameMonthly" + i];
   this["txtScore" + i] = mcHighScoreData["scoreMonthly" + i];
   this["txtDate" + i] = mcHighScoreData["dateMonthly" + i];
   i++;
}
stop();
