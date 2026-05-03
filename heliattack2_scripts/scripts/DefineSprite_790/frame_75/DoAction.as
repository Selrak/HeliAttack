if(mcHighScoreData.records > 0)
{
   mcHighScoreData.positionMonthly = mcHighScoreData.position;
   monthlyLoaded = true;
   var i = 0;
   while(i < mcHighScoreData.high)
   {
      mcHighScoreData["userNameMonthly" + i] = mcHighScoreData["user_name" + i];
      mcHighScoreData["scoreMonthly" + i] = mcHighScoreData["score" + i];
      mcHighScoreData["dateMonthly" + i] = mcHighScoreData["date" + i];
      i++;
   }
   play();
}
else
{
   gotoAndPlay(_currentframe - 1);
}
