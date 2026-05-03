if(getTimer() > timeOut)
{
   timeOut = getTimer() + timeOutVal;
   completed = false;
   gotoAndPlay(20);
}
else if(mcHighScoreData.records > 0)
{
   mcHighScoreData.positionDaily = mcHighScoreData.position;
   var i = 0;
   while(i < mcHighScoreData.high)
   {
      mcHighScoreData["userNameDaily" + i] = mcHighScoreData["user_name" + i];
      mcHighScoreData["scoreDaily" + i] = mcHighScoreData["score" + i];
      mcHighScoreData["dateDaily" + i] = mcHighScoreData["date" + i];
      i++;
   }
   gotoAndPlay(34);
}
else
{
   gotoAndPlay(_currentframe - 1);
}
