on(release){
   sounds = so.data.sounds = !sounds;
   if(sounds)
   {
      sdisplay = "On";
      smusic.start(0,9999999);
   }
   else
   {
      sdisplay = "Off";
      SoundBoard.stopAll();
   }
}
