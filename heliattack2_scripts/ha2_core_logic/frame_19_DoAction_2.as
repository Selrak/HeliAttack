function copyArray(arr, w, h)
{
   var tmp = new Array();
   var y = 0;
   while(y < height)
   {
      tmp[y] = new Array();
      var x = 0;
      while(x < width)
      {
         tmp[y][x] = new Array();
         tmp[y][x][0] = arr[y][x][0];
         tmp[y][x][1] = arr[y][x][1];
         x++;
      }
      y++;
   }
   return tmp;
}
function drawMap(arr, clipname, depth, tileset, realmap)
{
   if(realmap)
   {
      width = arr[0].length;
      height = arr.length;
      map = copyArray(arr,width,height);
   }
   var startx;
   var starty;
   var holder = createEmptyMovieClip(clipname,depth);
   var y = 0;
   while(y < sth + 1)
   {
      var x = 0;
      while(x < stw + 1)
      {
         var temp = holder.attachMovie(tileset,"tile_" + y + "_" + x,y * width + x);
         temp._y = y * tileHeight - 1;
         temp._x = x * tileWidth - 1;
         temp.gotoAndStop(arr[y][x][1] + 1);
         x++;
      }
      y++;
   }
   if(realmap)
   {
      holder.entityDepth = width * height * 2;
      temp = holder.attachMovie("hero","hero",holder.entityDepth++);
      temp.action = heroStart;
      temp.setup = heroSetup;
      temp.setup();
      player = temp;
      assignents();
   }
   return holder;
}
function assignents()
{
   var y = 0;
   while(y < height)
   {
      var x = 0;
      while(x < width)
      {
         if(map[y][x][0] == 32)
         {
            map[y][x][0] = 0;
            player._x = x * tileWidth + tileWidth / 2;
         }
         x++;
      }
      y++;
   }
   player._y = -50;
}
function getWorldPos(clip, pos, xscroll, yscroll)
{
   if(xscroll)
   {
      pos[0] = Math.floor((- clip._x) / tileWidth);
   }
   if(yscroll)
   {
      pos[1] = Math.floor((- clip._y) / tileHeight);
   }
}
function scrollMap(clip, arr, pos, bounds, xscroll, yscroll, hold)
{
   if(hold)
   {
      if(clip._x < (- (arr[0].length - stw)) * tileWidth)
      {
         clip._x = (- (arr[0].length - stw)) * tileWidth;
      }
      if(clip._x > 0)
      {
         clip._x = 0;
      }
      if(clip._y < (- (arr.length - sth)) * tileHeight)
      {
         clip._y = (- (arr.length - sth)) * tileHeight;
      }
      if(clip._y > 0)
      {
         clip._y = 0;
      }
   }
   var oldpos = new Array(pos[0],pos[1]);
   getWorldPos(clip,pos,xscroll,yscroll);
   if(xscroll)
   {
      if(oldpos[0] != pos[0])
      {
         if(oldpos[0] < pos[0])
         {
            while(oldpos[0] != pos[0])
            {
               var dy = bounds[1];
               var ty = oldpos[1];
               var ly = 0;
               while(ly < sth + 1)
               {
                  clip["tile_" + dy + "_" + bounds[0]]._x += (stw + 1) * tileWidth;
                  clip["tile_" + dy + "_" + bounds[0]].gotoAndStop(arr[ty][oldpos[0] + stw + 1][1] + 1);
                  dy++;
                  if(dy > sth)
                  {
                     dy = 0;
                  }
                  ty++;
                  ly++;
               }
               oldpos[0] = oldpos[0] + 1;
               bounds[0] = bounds[0] + 1;
               if(bounds[0] > stw)
               {
                  bounds[0] = 0;
               }
            }
         }
         else
         {
            while(oldpos[0] != pos[0])
            {
               var dl = bounds[0] - 1;
               if(dl < 0)
               {
                  dl = stw;
               }
               var dy = bounds[1];
               var ty = oldpos[1];
               var ly = 0;
               while(ly < sth + 1)
               {
                  clip["tile_" + dy + "_" + dl]._x -= (stw + 1) * tileWidth;
                  clip["tile_" + dy + "_" + dl].gotoAndStop(arr[ty][oldpos[0] - 1][1] + 1);
                  dy++;
                  if(dy > sth)
                  {
                     dy = 0;
                  }
                  ty++;
                  ly++;
               }
               oldpos[0]--;
               bounds[0]--;
               if(bounds[0] < 0)
               {
                  bounds[0] = stw;
               }
            }
         }
      }
   }
   if(yscroll)
   {
      if(oldpos[1] != pos[1])
      {
         if(oldpos[1] < pos[1])
         {
            while(oldpos[1] != pos[1])
            {
               var dx = bounds[0];
               var tx = oldpos[0];
               var lx = 0;
               while(lx < stw + 1)
               {
                  clip["tile_" + bounds[1] + "_" + dx]._y += (sth + 1) * tileWidth;
                  clip["tile_" + bounds[1] + "_" + dx].gotoAndStop(arr[oldpos[1] + sth + 1][tx][1] + 1);
                  dx++;
                  if(dx > stw)
                  {
                     dx = 0;
                  }
                  tx++;
                  lx++;
               }
               oldpos[1] = oldpos[1] + 1;
               bounds[1] = bounds[1] + 1;
               if(bounds[1] > sth)
               {
                  bounds[1] = 0;
               }
            }
         }
         else
         {
            while(oldpos[1] != pos[1])
            {
               var dl = bounds[1] - 1;
               if(dl < 0)
               {
                  dl = sth;
               }
               var dx = bounds[0];
               var tx = oldpos[0];
               var lx = 0;
               while(lx < stw + 1)
               {
                  clip["tile_" + dl + "_" + dx]._y -= (sth + 1) * tileWidth;
                  clip["tile_" + dl + "_" + dx].gotoAndStop(arr[oldpos[1] - 1][tx][1] + 1);
                  dx++;
                  if(dx > stw)
                  {
                     dx = 0;
                  }
                  tx++;
                  lx++;
               }
               oldpos[1]--;
               bounds[1]--;
               if(bounds[1] < 0)
               {
                  bounds[1] = sth;
               }
            }
         }
      }
   }
}
function bulletFrame(timeStep)
{
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         if(shit++ % 2 && sounds)
         {
            var r = random(4);
            _root["shit" + r].start(0,0);
         }
         break;
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function animationFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      if(this.pause-- <= 0)
      {
         this.nextFrame();
         if(this._currentframe == this._totalframes)
         {
            var i = 0;
            while(i < entityArray.length)
            {
               if(entityArray[i] == this)
               {
                  entityArray.splice(i,1);
                  break;
               }
               i++;
            }
            rem = 1;
            this.removeMovieClip();
         }
         this.stepc -= 1;
      }
   }
}
function distance(x1, y1, x2, y2)
{
   x = x1 - x2;
   y = y1 - y2;
   return Math.sqrt(x * x + y * y);
}
function popupFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc >= 1)
   {
      this._y--;
      this.frame = this.frame + 1;
      if(this.frame > 32)
      {
         this._alpha -= 10;
         if(this._alpha <= 0)
         {
            var i = 0;
            while(i < entityArray.length)
            {
               if(entityArray[i] == this)
               {
                  entityArray.splice(i,1);
                  break;
               }
               i++;
            }
            rem = 1;
            this.removeMovieClip();
         }
         this.stepc--;
      }
   }
}
function powerupFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(this.fall)
      {
         this.yspeed = this.yspeed + 1;
      }
      else
      {
         this.yspeed = 2;
      }
      this.stepc -= 1;
      if(this.randomed)
      {
         if(this.power._currentframe < this.power._totalframes)
         {
            this.power.nextFrame();
         }
         else
         {
            this.power.gotoAndStop(2);
         }
      }
   }
   var y = Math.floor((this._y + this.power._height / 2) / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(!this.stopped)
   {
      this._y += this.yspeed * timeStep;
      if(this.fall)
      {
         this.chute._xscale -= 10 * timeStep;
         if(this.chute._xscale < 0)
         {
            this.chute._xscale = 0;
            this.chute._visible = 0;
         }
         if(map[y][x][0] != 0)
         {
            if(this.yspeed < 4)
            {
               this._y = y * tileHeight - this.power._height / 2 + 2;
               this.stopped = 1;
            }
            else
            {
               this._y = y * tileHeight - this.power._height / 2 - 2;
               this.yspeed *= -0.25;
               this._y += this.yspeed * timeStep;
            }
         }
      }
      else
      {
         this.chute._xscale += 10 * timeStep;
         if(this.chute._xscale > 100)
         {
            this.chute._xscale = 100;
         }
         if(map[Math.floor((this._y + 150) / tileWidth)][x][0] != 0)
         {
            this.fall = 1;
         }
      }
   }
   else
   {
      this.time = this.time + 1;
   }
   if(x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      this._visible = 0;
   }
   else
   {
      this._visible = 1;
   }
   if(player.hitTest(this.power))
   {
      this.remove = 1;
      var temp = world.attachMovie("popup","popup_" + world.entityDepth,world.entityDepth++);
      temp._x = Math.floor(player._x + player.width / 2 - temp._width / 2);
      temp._y = Math.floor(player._y - temp._height * 2);
      temp.action = popupFrame;
      entityArray.push(temp);
      if(this.power._currentframe == 1)
      {
         player.health = Math.min(100,player.health += 20);
         temp.text = "Health";
         if(sounds)
         {
            sphealth.start(0,0);
         }
      }
      else
      {
         var gun = this.power._currentframe - 1;
         var bullets = 0;
         if(gun == 1)
         {
            if(sounds)
            {
               spmac10.start(0,0);
            }
            bullets = 50;
         }
         else if(gun == 2)
         {
            if(sounds)
            {
               spshotgun.start(0,0);
            }
            bullets = 14;
         }
         else if(gun == 3)
         {
            if(sounds)
            {
               spshotgunrockets.start(0,0);
            }
            bullets = 8;
         }
         else if(gun == 4)
         {
            if(sounds)
            {
               spgrenadelauncher.start(0,0);
            }
            bullets = 12;
         }
         else if(gun == 5)
         {
            if(sounds)
            {
               sprpg.start(0,0);
            }
            bullets = 10;
         }
         else if(gun == 6)
         {
            if(sounds)
            {
               sprocketlauncher.start(0,0);
            }
            bullets = 8;
         }
         else if(gun == 7)
         {
            if(sounds)
            {
               spseekerlauncher.start(0,0);
            }
            bullets = 6;
         }
         else if(gun == 8)
         {
            if(sounds)
            {
               spflamethrower.start(0,0);
            }
            bullets = 150;
         }
         else if(gun == 9)
         {
            if(sounds)
            {
               spfiremines.start(0,0);
            }
            bullets = 3;
         }
         else if(gun == 10)
         {
            if(sounds)
            {
               spabomb.start(0,0);
            }
            bullets = 2;
         }
         else if(gun == 11)
         {
            if(sounds)
            {
               sprailgun.start(0,0);
            }
            bullets = 3;
         }
         else if(gun == 12)
         {
            if(sounds)
            {
               spgrapplecannon.start(0,0);
            }
            bullets = 2;
         }
         else if(gun == 13)
         {
            var p = 1 + random(5);
            player.powerupOn = p;
            player.powerupTime = powerupTime;
            if(p == 1)
            {
               temp.text = "TriDamage";
               HUD.powerup.text = "TriDamage";
               if(sounds)
               {
                  sptridamage.start(0,0);
               }
            }
            else if(p == 2)
            {
               temp.text = "Invulnerability";
               HUD.powerup.text = "Invulnerability";
               if(sounds)
               {
                  spinvulnerability.start(0,0);
               }
            }
            else if(p == 3)
            {
               temp.text = "PredatorMode";
               HUD.powerup.text = "PredatorMode";
               player.guns[player.guns.length - 1].reloadtime = Infinity;
               if(sounds)
               {
                  sppredatormode.start(0,0);
               }
            }
            else if(p == 4)
            {
               temp.text = "TimeRift";
               HUD.powerup.text = "TimeRift";
               if(sounds)
               {
                  sptimerift.start(0,0);
               }
            }
            else if(p == 5)
            {
               temp.text = "Jetpack";
               HUD.powerup.text = "Jetpack";
               if(sounds)
               {
                  spjetpack.start(0,0);
               }
            }
         }
         if(gun < 13)
         {
            temp.text = guns[gun].name;
            player.guns[gun].bullets += bullets;
         }
      }
   }
   if(this.time > 450)
   {
      this._alpha -= 2;
   }
   if(this.remove || this.time >= 500)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function seekerFrame(timeStep)
{
   this.stepc += timeStep;
   var move = 0;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(!(this.r % 2))
      {
         var temp = world.attachMovie("smoke","smoke_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
      }
      this.stepc -= 1;
      move = 1;
   }
   if(this.target = null)
   {
      this._x += this.xspeed * timeStep;
      this._y += this.yspeed * timeStep;
   }
   else
   {
      var rotd = 360 - Math.atan2(this._x - this.targets._x,this._y - this.targets._y) * 180 / 3.141592653589793 - 90;
      var rotn = this._rotation;
      rotd = (rotd + 360) % 360;
      rotn = (rotn + 360) % 360;
      var dif = rotd - rotn;
      dif = dif <= 179 ? dif : -360 + dif;
      dif = dif >= -179 ? dif : 360 + dif;
      this._rotation += dif / 15 * timeStep;
      this.xspeed = this.sped * Math.cos(this._rotation * 3.141592653589793 / 180);
      this.yspeed = this.sped * Math.sin(this._rotation * 3.141592653589793 / 180);
      this._x += this.xspeed * timeStep;
      this._y += this.yspeed * timeStep;
   }
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var closest = Infinity;
   this.targets = null;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      var d = distance(this._x,this._y,enemyArray[i]._x,enemyArray[i]._y);
      if(d < closest)
      {
         closest = d;
         this.targets = enemyArray[i];
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || map[y][x][0] != 0)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 100)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 100;
            player.xspeed += int(mult * 12 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 32 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function aBombFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(!(this.r % 4))
      {
         var temp = world.attachMovie("flame","flame_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
      }
      this.stepc -= 1;
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || map[y][x][0] != 0)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp._xscale = temp._yscale = 800;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 300)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 300;
            player.xspeed += int(mult * 24 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 64 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sbigboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function smallrocketFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(!(this.r % 4))
      {
         var temp = world.attachMovie("smoke","smoke_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
      }
      this.stepc -= 1;
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || map[y][x][0] != 0)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp._xscale = temp._yscale = 50;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 50)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 50;
            player.xspeed += int(mult * 6 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 12 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            ssmallboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function rpgFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.activate = this.activate + 1;
      if(this.activate == 3)
      {
         if(sounds)
         {
            srocket.start(0,0);
         }
      }
      if(this.activate > 3 && this.activate < 7)
      {
         this.xspeed *= 2;
         this.yspeed *= 2;
      }
      if(this.activate > 2)
      {
         this.r = this.r + 1;
         if(!(this.r % 1))
         {
            var temp = world.attachMovie("smoke","smoke_" + world.entityDepth,world.entityDepth++);
            temp._x = this._x;
            temp._y = this._y;
            temp.stop();
            temp.action = animationFrame;
            entityArray.push(temp);
         }
      }
      this.stepc -= 1;
   }
   this._rotation += this.xspeed * timeStep * 4;
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || map[y][x][0] != 0)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 100)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 100;
            player.xspeed += int(mult * 9 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 24 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function rocketFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(!(this.r % 2))
      {
         var temp = world.attachMovie("smoke","smoke_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
      }
      this.stepc -= 1;
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || map[y][x][0] != 0)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 100)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 100;
            player.xspeed += int(mult * 12 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 32 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function grappleAttached(timeStep)
{
   if(this.attached._x == undefined)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
   this._x = this.attached._x + this.offsetx;
   this._y = this.attached._y + this.offsety;
   this.clear();
   this.lineStyle(2,0,100);
   this.lineTo(player._x + player.width / 2 - this._x,player._y + player.height / 2 - this._y);
}
function grappleFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      this.stepc -= 1;
   }
   if(this._rotation != 0)
   {
      this.gfx._rotation = this._rotation;
      this._rotation = 0;
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].action = heliFall;
         this.attached = enemyArray[i];
         this.offsetx = this._x - enemyArray[i]._x;
         this.offsety = this._y - enemyArray[i]._y;
         this.action = grappleAttached;
         entityArray.push(enemyArray[i]);
         enemyArray.splice(i,1);
         helis++;
         rthelis++;
         if(helis == 3)
         {
            var temp = world.attachMovie("powerup","powerup_" + world.entityDepth,world.entityDepth++);
            temp._x = this._x;
            temp._y = this._y;
            temp.chute._xscale = 0;
            if(rthelis >= nextHealth)
            {
               nextHealth *= 2;
               temp.power.gotoAndStop(1);
            }
            else
            {
               if(random(100) % 32 == 0)
               {
                  temp.randomed = 1;
               }
               temp.power.gotoAndStop(random(temp.power._totalframes - 1) + 2);
            }
            temp.action = powerupFrame;
            entityArray.push(temp);
            helis = 0;
         }
         var i = 0;
         while(i < 2)
         {
            var temp = world.attachMovie("Shard","Shard_" + world.entityDepth,world.entityDepth++);
            temp._x = this._x;
            temp._y = this._y;
            temp._rotation = random(360);
            temp.xspeed = -10 + random(20);
            temp.yspeed = -10 + random(20);
            temp.gotoAndStop(random(temp._totalframes) + 1);
            temp.action = shardFrame;
            entityArray.push(temp);
            i++;
         }
         addEnemy(300);
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
   this.clear();
   this.lineStyle(2,0,100);
   this.lineTo(player._x + player.width / 2 - this._x,player._y + player.height / 2 - this._y);
}
function grenadeFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      this.yspeed += 0.75;
      this.stepc -= 1;
   }
   this.gfx._rotation += this.xspeed * timeStep * 4;
   this._x += this.xspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(map[y][x][0] != 0)
   {
      this._x -= this.xspeed * timeStep;
      this.xspeed *= -0.5;
      var x = Math.floor(this._x / tileWidth);
      if(sounds)
      {
         var r = random(4);
         _root["smetal" + r].start(0,0);
      }
   }
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   if(map[y][x][0] != 0)
   {
      this._y -= this.yspeed * timeStep;
      this.yspeed *= -0.5;
      var y = Math.floor(this._y / tileHeight);
      this.bounces = this.bounces + 1;
      if(sounds)
      {
         var r = random(4);
         _root["smetal" + r].start(0,0);
      }
   }
   var hit = 0;
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1))
      {
         enemyArray[i].health -= this.damage;
         score += this.damage;
         hit = 1;
         hits++;
         break;
      }
      i++;
   }
   if(hit || this.bounces >= 3 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      if(hit || this.bounces >= 3)
      {
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 100)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 100;
            player.xspeed += int(mult * 9 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 24 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sboom.start(0,0);
         }
      }
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function fireMinesFrame(timeStep)
{
   this.stepc += timeStep;
   var move = 0;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      if(!this.active)
      {
         this.yspeed += 1;
      }
      this.stepc -= 1;
      move = 1;
   }
   this._rotation = 0;
   this._x += this.xspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(map[y][x][0] != 0)
   {
      this._x -= this.xspeed * timeStep;
      this.xspeed *= -0.5;
      var x = Math.floor(this._x / tileWidth);
   }
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   if(map[y][x][0] != 0)
   {
      this._y = y * tileHeight - this.power._height / 2 - 1;
      this.yspeed = 0;
      this.xspeed = 0;
      this.active = this.active + 1;
   }
   if(this.active == 1)
   {
      var temp = this.attachMovie("flamePillar","FlamePillar",0);
      temp._alpha = 0;
      temp._xscale = 0;
   }
   if(this.active)
   {
      if(sounds)
      {
         sflame.setVolume(255);
      }
      if(move)
      {
         this.active = this.active + 1;
      }
      var i = 0;
      while(i < enemyArray.length)
      {
         if(enemyArray[i].hitTest(this))
         {
            enemyArray[i].health -= this.damage * timeStep;
            score += this.damage * timeStep;
            if(this.nohit++ == 1)
            {
               hits++;
            }
            break;
         }
         i++;
      }
   }
   if(this.active <= 20)
   {
      this.flamePillar._alpha += 25 * timeStep;
      if(this.flamePillar._alpha > 100)
      {
         this.flamePillar._alpha = 100;
      }
      this.flamePillar._xscale += 25 * timeStep;
      if(this.flamePillar._xscale > 100)
      {
         this.flamePillar._xscale = 100;
      }
   }
   if(this.active > 30)
   {
      this.flamePillar._alpha -= 7 * timeStep;
      this.flamePillar._xscale -= 7 * timeStep;
      if(this.flamePillar._alpha <= 0)
      {
         var i = 0;
         while(i < entityArray.length)
         {
            if(entityArray[i] == this)
            {
               entityArray.splice(i,1);
               break;
            }
            i++;
         }
         rem = 1;
         this.removeMovieClip();
      }
   }
}
function railFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.anim > 1)
   {
      this._alpha -= 10 * timeStep;
   }
   if(this.stepc >= 1)
   {
      this.anim = this.anim + 1;
      if(this.anim == 1)
      {
         var hit = 0;
         var x = this._x;
         var y = this._y;
         var left = (worldpos[0] - 1) * tileWidth;
         var right = (worldpos[0] + stw + 1) * tileWidth;
         var up = (worldpos[1] - 1) * tileHeight;
         var down = (worldpos[1] + sth + 1) * tileHeight;
         var i = 0;
         while(i < enemyArray.length)
         {
            var tx = x;
            var ty = y;
            while(tx > left && tx < right && ty > up && ty < down)
            {
               tx += this.xspeed;
               ty += this.yspeed;
               if(enemyArray[i].hit.hitTest(tx + world._x,ty + world._y,1))
               {
                  enemyArray[i].health -= this.damage;
                  score += this.damage;
                  if(hit == 0)
                  {
                     hits++;
                     hit = 1;
                  }
                  break;
               }
            }
            i++;
         }
      }
      if(this.anim > 2)
      {
         if(this._alpha <= 0)
         {
            var i = 0;
            while(i < entityArray.length)
            {
               if(entityArray[i] == this)
               {
                  entityArray.splice(i,1);
                  break;
               }
               i++;
            }
            rem = 1;
            this.removeMovieClip();
         }
      }
   }
}
function shotgunRocket(x, y, rot, speed, damage)
{
   shots += 3;
   addBullet(x,y,rot - 10,speed,smallRocketFrame,7,damage);
   addBullet(x,y,rot,speed,smallRocketFrame,7,damage);
   addBullet(x,y,rot + 10,speed,smallRocketFrame,7,damage);
}
function shotgun(x, y, rot, speed, damage)
{
   shots += 5;
   if(map[Math.floor(y / TileHeight)][Math.floor(x / TileWidth)][0] == 0)
   {
      addBullet(x,y,rot - 10,speed,bulletFrame,1,damage);
      addBullet(x,y,rot - 5,speed,bulletFrame,1,damage);
      addBullet(x,y,rot,speed,bulletFrame,1,damage);
      addBullet(x,y,rot + 5,speed,bulletFrame,1,damage);
      addBullet(x,y,rot + 10,speed,bulletFrame,1,damage);
   }
}
function rocketLauncher(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,rocketFrame,2,damage);
}
function grapple(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,grappleFrame,12,damage);
}
function shoulderCannon(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,railFrame,11,damage);
}
function railGun(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,railFrame,9,damage);
}
function rpg(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,rpgFrame,8,damage);
}
function aBombLauncher(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,abombFrame,6,damage);
}
function seekerLauncher(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,seekerFrame,5,damage);
}
function machineGun(x, y, rot, speed, damage)
{
   shots++;
   if(map[Math.floor(y / TileHeight)][Math.floor(x / TileWidth)][0] == 0)
   {
      addBullet(x,y,rot - 2 + random(4),speed,bulletFrame,1,damage);
   }
}
function uzi(x, y, rot, speed, damage)
{
   shots += 2;
   if(map[Math.floor(y / TileHeight)][Math.floor(x / TileWidth)][0] == 0)
   {
      var xs = speed * Math.cos(rot * 3.141592653589793 / 180);
      var ys = speed * Math.sin(rot * 3.141592653589793 / 180);
      addBullet(x,y,rot - 8 + random(16),speed,bulletFrame,1,damage);
      addBullet(x + xs,y + ys,rot - 8 + random(16),speed,bulletFrame,1,damage);
   }
}
function flameFrame(timeStep)
{
   this.stepc += timeStep;
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var i = 0;
   while(i < enemyArray.length)
   {
      if(enemyArray[i].hitTest(this))
      {
         enemyArray[i].health -= this.damage * (1 - this.gfx._currentframe / this.gfx._totalframes) * timeStep;
         score += this.damage * (1 - this.gfx._currentframe / this.gfx._totalframes) * timeStep;
         if(this.hitser++ == 1)
         {
            hits++;
         }
      }
      i++;
   }
   if(this.stepc >= 1)
   {
      if(map[y][x][0] != 0 && this.gfx._currentframe < this.gfx._totalframes - 3)
      {
         this.gfx.gotoAndStop(this.gfx._totalframes - 3);
      }
      this.gfx.nextFrame();
      if(this.gfx._currentframe == this.gfx._totalframes)
      {
         var i = 0;
         while(i < entityArray.length)
         {
            if(entityArray[i] == this)
            {
               entityArray.splice(i,1);
               break;
            }
            i++;
         }
         rem = 1;
         this.removeMovieClip();
      }
      this.stepc -= 1;
   }
}
function flameThrower(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot - 10 + random(20),speed,flameFrame,3,damage);
}
function grenadeLauncher(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,grenadeFrame,4,damage);
}
function fireMines(x, y, rot, speed, damage)
{
   shots++;
   addBullet(x,y,rot,speed,fireMinesFrame,10,damage);
}
function addBullet(x, y, rot, speed, func, frame, damage)
{
   var temp = world.attachMovie("bullet","bullet_" + world.entityDepth,world.entityDepth++);
   temp._x = x;
   temp._y = y;
   temp.sped = speed;
   temp.xspeed = speed * Math.cos(rot * 3.141592653589793 / 180);
   temp.yspeed = speed * Math.sin(rot * 3.141592653589793 / 180);
   temp.gotoAndStop(frame);
   temp._rotation = rot;
   temp.action = func;
   temp.damage = damage;
   entityArray.push(temp);
}
function enemyBulletFrame(timeStep)
{
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   var hit = 0;
   if(player.gfx.hit.hitTest(this._x + world._x,this._y + world._y,1))
   {
      hit = 1;
      if(player.powerupon != 2)
      {
         player.health -= 10;
         var i = 0;
         while(i < 3)
         {
            var temp = world.attachMovie("blood","blood_" + world.entityDepth,world.entityDepth++);
            temp._x = player._x + player.width / 2;
            temp._y = player._y + player.height / 2;
            temp._rotation = random(360);
            temp.action = animationFrame;
            temp.stop();
            temp.pause = i * 2;
            entityArray.push(temp);
            i++;
         }
      }
   }
   if(hit || map[y][x][0] != 0 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function addEnemyBullet(x, y, rot, speed, parent)
{
   var temp = world.attachMovie("enemybullet","ebullet_" + world.entityDepth,world.entityDepth++);
   temp._x = x;
   temp._y = y;
   temp.xspeed = speed * Math.cos(rot * 3.141592653589793 / 180);
   temp.yspeed = speed * Math.sin(rot * 3.141592653589793 / 180);
   temp.gotoAndStop(frame);
   temp._rotation = rot;
   temp.action = enemyBulletFrame;
   entityArray.push(temp);
}
function heroSetup()
{
   this.stepc = 0;
   this.width = 48;
   this.height = 48;
   this.defplayerwidth = 10;
   this.defplayerheight = 42;
   this.xspeed = 0;
   this.yspeed = 0;
   this.xchange = 0;
   this.ychange = 0;
   this.jump = 0;
   this.jump2 = 0;
   this.duck = 0;
   this.guns = [];
   this.guns.push({type:0,reloadtime:Infinity,bullets:Infinity,shots:0});
   var i = 1;
   while(i < guns.length - 1)
   {
      this.guns.push({type:i,reloadtime:Infinity,bullets:0,shots:0});
      i++;
   }
   this.guns.push({type:guns.length - 1,reloadtime:Infinity,bullets:Infinity,shots:0});
   this.cgun = 0;
   this.bullettime = maxbullettime;
   this.hyperjump = 150;
   this.health = this.lastHealth = 100;
   this.powerupon = 0;
   this.cgun = 0;
}
function heroStart(timeStep)
{
   this.gfx.gotoAndStop(6);
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.yspeed = 2;
      this.stepc -= 1;
   }
   var y = Math.floor((this._y + this.height) / tileHeight);
   var x = Math.floor((this._x + this.width / 2) / tileWidth);
   this._y += this.yspeed * timeStep;
   this._y += 5;
   if(this.fall)
   {
      this.gfx.chute._xscale -= 10 * timeStep;
      if(this.gfx.chute._xscale < 0)
      {
         this.gfx.chute._xscale = 0;
         this.gfx.chute._visible = 0;
         this.action = heroAction;
         gamestarted = 1;
         addEnemy(300);
      }
   }
   else
   {
      this.gfx.chute._xscale += 10 * timeStep;
      if(this.gfx.chute._xscale > 100)
      {
         this.gfx.chute._xscale = 100;
      }
      if(y > 0 && map[y + 5][x][0] != 0)
      {
         this.fall = 1;
      }
   }
   if(this._y + this.height - (- world._y) > sh - sh / 4)
   {
      world._y = - (this._y + this.height) + sh - sh / 4;
      ret++;
   }
   return ret;
}
function heroAction(timestep)
{
   var move = 0;
   this.stepc += timestep;
   this.gfx._alpha = 100;
   if(this.stepc >= 1)
   {
      move = 1;
   }
   var color0 = new Color(world);
   var color1 = new Color(bg);
   var color2 = new Color(bglayer1);
   var color3 = new Color(HUD);
   if(this.lasthealth > this.health)
   {
      color0.setTransform(hitColor);
      color1.setTransform(hitColor);
      color2.setTransform(hitColor);
      color3.setTransform(hitColor);
      if(sounds)
      {
         shurt.start(0,0);
      }
   }
   else
   {
      color0.setTransform(normalColor);
      color1.setTransform(normalColor);
      color2.setTransform(normalColor);
      color3.setTransform(normalColor);
   }
   var thiscolor = new Color(this);
   var thiscolort = normalColor;
   if(this.powerupOn != 0)
   {
      HUD.powerup._visible = 1;
      if(this.powerupOn == 1)
      {
         thiscolort = doubleDamageColor;
      }
      if(this.powerupOn == 2)
      {
         thiscolort = invunerableColor;
      }
      this.gfx._alpha = 100;
      if(this.powerupOn == 3)
      {
         this.cgun = guns.length - 1;
         this.gfx._alpha = 0;
         color0.setTransform(invColor);
         color1.setTransform(invColor);
         color2.setTransform(invColor);
         color3.setTransform(invColor);
         if(this.pred++ % 10 == 4)
         {
            this.gfx._alpha = 10;
         }
         if(this.pred++ % 10 == 8)
         {
            this.gfx._alpha = 4;
         }
      }
      else if(this.cgun == guns.length - 1)
      {
         this.cgun = 0;
         this.gfx._alpha = 100;
      }
      if(this.powerupOn == 4)
      {
         thiscolort = warpColor;
         move = 1;
         timeStep = 1;
      }
      if(this.powerUpTime <= 0)
      {
         if(this.powerupOn == 3)
         {
            this.cgun = 0;
            this._visible = 1;
         }
         this.powerupOn = 0;
      }
      HUD.powerup.powerup.mask._yscale = this.powerupTime / powerupTime * 100;
      if(move)
      {
         if(this.powerupOn == 5 && this.jump)
         {
            if(this.smok++ % 5 == 0)
            {
               var temp = world.attachMovie("smoke","smoke_" + world.entityDepth,world.entityDepth++);
               temp._x = this._x + this.width / 2;
               temp._y = this._y + this.height / 2 + this.playerheight / 2;
               temp.stop();
               temp.action = animationFrame;
               entityArray.push(temp);
            }
         }
         this.powerupTime--;
      }
   }
   else
   {
      HUD.powerup._visible = 0;
   }
   thiscolor.setTransform(thiscolort);
   this.lasthealth = this.health;
   this.xchange = 0;
   if(move && Key.isDown(duckKey))
   {
      this.playerWidth = 2 * this.defPlayerWidth / 3;
      this.playerHeight = 2 * this.defPlayerHeight / 3;
      this.duck = 1;
   }
   else if(move)
   {
      if(this.duck)
      {
         this._y -= 2 * this.defPlayerWidth / 3;
      }
      this.playerWidth = this.defPlayerWidth;
      this.playerHeight = this.defPlayerHeight;
      this.duck = 0;
   }
   if(move && !this.duck)
   {
      if(Key.isDown(leftkey))
      {
         if(this.xspeed > -5)
         {
            this.xspeed--;
         }
      }
      if(Key.isDown(rightkey))
      {
         if(this.xspeed < 5)
         {
            this.xspeed = this.xspeed + 1;
         }
      }
   }
   if(this.yspeed > 0 || this.yspeed < 0)
   {
      if(!this.jump)
      {
         this.jump = 1;
      }
   }
   if(move && this.hyperjump < 150)
   {
      this.hyperjump = this.hyperjump + 1;
   }
   if(this.hyperjump >= 150 && move && Key.isDown(boostKey) && (!this.jump || !this.jump2) && !this.hjump)
   {
      if(!this.boostK)
      {
         if(sounds)
         {
            shjump.start(0,0);
         }
         this.yspeed = -32;
         if(this.jump)
         {
            this.jump2 = 1;
         }
         this.jump = 1;
         this.hjump = 1;
         this.hyperjump = 0;
         hjumps++;
      }
      this.boostK = 1;
   }
   else
   {
      this.boostK = 0;
   }
   HUD.hyperjump.mask._xscale = this.hyperjump / 150 * 100;
   if(move && Key.isDown(jumpkey))
   {
      if(this.powerupon == 5)
      {
         this.jump = this.jump2 = this.hjump = 1;
         this.yspeed = Math.max(this.yspeed - 2,-32);
      }
      else
      {
         if(this.up > 0)
         {
            this.yspeed = Math.min(this.yspeed,-8);
            if(!this.upk)
            {
               if(!this.jump)
               {
                  this.jump = 1;
               }
               else if(!this.jump2)
               {
                  this.jump2 = 1;
               }
            }
            this.up--;
         }
         this.upk = 1;
      }
   }
   else if(move)
   {
      if(!this.jump || !this.jump2 && !this.duck)
      {
         this.up = 6;
      }
      else
      {
         this.up = 0;
      }
      this.upk = 0;
   }
   if(this.jump && !this.duck)
   {
      this.gfx.gotoAndStop(3);
   }
   if(move && (Key.isDown(leftkey) && Key.isDown(rightkey)) || !Key.isDown(leftkey) && !Key.isDown(rightkey) || this.duck && !this.jump)
   {
      if(this.xspeed > 0)
      {
         this.xspeed--;
      }
      else if(this.xspeed < 0)
      {
         this.xspeed = this.xspeed + 1;
      }
   }
   if(move && this.xspeed > 6)
   {
      this.xspeed--;
   }
   if(move && this.xspeed < -6)
   {
      this.xspeed = this.xspeed + 1;
   }
   if(move && this.yspeed > tileHeight)
   {
      this.yspeed = tileHeight;
   }
   if(move && this.yspeed < - tileHeight)
   {
      this.yspeed = - tileHeight;
   }
   if(move)
   {
      this.yspeed = this.yspeed + 1;
   }
   this.xchange = this.xspeed;
   this.ychange = this.yspeed;
   this.tilex = Math.floor((this._x + this.xchange + this.width / 2 - this.playerwidth / 2) / tileWidth);
   this.tile2x = Math.floor((this._x + this.xchange + this.width / 2 + this.playerwidth / 2) / tileWidth);
   this.tiley = Math.floor((this._y + 1 + this.height / 2 - this.playerheight / 2) / tileHeight);
   this.tile2y = Math.floor((this._y + this.height / 2 + this.playerheight / 2) / tileHeight);
   if(this.xchange != 0)
   {
      if(this.xchange > 0)
      {
         if(this.tile2x >= width)
         {
            this.hits = 1;
         }
         else
         {
            this.hits = hitCheck(map,this.tiley,this.tile2x,this.tile2y,this.tile2x,1,1,1);
         }
         if(!this.hits)
         {
            this._x += this.xchange * timeStep;
         }
         else
         {
            this._x = this.tile2x * tileWidth - this.width + (this.width - this.playerWidth) / 2 - 1;
            this.xspeed = 0;
         }
      }
      else
      {
         if(this.tilex < 0)
         {
            this.hits = 1;
         }
         else
         {
            this.hits = hitCheck(map,this.tiley,this.tilex,this.tile2y,this.tilex,1,1,1);
         }
         if(!this.hits)
         {
            this._x += this.xchange * timeStep;
         }
         else
         {
            this._x = (this.tilex + 1) * tileWidth - (this.width - this.playerWidth) / 2 - 1;
            this.xspeed = 0;
         }
      }
   }
   this.tilex = Math.floor((this._x + 1 + this.width / 2 - this.playerwidth / 2) / tileWidth);
   this.tile2x = Math.floor((this._x + this.width / 2 + this.playerwidth / 2) / tileWidth);
   this.tiley = Math.floor((this._y + this.ychange + this.height / 2 - this.playerheight / 2) / tileHeight);
   this.tile2y = Math.floor((this._y + this.ychange + this.height / 2 + this.playerheight / 2) / tileHeight);
   if(this.ychange != 0)
   {
      if(this.ychange > 0)
      {
         if(!hitCheck(map,this.tile2y,this.tilex,this.tile2y,this.tile2x,0))
         {
            this._y += this.ychange * timeStep;
         }
         else
         {
            this._y = this.tile2y * tileHeight - this.height + (this.height - this.playerHeight) / 2 - 1;
            this.yspeed = 0;
            this.jump = 0;
            this.jump2 = 0;
            this.hjump = 0;
            this.grab = 0;
         }
      }
      else if(!hitCheck(map,this.tiley,this.tilex,this.tiley,this.tile2x,0))
      {
         this._y += this.ychange * timeStep;
      }
      else
      {
         this._y = (this.tiley + 1) * tileHeight - (this.height - this.playerHeight) / 2 - 1;
         this.yspeed = 0;
         this.jump = 1;
         this.jump2 = 1;
         this.up = 0;
      }
   }
   if(this.duck)
   {
      this.gfx.gotoAndStop(2);
   }
   else if(this.jump)
   {
      if(this.jump2)
      {
         this.gfx.gotoAndStop(5);
      }
      else
      {
         this.gfx.gotoAndStop(3);
      }
   }
   else if(this.xchange != 0)
   {
      this.gfx.gotoAndStop(4);
      if(move)
      {
         if(this.gfx.gfx._currentframe < this.gfx.gfx._totalframes)
         {
            this.gfx.gfx.nextFrame();
         }
         else
         {
            this.gfx.gfx.gotoAndStop(1);
         }
      }
   }
   else
   {
      this.gfx.gotoAndStop(1);
   }
   if(powerupon != 3 && Key.isDown(switchKey))
   {
      if(!this.switchK)
      {
         do
         {
            this.cgun = this.cgun + 1;
            if(this.cgun >= this.guns.length - 1)
            {
               this.cgun = 0;
            }
         }
         while(this.guns[this.cgun].bullets <= 0);
         
      }
      this.switchK = 1;
   }
   else
   {
      this.switchK = 0;
   }
   this.gun.gotoAndStop(this.guns[this.cgun].type + 1);
   this.gunrotation = 360 - Math.atan2(world._x + this._x + this.gun._x - _root._xmouse,world._y + this._y + this.gun._y - _root._ymouse) * 180 / 3.141592653589793 - 90;
   var rotd = this.gunrotation;
   var rotn = this.gun._rotation;
   rotd = (rotd + 360) % 360;
   rotn = (rotn + 360) % 360;
   var dif = rotd - rotn;
   dif = dif <= 179 ? dif : -360 + dif;
   dif = dif >= -179 ? dif : 360 + dif;
   this.gun._rotation += dif / 2 * timeStep;
   if(this.gun._rotation > 90 || this.gun._rotation < -90)
   {
      this.gun._yscale = -100;
   }
   else
   {
      this.gun._yscale = 100;
   }
   if(move)
   {
      this.guns[this.cgun].reloadtime = this.guns[this.cgun].reloadtime + 1;
   }
   if(this.guns[this.cgun].reloadtime < guns[this.guns[this.cgun].type].reloadtime)
   {
      HUD.reload.yellow._visible = 0;
      HUD.reload.mask._xscale = this.guns[this.cgun].reloadtime / guns[this.guns[this.cgun].type].reloadtime * 100;
   }
   else if(this.guns[this.cgun].bullets > 0)
   {
      HUD.reload.yellow._visible = 1;
   }
   if(mouseD)
   {
      if(move)
      {
         if(this.guns[this.cgun].bullets > 0)
         {
            if(this.guns[this.cgun].reloadtime >= guns[this.guns[this.cgun].type].reloadtime)
            {
               this.guns[this.cgun].shots = this.guns[this.cgun].shots + 1;
               this.guns[this.cgun].reloadtime = 0;
               this.guns[this.cgun].bullets--;
               point = {x:0,y:0};
               this.gun.barrell.localToGlobal(point);
               var type = this.guns[this.cgun].type;
               if(this.powerupOn == 1)
               {
                  guns[type].gun(point.x - world._x,point.y - world._y,this.gun._rotation,guns[type].speed,guns[type].damage * 3);
               }
               else
               {
                  guns[type].gun(point.x - world._x,point.y - world._y,this.gun._rotation,guns[type].speed,guns[type].damage);
               }
               if(sounds)
               {
                  if(guns[type].soundhold)
                  {
                     guns[type].sound.setVolume(100);
                  }
                  else
                  {
                     guns[type].sound.start(0,0);
                  }
               }
            }
            if(this.guns[this.cgun].bullets <= 0)
            {
               this.guns[this.cgun].reloadtime = Infinity;
               this.cgun = 0;
            }
         }
      }
   }
   HUD.weapon.gotoAndStop(this.cgun + 1);
   if(this.guns[this.cgun].bullets == Infinity)
   {
      HUD.ammo = "Infinite x ";
   }
   else
   {
      HUD.ammo = this.guns[this.cgun].bullets + " x ";
   }
   if(this.stepc > 1)
   {
      this.stepc -= 1;
   }
   if(this.powerupOn == 2)
   {
      this.health = this.ihealth;
   }
   this.ihealth = this.health;
   var ret = 0;
   if(this.xchange > 0 && this._x + this.width - (- world._x) > sw / 2 + this.width)
   {
      world._x = - (this._x + this.width) + sw / 2 + this.width;
      ret++;
   }
   if(this.xchange < 0 && this._x - (- world._x) < sw / 2 - this.width)
   {
      world._x = - this._x + sw / 2 - this.width;
      ret++;
   }
   if(this.ychange > 0 && this._y + this.height - (- world._y) > sh - sh / 4)
   {
      world._y = - (this._y + this.height) + sh - sh / 4;
      ret++;
   }
   if(this.ychange < 0 && this._y - (- world._y) < sh / 4)
   {
      world._y = - this._y + sh / 4;
      ret++;
   }
   return ret;
}
function heroDie(timeStep)
{
   HUD.ammo = "0 x ";
   HUD.reload.mask._xscale = 0;
   HUD.reload.yellow._visible = 0;
   HUD.bullettime.mask._xscale = 0;
   HUD.hyperjump.mask._xscale = 0;
   HUD.powerup._visible = 0;
   this.stepc += timeStep;
   if(this.stepc >= 1)
   {
      this.yspeed = this.yspeed + 1;
      this.stepc -= 1;
   }
   if(this.rot == undefined)
   {
      this.rot = 10;
   }
   this._rotation += Math.abs(this.xspeed + this.yspeed) * timeStep;
   this._x += this.xspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(map[y][x][0] != 0)
   {
      this._x -= this.xspeed * timeStep;
      this.xspeed *= -0.5;
      var x = Math.floor(this._x / tileWidth);
   }
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   if(map[y][x][0] != 0)
   {
      this._y = y * tileHeight - this.power._height / 2 - 2;
      this._y -= this.yspeed * timeStep;
      if(this.yspeed < 4)
      {
         this.action = null;
      }
      this.yspeed *= -0.5;
      this.rot = 0;
   }
   world._x = - this._x + sw / 2;
   world._y = - this._y + sh / 2;
   return 1;
}
function guyFall(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc >= 1)
   {
      this.yspeed = this.yspeed + 1;
      this.stepc -= 1;
   }
   if(this.rot == undefined)
   {
      this.rot = 10;
   }
   this._rotation += Math.abs(this.xspeed + this.yspeed) * timeStep;
   this._x += this.xspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(map[y][x][0] != 0)
   {
      this._x -= this.xspeed * timeStep;
      this.xspeed *= -0.5;
      var x = Math.floor(this._x / tileWidth);
   }
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   if(map[y][x][0] != 0)
   {
      if(this.yspeed < 4)
      {
         var i = 0;
         while(i < entityArray.length)
         {
            if(entityArray[i] == this)
            {
               entityArray.splice(i,1);
               break;
            }
            i++;
         }
         rem = 1;
         this.removeMovieClip();
      }
      else
      {
         this._y -= this.yspeed * timeStep;
         this.yspeed *= -0.2;
         this.rot = 0;
      }
   }
}
function heliFall(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc >= 1)
   {
      this.yspeed = this.yspeed + 1;
      this.stepc -= 1;
   }
   if(this.xspeed > 0)
   {
      this._rotation += this.yspeed * timeStep / 4;
   }
   else
   {
      this._rotation -= this.yspeed * timeStep / 4;
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   if(map[Math.floor(this._y / tileHeight)][Math.floor(this._x / tileWidth)][0] != 0)
   {
      var i = 0;
      while(i < 3)
      {
         var temp = world.attachMovie("Shard","Shard_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y - tileWidth / 2;
         temp._rotation = random(360);
         temp.gotoAndStop(random(temp._totalframes) + 1);
         temp.xspeed = -10 + random(20);
         temp.yspeed = -10 + random(20);
         temp.action = shardFrame;
         entityArray.push(temp);
         i++;
      }
      if(sounds)
      {
         sboom.start(0,0);
      }
      var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
      temp._x = this._x;
      temp._y = this._y;
      temp._xscale = temp._yscale = 200;
      temp.action = animationFrame;
      entityArray.push(temp);
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function shardFrame(timeStep)
{
   this.stepc += timeStep;
   if(this.stepc > 1)
   {
      this.r = this.r + 1;
      this.yspeed += 1;
      this.stepc -= 1;
   }
   this._rotation += this.xspeed * timeStep * 4;
   this._x += this.xspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   var x = Math.floor(this._x / tileWidth);
   if(map[y][x][0] != 0)
   {
      this._x -= this.xspeed * timeStep;
      this.xspeed *= -0.5;
      var x = Math.floor(this._x / tileWidth);
      if(!(sbounce++ % 3) && sounds)
      {
         var r = random(4);
         _root["smetal" + r].start(0,0);
      }
   }
   this._y += this.yspeed * timeStep;
   var y = Math.floor(this._y / tileHeight);
   if(map[y][x][0] != 0)
   {
      this._y -= this.yspeed * timeStep;
      this.yspeed *= -0.5;
      var y = Math.floor(this._y / tileHeight);
      this.bounces = this.bounces + 1;
      if(!(sbounce++ % 3) && sounds)
      {
         var r = random(4);
         _root["smetal" + r].start(0,0);
      }
   }
   if(this.bounces >= 3 || x < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      var i = 0;
      while(i < entityArray.length)
      {
         if(entityArray[i] == this)
         {
            entityArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      this.removeMovieClip();
   }
}
function heliFrame(timeStep)
{
   if(sounds)
   {
      var vol = distance(this._x,this._y,player._x + player.width / 2,player._y) / 800;
      vol = Math.min(vol,1);
      vol = Math.max(vol,0);
      sheli.setVolume(75 * (1 - vol));
   }
   if(this.health <= 0)
   {
      var i = 0;
      while(i < enemyArray.length)
      {
         if(enemyArray[i] == this)
         {
            enemyArray.splice(i,1);
            break;
         }
         i++;
      }
      rem = 1;
      if(!gameover)
      {
         if(player._y < this._y)
         {
            var temp = world.attachMovie("popup","popup_" + world.entityDepth,world.entityDepth++);
            temp._x = Math.floor(player._x + player.width / 2 - temp._width / 2);
            temp._y = Math.floor(player._y - temp._height * 2);
            temp.action = popupFrame;
            entityArray.push(temp);
            temp.text = "Random Weapon";
            var gun = random(7) + 1;
            var bullets = 0;
            if(gun == 1)
            {
               bullets = 10;
            }
            else if(gun == 2)
            {
               bullets = 3;
            }
            else if(gun == 3)
            {
               bullets = 2;
            }
            else if(gun == 4)
            {
               bullets = 2;
            }
            else if(gun == 5)
            {
               bullets = 2;
            }
            else if(gun == 6)
            {
               bullets = 2;
            }
            else if(gun == 7)
            {
               bullets = 1;
            }
            else if(gun == 8)
            {
               bullets = 30;
            }
            else if(gun == 9)
            {
               bullets = 1;
            }
            player.guns[gun].bullets += bullets;
         }
         helis++;
         rthelis++;
         if(helis == 3)
         {
            var temp = world.attachMovie("powerup","powerup_" + world.entityDepth,world.entityDepth++);
            temp._x = this._x;
            temp._y = this._y;
            temp.chute._xscale = 0;
            if(rthelis >= nextHealth)
            {
               nextHealth *= 2;
               temp.power.gotoAndStop(1);
            }
            else
            {
               if(random(100) % 32 == 0)
               {
                  temp.randomed = 1;
               }
               temp.power.gotoAndStop(random(temp.power._totalframes - 1) + 2);
            }
            temp.action = powerupFrame;
            entityArray.push(temp);
            helis = 0;
         }
      }
      var i = 0;
      while(i < 3)
      {
         var temp = world.attachMovie("Shard","Shard_" + world.entityDepth,world.entityDepth++);
         temp._x = this._x;
         temp._y = this._y;
         temp._rotation = random(360);
         temp.xspeed = -10 + random(20);
         temp.yspeed = -10 + random(20);
         temp.gotoAndStop(random(temp._totalframes) + 1);
         temp.action = shardFrame;
         entityArray.push(temp);
         i++;
      }
      var temp = world.attachMovie("GuyBurned","GuyBurned_" + world.entityDepth,world.entityDepth++);
      temp._x = this._x;
      temp._y = this._y;
      temp._rotation = this._rotation;
      temp.action = guyFall;
      temp.xspeed = -10 + random(20);
      temp.yspeed = -10 + random(15);
      entityArray.push(temp);
      var temp = world.attachMovie("HeliDestroyed","HeliDestroyed_" + world.entityDepth,world.entityDepth++);
      temp._x = this._x;
      temp._y = this._y;
      temp._rotation = this._rotation;
      temp.xspeed = this.xspeed;
      temp.yseed = this.yspeed;
      temp.action = heliFall;
      temp.gotoAndStop(this._currentframe);
      entityArray.push(temp);
      var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
      temp._x = this._x;
      temp._y = this._y;
      temp._xscale = temp._yscale = 200;
      temp.action = animationFrame;
      entityArray.push(temp);
      player.bullettime = Math.min(maxbullettime,player.bullettime + maxbullettime / 3);
      if(!gameover)
      {
         addEnemy(300);
      }
      if(sounds)
      {
         sheliboom.start(0,0);
      }
      this.removeMovieClip();
      return undefined;
   }
   if(this.lasthealth != this.health)
   {
      var color0 = new Color(this);
      color0.setTransform(whiteColor);
   }
   else
   {
      var color0 = new Color(this);
      color0.setTransform(normalColor);
   }
   this.lasthealth = this.health;
   var move = 0;
   this.stepc += timestep;
   if(this.stepc >= 1)
   {
      move = 1;
      this.stepc -= 1;
   }
   if(this.onScreen <= 0)
   {
      if(this.goto == undefined)
      {
         this.goto = random(10);
      }
      if(this.goto < 4)
      {
         this.tx = worldpos[0] * tileWidth - spw * 2;
      }
      else if(this.goto < 8)
      {
         this.tx = worldpos[0] * tileWidth + spw * 2;
      }
      else
      {
         this.ty = worldpos[1] * tileHeight - sph;
      }
      if(this._y < worldpos[1] * tileHeight - this._height || this._x < worldpos[0] * tileWidth - this._width || this._x > worldpos[0] * tileWidth + spw + this._width)
      {
         var i = 0;
         while(i < enemyArray.length)
         {
            if(enemyArray[i] == this)
            {
               enemyArray.splice(i,1);
               break;
            }
            i++;
         }
         addEnemy(this.health);
         this.removeMovieClip("");
      }
   }
   else
   {
      if(move)
      {
         if(this.xt++ % 75 == 1)
         {
            this.xdif = (- spw) / 2 + random(spw - this._width / 2) + this._width / 2;
         }
      }
      this.tx = player._x + this.xdif;
      if(this.tx < this._width / 2)
      {
         this.tx = this._width / 2;
      }
      if(this.tx > width * tileWidth - this.Width / 2)
      {
         this.tx = width * tileWidth - this.Width / 2;
      }
      if(player.hjump)
      {
         this.ty = Math.min(height * tileHeight - sph / 2 - 100,player._y + 50 + random(50));
      }
      else if(move)
      {
         if(this.yt++ % 40 == 1)
         {
            this.ty = player._y - sph / 2 - (-2 + random(4)) * 10;
         }
      }
   }
   if(this.onScreen < 0 || this._y < worldpos[1] * tileHeight || this._x < worldpos[0] * tileWidth || this._x > worldpos[0] * tileWidth + spw)
   {
      var dx = this.tx - this._x;
      var dy = this.ty - this._y;
      this.xspeed += dx / 100;
      this.yspeed += dy / 20;
   }
   else
   {
      var dx = this.tx - this._x;
      var dy = this.ty - this._y;
      this.xspeed += dx / 200;
      this.yspeed += dy / 100;
   }
   if(move)
   {
      var r = Math.floor(this.xspeed / 20 * 15);
      if(Math.abs(r) > 2)
      {
         this._rotation = r;
      }
      else
      {
         this._rotation = 0;
      }
   }
   this._x += this.xspeed * timeStep;
   this._y += this.yspeed * timeStep;
   if(move)
   {
      this.xspeed *= 0.9 * timeStep;
      this.yspeed *= 0.9 * timeSetp;
   }
   this.gun.barrell.localToGlobal(point);
   if(player.powerupon != 3)
   {
      this.gunrotation = 360 - Math.atan2(this._x + this.gun._x - player._x - player.width / 2,this._y + this.gun._y - player._y) * 180 / 3.141592653589793 - 90 - this._rotation;
   }
   else
   {
      this.gunrotation = 360 - Math.atan2(this._x + this.gun._x - player._x - player.width / 2 - spw / 2 + random(spw),this._y + this.gun._y - player._y) * 180 / 3.141592653589793 - 90 - this._rotation;
   }
   var rotd = this.gunrotation;
   var rotn = this.gun._rotation;
   rotd = (rotd + 360) % 360;
   rotn = (rotn + 360) % 360;
   var dif = rotd - rotn;
   dif = dif <= 179 ? dif : -360 + dif;
   dif = dif >= -179 ? dif : 360 + dif;
   this.gun._rotation += dif / Math.max(1,10 - level) * timeStep;
   if(this.gun._rotation > 90 || this.gun._rotation < -90)
   {
      this.gun._yscale = -100;
   }
   else
   {
      this.gun._yscale = 100;
   }
   if(move)
   {
      if(this.shoot++ % Math.max(10,16 - level) == 1)
      {
         if(player.powerupon == 3)
         {
            this.gun._rotation = this.gunrotation;
         }
         point = {x:0,y:0};
         this.gun.barrell.localToGlobal(point);
         addEnemyBullet(point.x - world._x,point.y - world._y,this.gun._rotation - 5 + random(10),7);
      }
   }
   var y = Math.floor((this._y - this._height / 2) / tileHeight);
   var x = Math.floor((this._x - this._width / 2) / tileWidth);
   var y2 = Math.floor((this._y + this._height / 2) / tileHeight);
   var x2 = Math.floor((this._x + this._width / 2) / tileWidth);
   if(x2 < worldpos[0] - 1 || x > worldpos[0] + stw + 1 || y2 < worldpos[1] - 1 || y > worldpos[1] + sth + 1)
   {
      this._visible = 0;
   }
   else
   {
      if(move)
      {
         this.onscreen--;
      }
      this._visible = 1;
   }
}
function addEnemy(health)
{
   var temp = world.attachMovie("Heli","Heli_" + world.entityDepth,world.entityDepth++);
   if(random(3))
   {
      if(random(2))
      {
         temp._x = - world._x - temp._width;
      }
      else
      {
         temp._x = - world._x + spw + temp._width;
      }
      temp._y = maxheight;
   }
   else
   {
      temp._x = - world._x + spw / 2;
      temp._y = worldpos[1] * tileHeight - this._height / 2;
   }
   temp.action = heliFrame;
   temp.health = health;
   temp.gotoAndStop(random(2) + 1);
   temp.onscreen = 150 + random(100);
   temp._visible = 0;
   enemyArray.push(temp);
}
function game(first)
{
   if(Key.isDown(soundKey))
   {
      if(soundK)
      {
         sounds = so.data.sounds = !sounds;
         if(!sounds)
         {
            SoundBoard.stopAll();
         }
         else
         {
            smusic.start(0,9999999);
         }
      }
      soundK = 0;
   }
   else
   {
      soundK = 1;
   }
   stepc += sendGameSpeed;
   if(stepc > 1)
   {
      stepc--;
      sflame.setVolume(0);
   }
   var scroll = 0;
   if(Key.isDown(suicideKey) || player.health <= 0 || gameover)
   {
      if(Key.isDown(suicideKey))
      {
         s = 1;
      }
      gameover++;
      sheli.setVolume(0);
      if(gameover == 1)
      {
         mouseD = 0;
         var color0 = new Color(world);
         var color1 = new Color(bg);
         var color2 = new Color(bglayer1);
         var color3 = new Color(HUD);
         color0.setTransform(normalColor);
         color1.setTransform(normalColor);
         color2.setTransform(normalColor);
         color3.setTransform(normalColor);
         var x = player._x + player.width / 2;
         var y = player._y + player.height / 2;
         var d = player.getDepth();
         ttweapon = new Array();
         var i = 0;
         while(i < player.guns.length)
         {
            ttweapon[i] = player.guns[i].shots;
            i++;
         }
         player.removeMovieClip("");
         player = world.attachMovie("guyBurned","player",d);
         player._x = x;
         player._y = y;
         player.action = heroDie;
         player.xspeed = -10 + random(20);
         player.yspeed = - random(10);
         var temp = world.attachMovie("boom","boom_" + world.entityDepth,world.entityDepth++);
         temp._x = x;
         temp._y = y;
         temp._xscale = temp._yscale = 800;
         temp.stop();
         temp.action = animationFrame;
         entityArray.push(temp);
         var dist = distance(this._x,this._y,player._x + player.width / 2,player._y + player.height);
         if(dist < 300)
         {
            var ang = 360 - Math.atan2(player._x + player.width / 2 - this._x,player._y + player.height - this._y) * 180 / 3.141592653589793 + 90;
            var mult = 1 - dist / 300;
            player.xspeed += int(mult * 24 * Math.cos(ang * 3.141592653589793 / 180));
            player.yspeed += mult * 64 * Math.sin(ang * 3.141592653589793 / 180);
            player.hjump = 1;
         }
         if(sounds)
         {
            sbigboom.start(0,0);
         }
         var i = 0;
         while(i < enemyArray.length)
         {
            enemyArray[i].health -= Infinity;
            i++;
         }
      }
      if(gameover > 200 || enemyArray.length == 0 && entityArray.length == 0)
      {
         onEnterFrame = null;
         var temp = attachMovie("stats","stats",32);
         temp._x = 81;
         temp._y = 80;
         temp.score = Math.floor(score) * 100;
         temp.time = Math.floor(time / 30) + " seconds";
         temp.shots = shots;
         temp.hits = hits;
         if(shots > 0)
         {
            temp.accuracy = Math.floor(hits / shots * 100) + "%";
         }
         else
         {
            temp.accuracy = "0%";
         }
         var maxi = 0;
         var maxs = -Infinity;
         var i = 1;
         while(i < ttweapon.length)
         {
            if(ttweapon[i] > maxs)
            {
               maxs = ttweapon[i];
               maxi = i;
            }
            i++;
         }
         if(maxs <= 0)
         {
            maxi = 0;
         }
         if(tweapon[maxi] != 0)
         {
            temp.weapon = guns[maxi].name;
         }
         else
         {
            temp.weapon = "None";
         }
         temp.helis = rthelis;
         games = so.data.games += 1;
         ts = so.data.totalscore += score;
         tshots = so.data.totalshots += shots;
         thits = so.data.totalhits += hits;
         ttime = so.data.totaltime += time;
         thelis = so.data.totalhelis += rthelis;
         thjumps = so.data.totalhjumps += hjumps;
         tbtime = so.data.totalbtime += btime;
         so.data.highscore = hs;
         if(time > besttime)
         {
            besttime = so.data.besttime = time;
         }
         if(time < worsttime && !s)
         {
            worsttime = so.data.worsttime = time;
         }
         if(rthelis > bhelis)
         {
            bhelis = so.data.besthelis = rthelis;
         }
         var i = 0;
         while(i < ttweapon.length)
         {
            so.data.tweapon[i] += ttweapon[i];
            i++;
         }
         so.flush();
         sendscore = Math.floor(score) * 100;
         temp.doRelease = function()
         {
            this.removeMovieClip("");
            endGame();
            gotoAndStop(20);
         };
         temp.submit.onRelease = function()
         {
            this._parent.removeMovieClip("");
            endGame();
            gotoAndStop(24);
         };
         temp.submit.hitArea = temp.submit.hitState;
         temp.submit.hitState._visible = 0;
         onKeyDown = null;
         onEnterFrame = null;
         return undefined;
      }
   }
   if(player.bullettime > 0 && Key.isDown(bulletTimeKey) && gamestarted || gameover || player.powerupOn == 4)
   {
      sendGameSpeed = Math.max(0.2,sendGameSpeed - 0.1);
      if(player.powerupOn != 4)
      {
         player.bullettime--;
      }
      if(!gameover)
      {
         btime++;
      }
   }
   else
   {
      sendGameSpeed = Math.min(gameSpeed,sendGameSpeed + 0.1);
   }
   HUD.bullettime.mask._xscale = player.bullettime / maxbullettime * 100;
   var i = 0;
   while(i < entityArray.length)
   {
      entityArray[i].action(sendGameSpeed);
      if(rem)
      {
         rem = 0;
         i--;
      }
      i++;
   }
   var i = 0;
   while(i < enemyArray.length)
   {
      enemyArray[i].action(sendGameSpeed);
      if(rem)
      {
         rem = 0;
         i--;
      }
      i++;
   }
   sx = world._x;
   sy = world._y;
   if(player.action(sendGameSpeed) || first)
   {
      scrollMap(world,map,worldpos,worldbounds,1,1,1);
      sdx = sx - world._x;
      sdy = sy - world._y;
      bglayer1._x -= sdx / 2;
      if(bglayer1._x < (- bglayer1width) / 2)
      {
         bglayer1._x = 0 + bglayer1._x + bglayer1width / 2;
      }
      if(bglayer1._x > 0)
      {
         bglayer1._x = (- bglayer1width) / 2 + bglayer1._x;
      }
      var yhpos = (- world._y) / maxheight;
      bglayer1._y = - (bglayer1height - sh) + Math.max(0,(1 - yhpos) / 2 * (bglayer1height - sph));
      scrollMap(bglayer1,bglayer1map,bglayer1pos,bglayer1bounds,1,1,0);
   }
   if(!gameover && gamestarted)
   {
      time += 1 * sendGameSpeed;
   }
   if(Math.floor(score) > hs)
   {
      hs = Math.floor(score);
      if(hssent != 0)
      {
         hssent = so.data.highscoresent = 0;
      }
   }
   HUD.highscore = "High Score: " + hs * 100;
   HUD.score = "Score: " + Math.floor(score) * 100;
   HUD.health.mask._yscale = player.health / 100 * 100;
   HUD.time = "Time: " + Math.floor(time / 30) + " seconds     Helis: " + rthelis;
   if(score > nextLevel)
   {
      nextLevel *= 2;
      level++;
      var temp = world.attachMovie("popup","popup_" + world.entityDepth,world.entityDepth++);
      temp._x = Math.floor(player._x + player.width / 2 - temp._width / 2);
      temp._y = Math.floor(player._y - temp._height * 2);
      temp.action = popupFrame;
      temp.text = "Level Up";
      entityArray.push(temp);
   }
}
function startGame()
{
   s = 0;
   level = 0;
   world = drawMap(map1,"world",1,"tiles",1);
   worldpos = new Array(0,0);
   worldbounds = new Array(0,0);
   bglayer1map = bglayer1_1;
   bglayer1 = drawMap(bglayer1map,"bglayer1",0,"bg",0);
   bglayer1pos = new Array(0,0);
   bglayer1bounds = new Array(0,0);
   bglayer1width = bglayer1map[0].length * tileWidth;
   bglayer1height = bglayer1map.length * tileHeight;
   HUD = attachMovie("HUD","HUD",2);
   HUD.weapon.gotoAndStop(1);
   maxheight = height * tileHeight - sh;
   entityArray = new Array();
   enemyArray = new Array();
   gameSpeed = 1;
   sendGameSpeed = gameSpeed;
   rem = 0;
   score = 0;
   gameover = 0;
   time = 0;
   shots = 0;
   hits = 0;
   hjumps = 0;
   btime = 0;
   helis = 0;
   rthelis = 0;
   nextHealth = 15;
   nextLevel = 10000;
   powerupTime = 500;
   gamestarted = 0;
   Key.addListener(this);
   onKeyDown = function()
   {
      if(Key.isDown(pauseKey))
      {
         if(onEnterFrame == null)
         {
            onEnterFrame = game;
         }
         else
         {
            onEnterFrame = null;
         }
      }
   };
   mouseD = 0;
   onMouseDown = function()
   {
      mouseD = 1;
   };
   onMouseUp = function()
   {
      mouseD = 0;
   };
   game(1);
   onEnterFrame = game;
   sflame.start(0,9999999);
   sflame.setVolume(0);
   sheli.start(0,9999999);
   sheli.setVolume(0);
   smusic.setVolume(50);
   if(sounds)
   {
      sbigboom.start(0,0);
   }
}
function endGame()
{
   SoundBoard.stopAll();
   if(sounds)
   {
      smusic.start(0,9999999);
   }
   world.removeMovieClip("");
   bglayer1.removeMovieClip("");
   HUD.removeMovieClip("");
   onMouseDown = onMouseUp = onEnterFrame = null;
   onEnterFrame = null;
   onKeyDown = null;
}
hitCheck = function(mapa, cy, cx, cy2, cx2, type, equal, hold)
{
   if(type == undefined)
   {
      var type = 1;
   }
   if(equal == undefined)
   {
      var equal = 0;
   }
   if(hold == undefined)
   {
      var hold = 0;
   }
   var count = 0;
   var y = cy;
   while(y <= cy2)
   {
      var x = cx;
      while(x <= cx2)
      {
         if(mapa[y][x][0] >= 0 && mapa[y][x][0] < 100)
         {
            if(equal)
            {
               if(mapa[y][x][0] == type)
               {
                  count++;
                  if(!hold)
                  {
                     return 1;
                  }
               }
            }
            else if(mapa[y][x][0] != type)
            {
               count++;
               if(!hold)
               {
                  return 1;
               }
            }
         }
         x++;
      }
      y++;
   }
   return count;
};
map1 = [[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,1],[1,4],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,1],[1,8],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,5]],[[32,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,1],[1,4],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,5],[1,2],[1,6],[1,4],[0,0],[0,0],[0,0],[1,3],[1,5],[1,10],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[1,3],[1,5],[1,2]],[[1,1],[1,1],[1,1],[1,1],[1,1],[1,5],[1,2],[1,6],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,5],[1,2],[1,2],[1,2],[1,6],[1,1],[1,1],[1,1],[1,5],[1,2],[1,6],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,5],[1,2],[1,2]]];
bglayer1_1 = [[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,1],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,1],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]],[[0,2],[0,0],[0,0],[0,1],[0,1],[0,0],[0,0],[0,0],[0,0],[0,1],[0,2],[0,0],[0,0],[0,1],[0,1],[0,0],[0,0],[0,0],[0,0],[0,1]],[[0,2],[0,1],[0,1],[0,2],[0,2],[0,1],[0,0],[0,0],[0,1],[0,2],[0,2],[0,1],[0,1],[0,2],[0,2],[0,1],[0,0],[0,0],[0,1],[0,2]]];
sw = 450;
sh = 320;
tileWidth = tileHeight = 50;
stw = Math.ceil(sw / tileWidth);
sth = Math.ceil(sh / tileHeight);
spw = stw * tileWidth;
sph = sth * tileHeight;
guns = new Array();
guns[0] = {name:"MachineGun",gun:machineGun,reloadtime:5,speed:8,damage:10,sound:sgun};
guns[1] = {name:"AkimboMac10\'s",gun:uzi,reloadtime:4,speed:8,damage:9,sound:sgun};
guns[2] = {name:"Shotgun",gun:shotgun,reloadtime:25,speed:8,damage:15,sound:sshotgun};
guns[3] = {name:"ShotgunRockets",gun:shotgunRocket,reloadtime:40,speed:7,damage:40,sound:srocket};
guns[4] = {name:"GrenadeLauncher",gun:grenadeLauncher,reloadtime:30,speed:15,damage:75,sound:sgrenade};
guns[5] = {name:"RPG",gun:rpg,reloadtime:40,speed:4,damage:75,sound:sgrenade};
guns[6] = {name:"RocketLauncher",gun:rocketLauncher,reloadtime:50,speed:7,damage:100,sound:srocket};
guns[7] = {name:"SeekerLauncher",gun:seekerLauncher,reloadtime:55,speed:7,damage:100,sound:srocket};
guns[8] = {name:"FlameThrower",gun:flameThrower,reloadtime:1,speed:8,damage:2,sound:sflame,soundhold:1};
guns[9] = {name:"FireMines",gun:fireMines,reloadtime:100,speed:3,damage:5,sound:null};
guns[10] = {name:"A-BombLauncher",gun:aBombLauncher,reloadtime:150,speed:3,damage:300,sound:srocket};
guns[11] = {name:"RailGun",gun:railGun,reloadtime:75,speed:20,damage:150,sound:srailgun};
guns[12] = {name:"GrappleCannon",gun:grapple,reloadtime:250,speed:20,damage:300,sound:sgrapple};
guns[13] = {name:"ShoulderCannon",gun:shoulderCannon,reloadtime:100,speed:20,damage:300,sound:srailgun};
maxbullettime = 250;
whiteColor = {ra:"100",rb:"25",ga:"100",gb:"25",ba:"100",bb:"25",aa:"100",ab:"0"};
normalColor = {ra:"100",rb:"0",ga:"100",gb:"0",ba:"100",bb:"0",aa:"100",ab:"0"};
hitColor = {ra:"100",rb:"150",ga:"100",gb:"0",ba:"100",bb:"0",aa:"100",ab:"0"};
doubleDamageColor = {ra:"50",rb:"0",ga:"50",gb:"0",ba:"255",bb:"0",aa:"100",ab:"0"};
invunerableColor = {ra:"100",rb:"0",ga:"0",gb:"0",ba:"0",bb:"0",aa:"100",ab:"0"};
warpColor = {ra:"0",rb:"0",ga:"100",gb:"0",ba:"0",bb:"0",aa:"100",ab:"0"};
invColor = {ra:"-100",rb:"255",ga:"-100",gb:"255",ba:"-100",bb:"255",aa:"100",ab:"0"};
highscore = "High Score: " + hs * 100;
