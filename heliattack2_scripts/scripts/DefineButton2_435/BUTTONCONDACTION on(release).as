on(release){
   boostKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      boostKey = Key.getCode();
      so.data.boostKey = boostKey;
      boostKeyM.gotoAndStop(boostKey);
      onKeyDown = null;
   };
}
