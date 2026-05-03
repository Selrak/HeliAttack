on(release){
   rightKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      rightKey = Key.getCode();
      so.data.rightKey = rightKey;
      rightKeyM.gotoAndStop(rightKey);
      onKeyDown = null;
   };
}
