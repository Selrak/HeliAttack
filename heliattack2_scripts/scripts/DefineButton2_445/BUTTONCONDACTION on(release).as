on(release){
   leftKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      leftKey = Key.getCode();
      so.data.leftKey = leftKey;
      leftKeyM.gotoAndStop(leftKey);
      onKeyDown = null;
   };
}
