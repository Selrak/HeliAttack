if(!monthlyTabClicked or !monthlyLoaded)
{
   getHighscores(0,mcHighScoreData);
   monthlyTabClicked = true;
}
else if(monthlyLoaded)
{
   gotoAndPlay(76);
}
