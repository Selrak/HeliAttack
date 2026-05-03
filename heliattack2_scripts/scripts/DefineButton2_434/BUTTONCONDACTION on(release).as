on(release){
   switchKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      switchKey = Key.getCode();
      so.data.switchKey = switchKey;
      switchKeyM.gotoAndStop(switchKey);
      onKeyDown = null;
   };
}
