if(!weeklyTabClicked or !weeklyLoaded)
{
   getHighScores(1,mcHighScoreData);
   weeklyTabClicked = true;
}
else if(weeklyLoaded)
{
   gotoAndPlay(56);
}
