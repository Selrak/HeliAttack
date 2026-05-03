on(release){
   soundKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      soundKey = Key.getCode();
      so.data.soundKey = soundKey;
      soundKeyM.gotoAndStop(soundKey);
      onKeyDown = null;
   };
}
