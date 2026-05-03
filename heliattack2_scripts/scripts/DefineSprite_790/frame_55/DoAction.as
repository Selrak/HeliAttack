if(mcHighScoreData.records > 0)
{
   mcHighScoreData.positionWeekly = mcHighScoreData.position;
   weeklyLoaded = true;
   var i = 0;
   while(i < mcHighScoreData.high)
   {
      mcHighScoreData["userNameWeekly" + i] = mcHighScoreData["user_name" + i];
      mcHighScoreData["scoreWeekly" + i] = mcHighScoreData["score" + i];
      mcHighScoreData["dateWeekly" + i] = mcHighScoreData["date" + i];
      i++;
   }
   gotoAndPlay(56);
}
else
{
   gotoAndPlay(_currentframe - 1);
}
