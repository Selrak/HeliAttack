on(release){
   bullettimeKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      bullettimeKey = Key.getCode();
      so.data.bullettimeKey = bullettimeKey;
      bullettimeKeyM.gotoAndStop(bullettimeKey);
      onKeyDown = null;
   };
}
