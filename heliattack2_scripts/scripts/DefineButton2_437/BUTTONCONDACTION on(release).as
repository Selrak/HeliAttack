on(release){
   pauseKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      pauseKey = Key.getCode();
      so.data.pauseKey = pauseKey;
      pauseKeyM.gotoAndStop(pauseKey);
      onKeyDown = null;
   };
}
