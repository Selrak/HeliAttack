on(release){
   duckKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      duckKey = Key.getCode();
      so.data.duckKey = duckKey;
      duckKeyM.gotoAndStop(duckKey);
      onKeyDown = null;
   };
}
