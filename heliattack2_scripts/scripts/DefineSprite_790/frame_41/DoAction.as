if(!dailyTabClicked)
{
   mcYourScore.position = position;
   dailyTabClicked = true;
}
mcYourScore.position = mcHighScoreData.positionDaily;
var i = 0;
while(i < mcHighScoreData.high)
{
   this["txtUserName" + i] = mcHighScoreData["userNameDaily" + i];
   this["txtScore" + i] = mcHighScoreData["scoreDaily" + i];
   this["txtDate" + i] = mcHighScoreData["dateDaily" + i];
   i++;
}
stop();
