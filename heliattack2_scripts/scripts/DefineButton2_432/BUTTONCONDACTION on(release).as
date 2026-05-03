on(release){
   jumpKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      jumpKey = Key.getCode();
      so.data.jumpKey = jumpKey;
      jumpKeyM.gotoAndStop(jumpKey);
      onKeyDown = null;
   };
}
