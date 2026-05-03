soundBoard = new Object();
soundBoard.soundNum = 0;
soundBoard.soundBoardClip = createEmptyMovieClip("soundBoardClip",1024);
soundBoard.sounds = new Array();
soundBoard.newSound = function(name)
{
   var soundHolder = this.soundBoardClip.createEmptyMovieClip("SoundClip_" + this.soundNum,this.soundNum);
   var tsound;
   tsound = this.soundBoardClip["Sound_" + this.soundNum] = new Sound(soundHolder);
   tsound.attachSound(name);
   this.soundNum = this.soundNum + 1;
   this.sounds.push({name:name,tsound:tsound});
   return tsound;
};
soundBoard.stopAll = function()
{
   var i = 0;
   while(i < this.sounds.length)
   {
      this.sounds[i].tsound.stop();
      i++;
   }
};
spabomb = SoundBoard.newSound("spabomb");
spfiremines = SoundBoard.newSound("spfiremines");
spflamethrower = SoundBoard.newSound("spflamethrower");
spgrapplecannon = SoundBoard.newSound("spgrapplecannon");
spgrenadelauncher = SoundBoard.newSound("spgrenadelauncher");
sphealth = SoundBoard.newSound("sphealth");
spinvulnerability = SoundBoard.newSound("spinvulnerablilty");
spjetpack = SoundBoard.newSound("spjetpack");
spmac10 = SoundBoard.newSound("spmac10");
sppredatormode = SoundBoard.newSound("sppredatormode");
sprailgun = SoundBoard.newSound("sprailgun");
sprocketlauncher = SoundBoard.newSound("sprocketlauncher");
sprpg = SoundBoard.newSound("sprpg");
spseekerlauncher = SoundBoard.newSound("spseekerlauncher");
spshotgun = SoundBoard.newSound("spshotgun");
spshotgunrockets = SoundBoard.newSound("spshotgunrockets");
sptimerift = SoundBoard.newSound("sptimerift");
sptridamage = SoundBoard.newSound("sptridamage");
sboom = SoundBoard.newSound("sboom");
ssmallboom = SoundBoard.newSound("sboom");
ssmallboom.setVolume(50);
sheliboom = SoundBoard.newSound("sheliboom");
sbigboom = SoundBoard.newSound("sbigboom");
sflame = SoundBoard.newSound("sflame");
sgrapple = SoundBoard.newSound("sgrapple");
sgrenade = SoundBoard.newSound("sgrenade");
shurt = SoundBoard.newSound("shurt");
sgun = SoundBoard.newSound("sgun");
srailgun = SoundBoard.newSound("srailgun");
srocket = SoundBoard.newSound("srocket");
sshotgun = SoundBoard.newSound("sshotgun");
shjump = SoundBoard.newSound("shjump");
smetal0 = SoundBoard.newSound("smetal0");
smetal1 = SoundBoard.newSound("smetal1");
smetal2 = SoundBoard.newSound("smetal2");
smetal3 = SoundBoard.newSound("smetal3");
shit0 = SoundBoard.newSound("smetal0");
shit0.setVolume(75);
shit1 = SoundBoard.newSound("smetal1");
shit1.setVolume(75);
shit2 = SoundBoard.newSound("smetal2");
shit2.setVolume(75);
shit3 = SoundBoard.newSound("smetal3");
shit3.setVolume(75);
sheli = SoundBoard.newSound("sheli");
smusic = SoundBoard.newSound("smusic");
