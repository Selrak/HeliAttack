on(release){
   suicideKeyM.gotoAndStop(200);
   Key.addListener(this);
   onKeyDown = function()
   {
      suicideKey = Key.getCode();
      so.data.suicideKey = suicideKey;
      suicideKeyM.gotoAndStop(suicideKey);
      onKeyDown = null;
   };
}
