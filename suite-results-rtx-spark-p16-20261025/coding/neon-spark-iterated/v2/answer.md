```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>NEON SPARK</title>
<style>
html,body{margin:0;padding:0;overflow:hidden;background:#020008;height:100%;}
canvas{display:block;cursor:crosshair;touch-action:none;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
'use strict';
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let W=0,H=0,DPR=1,horizonY=0;
let stars=[],mtnBack=[],mtnFront=[],sunCanvas=null,sunR=100,scanC=null;
let gridScroll=0,time=0;

function resize(){
  DPR=Math.min(window.devicePixelRatio||1,2);
  W=window.innerWidth;H=window.innerHeight;
  canvas.width=Math.floor(W*DPR);canvas.height=Math.floor(H*DPR);
  canvas.style.width=W+'px';canvas.style.height=H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);
  horizonY=H*0.62;
  sunR=Math.min(W,H)*0.28;
  buildStars();buildMountains();buildSun();buildScan();
  if(player){player.y=H*0.86;if(player.tx>W)player.tx=W/2;}
}
window.addEventListener('resize',resize);
window.addEventListener('contextmenu',e=>e.preventDefault());

function buildStars(){
  stars=[];const n=Math.floor(W*H/5500);
  for(let i=0;i<n;i++)stars.push({x:Math.random()*W,y:Math.random()*horizonY*0.92,
    r:Math.random()*1.8+0.3,ph:Math.random()*6.28,sp:Math.random()*2.5+0.5,
    c:Math.random()<0.12?'255,210,255':(Math.random()<0.5?'200,240,255':'255,255,255')});
}
function ridge(peak,step){
  const p=[];let x=-60;
  while(x<W+60){p.push({x,y:horizonY-(0.25+0.75*Math.random())*peak});x+=step;}
  p.push({x:W+60,y:horizonY});return p;
}
function buildMountains(){mtnBack=ridge(H*0.30,100);mtnFront=ridge(H*0.17,75);}

function buildSun(){
  const pad=100,size=Math.ceil(sunR*2+pad);
  sunCanvas=document.createElement('canvas');
  sunCanvas.width=sunCanvas.height=size;
  const s=sunCanvas.getContext('2d'),cx=size/2;
  const g=s.createLinearGradient(0,cx-sunR,0,cx+sunR);
  g.addColorStop(0,'#ffe14d');g.addColorStop(0.35,'#ff9500');g.addColorStop(0.7,'#ff3080');g.addColorStop(1,'#e000a0');
  s.fillStyle=g;
  s.beginPath();s.arc(cx,cx,sunR,0,Math.PI*2);s.fill();
  // Classic horizontal stripe cut-outs in lower half
  s.globalCompositeOperation='destination-out';
  s.fillStyle='#000';
  let y=cx+sunR*0.12,band=2,gap=9;
  while(y<cx+sunR){
    s.fillRect(0,y,size,band);
    y+=band+gap;
    band=Math.max(2,band*1.35);
    gap=Math.max(7,gap*1.3);
  }
  s.globalCompositeOperation='source-over';
}

function buildScan(){
  scanC=document.createElement('canvas');
  scanC.width=Math.max(2,Math.floor(W));scanC.height=Math.max(2,Math.floor(H));
  const s=scanC.getContext('2d');
  // Scanlines – every 2px, 28% black
  s.fillStyle='rgba(0,0,0,0.28)';
  for(let y=0;y<H;y+=2)s.fillRect(0,y,W,1);
  // Subtle RGB separation lines
  s.fillStyle='rgba(255,0,80,0.03)';
  for(let y=1;y<H;y+=2)s.fillRect(0,y,W,1);
  // Vignette
  const v=s.createRadialGradient(W/2,H/2,Math.min(W,H)*0.28,W/2,H/2,Math.max(W,H)*0.85);
  v.addColorStop(0,'rgba(0,0,0,0)');
  v.addColorStop(0.55,'rgba(0,0,0,0.12)');
  v.addColorStop(1,'rgba(0,0,0,0.72)');
  s.fillStyle=v;s.fillRect(0,0,W,H);
}

/* ================= AUDIO ================= */
let AC=null,master,musicG,sfxG,muted=false,musicOn=false,nb=null,mStep=0,mNext=0;
function initAudio(){
  if(AC)return;
  try{
    AC=new(window.AudioContext||window.webkitAudioContext)();
    master=AC.createGain();master.gain.value=0.7;master.connect(AC.destination);
    musicG=AC.createGain();musicG.gain.value=0.42;musicG.connect(master);
    sfxG=AC.createGain();sfxG.gain.value=0.85;sfxG.connect(master);
    mNext=AC.currentTime+0.1;
  }catch(e){}
}
function toggleMute(){muted=!muted;if(master)master.gain.value=muted?0:0.7;}
function mtof(m){return 440*Math.pow(2,(m-69)/12);}
function noiseBuf(){
  if(nb)return nb;
  nb=AC.createBuffer(1,AC.sampleRate,AC.sampleRate);
  const d=nb.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;
  return nb;
}
function sfxLaser(){
  if(!AC)return;const t=AC.currentTime;
  const o=AC.createOscillator();o.type='square';
  o.frequency.setValueAtTime(920,t);o.frequency.exponentialRampToValueAtTime(220,t+0.07);
  const g=AC.createGain();g.gain.setValueAtTime(0.08,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.08);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.09);
}
function sfxBoom(big){
  if(!AC)return;const t=AC.currentTime;
  const s=AC.createBufferSource();s.buffer=noiseBuf();
  const f=AC.createBiquadFilter();f.type='lowpass';
  f.frequency.setValueAtTime(big?1200:1800,t);f.frequency.exponentialRampToValueAtTime(40,t+(big?1.4:0.4));
  const g=AC.createGain();g.gain.setValueAtTime(big?0.7:0.4,t);
  g.gain.exponentialRampToValueAtTime(0.001,t+(big?1.5:0.45));
  s.connect(f);f.connect(g);g.connect(sfxG);s.start(t);s.stop(t+1.6);
  // Sub boom
  const o=AC.createOscillator();o.type='sine';
  o.frequency.setValueAtTime(big?80:120,t);o.frequency.exponentialRampToValueAtTime(30,t+(big?0.6:0.3));
  const g2=AC.createGain();g2.gain.setValueAtTime(big?0.5:0.2,t);
  g2.gain.exponentialRampToValueAtTime(0.001,t+(big?0.7:0.35));
  o.connect(g2);g2.connect(sfxG);o.start(t);o.stop(t+(big?0.8:0.4));
}
function sfxPower(){
  if(!AC)return;const t=AC.currentTime;
  [523.25,659.25,783.99,1046.5].forEach((f,i)=>{
    const o=AC.createOscillator();o.type='triangle';o.frequency.value=f;
    const g=AC.createGain();const t0=t+i*0.06;
    g.gain.setValueAtTime(0.13,t0);g.gain.exponentialRampToValueAtTime(0.001,t0+0.15);
    o.connect(g);g.connect(sfxG);o.start(t0);o.stop(t0+0.16);
  });
}
function sfxShield(){
  if(!AC)return;const t=AC.currentTime;
  const o=AC.createOscillator();o.type='sine';
  o.frequency.setValueAtTime(280,t);o.frequency.exponentialRampToValueAtTime(880,t+0.18);
  const g=AC.createGain();g.gain.setValueAtTime(0.18,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.22);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.23);
}
const BASSP=[0,0,12,0, 3,3,15,3, 5,5,17,5, 10,7,3,0];
function playStep(step,t){
  const b=BASSP[step];
  if(b>=0){
    const o=AC.createOscillator();o.type='sawtooth';o.frequency.value=mtof(33+b);
    const f=AC.createBiquadFilter();f.type='lowpass';f.frequency.value=320;
    const g=AC.createGain();g.gain.setValueAtTime(0.2,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.18);
    o.connect(f);f.connect(g);g.connect(musicG);o.start(t);o.stop(t+0.2);
  }
  if(step%4===0){
    const o=AC.createOscillator();o.type='sine';
    o.frequency.setValueAtTime(130,t);o.frequency.exponentialRampToValueAtTime(40,t+0.12);
    const g=AC.createGain();g.gain.setValueAtTime(0.5,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.15);
    o.connect(g);g.connect(musicG);o.start(t);o.stop(t+0.16);
  }
  if(step%4===2){
    const s=AC.createBufferSource();s.buffer=noiseBuf();
    const f=AC.createBiquadFilter();f.type='bandpass';f.frequency.value=1800;f.Q.value=0.8;
    const g=AC.createGain();g.gain.setValueAtTime(0.16,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.1);
    s.connect(f);f.connect(g);g.connect(musicG);s.start(t);s.stop(t+0.12);
  }
  if(step%2===1){
    const s=AC.createBufferSource();s.buffer=noiseBuf();
    const f=AC.createBiquadFilter();f.type='highpass';f.frequency.value=6500;
    const g=AC.createGain();g.gain.setValueAtTime(0.05,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.04);
    s.connect(f);f.connect(g);g.connect(musicG);s.start(t);s.stop(t+0.05);
  }
}
function scheduleMusic(){
  if(!AC||!musicOn)return;
  const spb=60/132/2;
  while(mNext<AC.currentTime+0.15){playStep(mStep,mNext);mStep=(mStep+1)%16;mNext+=spb;}
}

/* ================= STATE ================= */
let state='title',paused=false,titleT=0,goT=0;
let score=0,dispScore=0,best=0,combo=0,comboT=0,wave=0;
let waveState='inter',waveDelay=1.2,waveMsg='',waveMsgT=0;
let spawnQueue=[],enemies=[],pBullets=[],eBullets=[],powerups=[],particles=[],shocks=[],popups=[];
let boss=null,slowT=0,timeScale=1,hitStop=0,shake=0,flash=0,whiteFlash=0;
try{best=+localStorage.getItem('neonSparkBest')||0;}catch(e){}

const player={x:0,tx:0,y:0,lives:3,inv:0,fireCd:0,spread:0,shield:0,r:12};

function resetGame(){
  score=0;dispScore=0;combo=0;comboT=0;wave=0;
  enemies.length=0;pBullets.length=0;eBullets.length=0;powerups.length=0;
  particles.length=0;shocks.length=0;popups.length=0;
  spawnQueue.length=0;
  boss=null;slowT=0;timeScale=1;hitStop=0;shake=0;flash=0;whiteFlash=0;
  paused=false;
  player.x=player.tx=W/2;player.y=H*0.86;
  player.lives=3;player.inv=1.5;player.fireCd=0;player.spread=0;player.shield=0;
  waveState='inter';waveDelay=1.5;
  waveMsg='';waveMsgT=0;
}

function startGame(){
  initAudio();
  if(AC&&AC.state==='suspended')AC.resume();
  resetGame();
  state='playing';
  musicOn=true;mStep=0;mNext=AC?AC.currentTime+0.1:0;
}
function gameOver(){
  state='gameover';goT=0;musicOn=false;
  flash=1;whiteFlash=0.6;shake=40;
  sfxBoom(true);
  if(score>best){best=score;try{localStorage.setItem('neonSparkBest',best);}catch(e){}}
}
const mult=()=>1+Math.min(7,Math.floor(combo/5));

/* ================= FX ================= */
function boom(x,y,c,n,pw){
  for(let i=0;i<n;i++){
    const a=Math.random()*6.283,sp=(80+Math.random()*350)*pw;
    particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,
      life:0.35+Math.random()*0.8,max:1.15,r:1+Math.random()*3,c});
  }
  shocks.push({x,y,r:4,v:600*pw,life:0.5,max:0.5,c});
  // Second smaller ring
  if(pw>0.5)shocks.push({x,y,r:2,v:380*pw,life:0.35,max:0.35,c:'#fff'});
}
function bigBoom(x,y){
  const cols=['#ff2d95','#ff8a00','#00e5ff','#76B900','#ffe14d'];
  for(let r=0;r<5;r++){
    boom(x+(Math.random()-0.5)*60,y+(Math.random()-0.5)*40,cols[r%5],30,1.2+Math.random()*0.5);
  }
}
function popup(x,y,txt,c,size){popups.push({x,y,txt,c,size:size||16,life:1.2,max:1.2});}

function updateFx(dt){
  for(let i=particles.length-1;i>=0;i--){
    const p=particles[i];p.life-=dt;
    if(p.life<=0){particles.splice(i,1);continue;}
    p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=(1-2.5*dt);p.vy*=(1-2.5*dt);
  }
  for(let i=shocks.length-1;i>=0;i--){
    const s=shocks[i];s.life-=dt;s.r+=s.v*dt;s.v*=(1-4*dt);
    if(s.life<=0)shocks.splice(i,1);
  }
  for(let i=popups.length-1;i>=0;i--){
    const p=popups[i];p.life-=dt;p.y-=45*dt;
    if(p.life<=0)popups.splice(i,1);
  }
  shake=Math.max(0,shake-shake*7*dt-6*dt);
  flash=Math.max(0,flash-flash*2.5*dt);
  whiteFlash=Math.max(0,whiteFlash-whiteFlash*8*dt);
  if(waveMsgT>0)waveMsgT-=dt;
  if(comboT>0){comboT-=dt;if(comboT<=0)combo=0;}
  dispScore+=(score-dispScore)*Math.min(1,dt*12);
}

/* ================= WAVES / ENEMIES ================= */
function startWave(n){
  wave=n;
  spawnQueue.length=0;
  boss=null;
  if(n%5===0){
    const hp=35+n*8;
    boss={x:W/2,y:-160,ty:H*0.2,hp,max:hp,t:0,fireCd:2,phase:0,spiralA:0,spiralCd:0,dying:0,dieT:0,dieBoom:0};
    waveState='boss';
    waveMsg='⚠ BOSS WAVE ⚠';waveMsgT=2.5;
    sfxBoom(false);
    return;
  }
  waveState='spawning';
  const count=6+Math.floor(n*1.5);
  for(let i=0;i<count;i++){
    let type;
    if(n<=2){type=Math.random()<0.7?'weaver':'diver';}
    else{const r=Math.random();type=r<0.38?'weaver':(r<0.68?'diver':'shooter');}
    spawnQueue.push({t:i*0.5+Math.random()*0.25,type});
  }
  waveMsg='WAVE '+n;waveMsgT=2;
}
function spawnEnemy(type){
  const e={type,t:0,hp:1,x:W*0.15+Math.random()*W*0.7,y:-30,fireCd:1+Math.random()};
  if(type==='weaver'){e.amp=50+Math.random()*80;e.baseX=Math.max(e.amp+40,Math.min(W-e.amp-40,e.x));e.sp=75+Math.random()*60;}
  if(type==='diver'){e.sp=140+Math.random()*60;}
  if(type==='shooter'){e.ty=H*(0.1+Math.random()*0.22);e.drift=Math.random()*6.28;}
  enemies.push(e);
}
function killEnemy(e,idx){
  enemies.splice(idx,1);
  const col=e.type==='weaver'?'#ff2d95':(e.type==='diver'?'#00e5ff':'#ff8a00');
  boom(e.x,e.y,col,20,0.8);
  sfxBoom(false);
  shake=Math.min(30,shake+4);
  hitStop=Math.max(hitStop,0.045);
  whiteFlash=Math.max(whiteFlash,0.15);
  combo++;comboT=3;
  const pts=(e.type==='weaver'?100:e.type==='diver'?150:200)*mult();
  score+=pts;
  popup(e.x,e.y,'+'+pts,col,15);
  if(Math.random()<0.16){
    const r=Math.random();
    powerups.push({x:e.x,y:e.y,vy:70,type:r<0.4?'spread':(r<0.75?'shield':'slow'),t:0});
  }
}
function updateEnemies(dt){
  for(let i=enemies.length-1;i>=0;i--){
    const e=enemies[i];e.t+=dt;
    if(e.type==='weaver'){e.y+=e.sp*dt;e.x=e.baseX+Math.sin(e.t*2.2)*e.amp;}
    else if(e.type==='diver'){e.y+=e.sp*dt;e.sp+=55*dt;e.x+=(player.x-e.x)*Math.min(1,dt*2.2);}
    else{
      e.y+=(e.ty-e.y)*Math.min(1,dt*2);
      e.x+=Math.sin(e.t*0.8+e.drift)*45*dt;
      e.fireCd-=dt;
      if(e.fireCd<=0&&e.y>20){
        const a=Math.atan2(player.y-e.y,player.x-e.x);
        eBullets.push({x:e.x,y:e.y+12,vx:Math.cos(a)*180,vy:Math.sin(a)*180,r:5,c:'#ff8a00'});
        e.fireCd=1.6+Math.random()*0.9;
      }
    }
    if(e.y>H*0.9){enemies.splice(i,1);continue;}
    const dx=e.x-player.x,dy=e.y-player.y;
    if(dx*dx+dy*dy<(player.r+14)*(player.r+14)){hitPlayer();boom(e.x,e.y,'#ff2d95',14,0.5);enemies.splice(i,1);}
  }
}
function updateBoss(dt){
  if(!boss)return;
  boss.t+=dt;
  if(boss.dying>0){
    boss.dieT+=dt;
    if(boss.dieBoom>0){
      boss.dieBoom-=dt;
      if(boss.dieBoom<=0){
        const w=Math.min(W*0.4,320);
        const cols=['#ff2d95','#ff8a00','#00e5ff','#76B900','#ffe14d'];
        boom(boss.x+(Math.random()-0.5)*w,boss.y+(Math.random()-0.5)*w*0.4,
          cols[Math.floor(Math.random()*5)],25,1);
        sfxBoom(false);shake=Math.min(35,shake+7);
        hitStop=Math.max(hitStop,0.03);
        whiteFlash=Math.max(whiteFlash,0.1);
        boss.dieBoom=0.09;
      }
    }
    if(boss.dieT>1.4){
      bigBoom(boss.x,boss.y);
      flash=1;whiteFlash=0.8;shake=45;hitStop=0.25;sfxBoom(true);
      const pts=5000*mult();score+=pts;
      popup(boss.x,boss.y,'+'+pts,'#76B900',28);
      powerups.push({x:boss.x-50,y:boss.y,vy:70,type:'spread',t:0});
      powerups.push({x:boss.x+50,y:boss.y,vy:70,type:Math.random()<0.5?'shield':'slow',t:0});
      boss=null;waveState='inter';waveDelay=2.5;
    }
    return;
  }
  boss.y+=(boss.ty-boss.y)*Math.min(1,dt*1.5);
  boss.x=W/2+Math.sin(boss.t*0.55)*W*0.2;
  const frac=boss.hp/boss.max;
  boss.phase=frac>0.66?0:(frac>0.33?1:2);
  if(boss.phase===0){
    boss.fireCd-=dt;
    if(boss.fireCd<=0){
      const a=Math.atan2(player.y-boss.y,player.x-boss.x);
      for(let k=-2;k<=2;k++){
        const aa=a+k*0.22;
        eBullets.push({x:boss.x,y:boss.y+20,vx:Math.cos(aa)*220,vy:Math.sin(aa)*220,r:6,c:'#ff8a00'});
      }
      boss.fireCd=1.5;
    }
  }else if(boss.phase===1){
    boss.fireCd-=dt;
    if(boss.fireCd<=0){
      for(let k=0;k<20;k++){
        const a=k/20*6.283+boss.t*0.5;
        eBullets.push({x:boss.x,y:boss.y,vx:Math.cos(a)*170,vy:Math.sin(a)*170,r:5,c:'#ff2d95'});
      }
      boss.fireCd=1.3;
    }
  }else{
    boss.spiralCd-=dt;
    if(boss.spiralCd<=0){
      boss.spiralA+=0.4;
      for(let k=0;k<2;k++){
        const a=boss.spiralA+k*Math.PI;
        eBullets.push({x:boss.x,y:boss.y+10,vx:Math.cos(a)*200,vy:Math.sin(a)*200,r:5,c:'#76B900'});
      }
      boss.spiralCd=0.06;
    }
  }
  const dx=boss.x-player.x,dy=boss.y-player.y;
  const bw=Math.min(W*0.4,320)/2;
  if(Math.abs(dx)<bw+player.r&&dy<60+player.r&&dy>-40+player.r)hitPlayer();
}
function updateWaves(dt){
  if(boss){updateBoss(dt);return;}
  if(waveState==='inter'){
    waveDelay-=dt;
    if(waveDelay<=0)startWave(wave+1);
    return;
  }
  if(waveState==='spawning'){
    for(let i=spawnQueue.length-1;i>=0;i--){
      spawnQueue[i].t-=dt;
      if(spawnQueue[i].t<=0){
        spawnEnemy(spawnQueue[i].type);
        spawnQueue.splice(i,1);
      }
    }
    if(spawnQueue.length===0&&enemies.length===0){
      waveState='inter';waveDelay=2.2;
    }
  }
}

/* ================= PLAYER / BULLETS ================= */
function hitPlayer(){
  if(player.inv>0)return;
  if(player.shield>0){
    player.shield=0;sfxShield();
    boom(player.x,player.y,'#00e5ff',28,0.9);
    whiteFlash=Math.max(whiteFlash,0.1);
    return;
  }
  player.lives--;player.inv=2;
  shake=Math.min(40,shake+18);hitStop=Math.max(hitStop,0.1);
  whiteFlash=Math.max(whiteFlash,0.4);
  boom(player.x,player.y,'#ff2d95',50,1.4);
  sfxBoom(true);
  eBullets=eBullets.filter(b=>{const dx=b.x-player.x,dy=b.y-player.y;return dx*dx+dy*dy>220*220;});
  if(player.lives<=0)gameOver();
}
function updatePlayer(dt){
  const k=keys;
  let mv=0;
  if(k['a']||k['arrowleft'])mv-=1;
  if(k['d']||k['arrowright'])mv+=1;
  if(mv){player.x+=mv*580*dt;player.tx=player.x;}
  else player.x+=(player.tx-player.x)*Math.min(1,dt*10);
  player.x=Math.max(20,Math.min(W-20,player.x));
  player.inv=Math.max(0,player.inv-dt);
  player.spread=Math.max(0,player.spread-dt);
  player.shield=Math.max(0,player.shield-dt);
  for(let i=0;i<2;i++)
    particles.push({x:player.x+(Math.random()-0.5)*8,y:player.y+14,
      vx:(Math.random()-0.5)*45,vy:130+Math.random()*130,
      life:0.22+Math.random()*0.2,max:0.42,r:1.5+Math.random()*2.2,
      c:Math.random()<0.5?'#ff8a00':'#00e5ff'});
  player.fireCd-=dt;
  if(player.fireCd<=0){
    player.fireCd=player.spread>0?0.18:0.22;
    sfxLaser();
    const angles=[0];
    if(player.spread>0)angles.push(-0.28,0.28);
    for(const a of angles){
      pBullets.push({x:player.x+a*8,y:player.y-18,vx:Math.sin(a)*660,vy:-Math.cos(a)*660,r:3.5,c:'#00e5ff'});
    }
  }
}
function updateBullets(dt){
  for(let i=pBullets.length-1;i>=0;i--){
    const b=pBullets[i];b.x+=b.vx*dt;b.y+=b.vy*dt;
    if(b.y<-20||b.x<-20||b.x>W+20){pBullets.splice(i,1);continue;}
    let hit=false;
    for(let j=enemies.length-1;j>=0;j--){
      const e=enemies[j],dx=e.x-b.x,dy=e.y-b.y;
      if(dx*dx+dy*dy<20*20){
        hit=true;e.hp--;
        boom(b.x,b.y,'#00e5ff',6,0.3);
        if(e.hp<=0)killEnemy(e,j);
        break;
      }
    }
    if(!hit&&boss&&boss.dying<=0){
      const bw=Math.min(W*0.4,320)/2;
      if(Math.abs(b.x-boss.x)<bw&&Math.abs(b.y-boss.y)<60){
        hit=true;boss.hp--;
        boom(b.x,b.y,'#ff2d95',5,0.25);
        if(boss.hp<=0){boss.dying=1;boss.dieT=0;boss.dieBoom=0;}
      }
    }
    if(hit)pBullets.splice(i,1);
  }
  for(let i=eBullets.length-1;i>=0;i--){
    const b=eBullets[i];b.x+=b.vx*dt;b.y+=b.vy*dt;
    if(b.y>H+30||b.y<-40||b.x<-30||b.x>W+30){eBullets.splice(i,1);continue;}
    const dx=b.x-player.x,dy=b.y-player.y;
    if(dx*dx+dy*dy<(player.r+b.r)*(player.r+b.r)){
      eBullets.splice(i,1);hitPlayer();
    }
  }
}
function updatePowerups(dt){
  for(let i=powerups.length-1;i>=0;i--){
    const p=powerups[i];p.t+=dt;p.y+=p.vy*dt;
    if(p.y>H+30){powerups.splice(i,1);continue;}
    const dx=p.x-player.x,dy=p.y-player.y;
    if(dx*dx+dy*dy<32*32){
      powerups.splice(i,1);
      sfxPower();
      const col=p.type==='spread'?'#76B900':(p.type==='shield'?'#00e5ff':'#ff2d95');
      boom(p.x,p.y,col,18,0.5);
      if(p.type==='spread'){player.spread=10;popup(player.x,player.y-34,'SPREAD','#76B900',16);}
      else if(p.type==='shield'){player.shield=8;popup(player.x,player.y-34,'SHIELD','#00e5ff',16);}
      else{slowT=5;popup(player.x,player.y-34,'TIME WARP','#ff2d95',16);}
    }
  }
}

/* ================= DRAWING ================= */
function drawSky(){
  const g=ctx.createLinearGradient(0,0,0,horizonY);
  g.addColorStop(0,'#04000e');g.addColorStop(0.45,'#1a0338');g.addColorStop(1,'#4a0a5e');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,horizonY+2);
}
function drawStars(){
  ctx.save();
  for(const s of stars){
    const a=0.2+0.8*Math.abs(Math.sin(time*s.sp+s.ph));
    ctx.globalAlpha=a;
    ctx.fillStyle='rgb('+s.c+')';
    ctx.fillRect(s.x,s.y,s.r,s.r);
  }
  ctx.restore();
}
function drawSun(y,alpha){
  ctx.save();
  ctx.globalAlpha=alpha||1;
  ctx.beginPath();ctx.rect(0,0,W,horizonY);ctx.clip();
  const sx=W/2;
  ctx.globalCompositeOperation='lighter';
  const gl=ctx.createRadialGradient(sx,y,sunR*0.2,sx,y,sunR*2);
  gl.addColorStop(0,'rgba(255,80,190,0.3)');gl.addColorStop(0.5,'rgba(255,140,0,0.1)');gl.addColorStop(1,'rgba(255,80,190,0)');
  ctx.fillStyle=gl;ctx.fillRect(sx-sunR*2,y-sunR*2,sunR*4,sunR*4);
  ctx.globalCompositeOperation='source-over';
  ctx.drawImage(sunCanvas,sx-sunCanvas.width/2,y-sunCanvas.height/2);
  ctx.restore();
}
function drawMtn(pts,line,fill,off,alpha){
  ctx.save();ctx.globalAlpha=alpha||1;ctx.translate(off,0);
  ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
  for(const p of pts)ctx.lineTo(p.x,p.y);
  ctx.lineTo(W+80,horizonY+4);ctx.lineTo(-80,horizonY+4);ctx.closePath();
  ctx.fillStyle=fill;ctx.fill();
  ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
  for(const p of pts)ctx.lineTo(p.x,p.y);
  ctx.strokeStyle=line;ctx.lineWidth=1.5;
  ctx.shadowColor=line;ctx.shadowBlur=14;
  ctx.globalAlpha=(alpha||1)*0.8;ctx.stroke();
  ctx.restore();
}
function drawGrid(alpha){
  const gy=horizonY;
  const fg=ctx.createLinearGradient(0,gy,0,H);
  fg.addColorStop(0,'#170335');fg.addColorStop(0.35,'#0b0120');fg.addColorStop(1,'#020008');
  ctx.fillStyle=fg;ctx.fillRect(0,gy,W,H-gy);
  ctx.save();
  ctx.globalAlpha=alpha||1;
  ctx.globalCompositeOperation='lighter';
  ctx.strokeStyle='rgba(0,229,255,0.18)';ctx.lineWidth=1;
  const vp=W/2;
  for(let i=-14;i<=14;i++){
    ctx.beginPath();ctx.moveTo(vp+i*8,gy);ctx.lineTo(vp+i*(W/8.5),H+60);ctx.stroke();
  }
  const rows=15;
  for(let i=0;i<rows;i++){
    const t=(i+gridScroll)/rows;
    const y=gy+(H-gy)*t*t*t;
    const a=0.05+0.45*t*t;
    ctx.strokeStyle='rgba(255,45,149,'+a.toFixed(3)+')';
    ctx.lineWidth=1+t*2.2;
    ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();
  }
  ctx.strokeStyle='rgba(255,211,25,0.9)';
  ctx.shadowColor='#ffd319';ctx.shadowBlur=16;ctx.lineWidth=2.5;
  ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(W,gy);ctx.stroke();
  ctx.restore();
}
function shipPath(s){
  ctx.beginPath();
  ctx.moveTo(0,-20*s);
  ctx.quadraticCurveTo(7*s,-8*s,17*s,10*s);
  ctx.lineTo(8*s,6*s);
  ctx.lineTo(0,13*s);
  ctx.lineTo(-8*s,6*s);
  ctx.lineTo(-17*s,10*s);
  ctx.quadraticCurveTo(-7*s,-8*s,0,-20*s);
  ctx.closePath();
}
function drawShipShape(x,y,s,color){
  ctx.save();ctx.translate(x,y);
  ctx.shadowColor=color;ctx.shadowBlur=18;
  shipPath(s);
  ctx.fillStyle='rgba(0,16,38,0.94)';ctx.fill();
  ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();
  ctx.shadowColor='#76B900';ctx.shadowBlur=8;
  ctx.beginPath();ctx.arc(0,-6*s,3.4*s,0,7);
  ctx.fillStyle='#76B900';ctx.fill();
  ctx.restore();
}
function drawEnemy(e){
  ctx.save();ctx.translate(e.x,e.y);
  if(e.type==='weaver'){
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=16;
    ctx.rotate(Math.sin(e.t*2)*0.3);
    ctx.beginPath();ctx.moveTo(0,-15);ctx.lineTo(13,0);ctx.lineTo(0,15);ctx.lineTo(-13,0);ctx.closePath();
    ctx.fillStyle='rgba(60,0,30,0.9)';ctx.fill();
    ctx.strokeStyle='#ff2d95';ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,4,0,7);ctx.fillStyle='#ff2d95';ctx.fill();
  }else if(e.type==='diver'){
    ctx.shadowColor='#00e5ff';ctx.shadowBlur=16;
    ctx.beginPath();ctx.moveTo(0,17);ctx.lineTo(12,-11);ctx.lineTo(0,-5);ctx.lineTo(-12,-11);ctx.closePath();
    ctx.fillStyle='rgba(0,35,55,0.9)';ctx.fill();
    ctx.strokeStyle='#00e5ff';ctx.lineWidth=2;ctx.stroke();
  }else{
    ctx.shadowColor='#ff8a00';ctx.shadowBlur=16;
    ctx.rotate(e.t*0.8);
    ctx.beginPath();
    for(let k=0;k<6;k++){const a=k/6*6.283;const px=Math.cos(a)*14,py=Math.sin(a)*14;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}
    ctx.closePath();
    ctx.fillStyle='rgba(60,25,0,0.9)';ctx.fill();
    ctx.strokeStyle='#ff8a00';ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,5,0,7);ctx.fillStyle='#ffe14d';ctx.fill();
  }
  ctx.restore();
}
function drawBoss(){
  if(!boss)return;
  const w=Math.min(W*0.4,320),h=w*0.34,x=boss.x,y=boss.y;
  ctx.save();ctx.translate(x,y);
  const fl=1+0.06*Math.sin(boss.t*5);
  ctx.shadowColor='#ff2d95';ctx.shadowBlur=30;
  ctx.beginPath();
  ctx.moveTo(-w/2,0);ctx.lineTo(-w*0.35,-h*0.55);ctx.lineTo(-w*0.1,-h*0.28);
  ctx.lineTo(0,-h);ctx.lineTo(w*0.1,-h*0.28);ctx.lineTo(w*0.35,-h*0.55);
  ctx.lineTo(w/2,0);ctx.lineTo(w*0.3,h*0.45);ctx.lineTo(-w*0.3,h*0.45);ctx.closePath();
  const g=ctx.createLinearGradient(0,-h,0,h*0.5);
  g.addColorStop(0,'#3d0030');g.addColorStop(1,'#0a0018');
  ctx.fillStyle=g;ctx.fill();
  ctx.strokeStyle='#ff2d95';ctx.lineWidth=3;ctx.stroke();
  const core=ctx.createRadialGradient(0,0,0,0,0,h*0.45*fl);
  core.addColorStop(0,'#f0ffb0');core.addColorStop(0.4,'#76B900');core.addColorStop(1,'rgba(118,185,0,0)');
  ctx.fillStyle=core;
  ctx.beginPath();ctx.arc(0,0,h*0.45*fl,0,7);ctx.fill();
  ctx.restore();
  const bw=W*0.5,bx=(W-bw)/2,by=24,frac=Math.max(0,boss.hp/boss.max);
  ctx.save();
  ctx.fillStyle='rgba(0,0,0,0.6)';ctx.fillRect(bx,by,bw,12);
  const hg=ctx.createLinearGradient(bx,0,bx+bw,0);
  hg.addColorStop(0,'#ff2d95');hg.addColorStop(1,'#ff8a00');
  ctx.fillStyle=hg;ctx.shadowColor='#ff2d95';ctx.shadowBlur=14;
  ctx.fillRect(bx,by,bw*frac,12);
  ctx.strokeStyle='#ff2d95';ctx.lineWidth=1.5;ctx.strokeRect(bx,by,bw,12);
  ctx.restore();
}
function drawEntities(){
  ctx.save();ctx.globalCompositeOperation='lighter';
  for(const b of pBullets){
    ctx.shadowColor=b.c;ctx.shadowBlur=14;
    ctx.strokeStyle=b.c;ctx.lineWidth=3.5;
    ctx.beginPath();ctx.moveTo(b.x,b.y+12);ctx.lineTo(b.x,b.y-10);ctx.stroke();
    ctx.strokeStyle='rgba(255,255,255,0.7)';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.moveTo(b.x,b.y+6);ctx.lineTo(b.x,b.y-6);ctx.stroke();
  }
  for(const b of eBullets){
    ctx.shadowColor=b.c;ctx.shadowBlur=14;
    ctx.fillStyle=b.c;
    ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,7);ctx.fill();
    ctx.fillStyle='rgba(255,255,255,0.5)';
    ctx.beginPath();ctx.arc(b.x,b.y,b.r*0.4,0,7);ctx.fill();
  }
  ctx.restore();
  for(const e of enemies)drawEnemy(e);
  drawBoss();
  for(const p of powerups){
    const col=p.type==='spread'?'#76B900':(p.type==='shield'?'#00e5ff':'#ff2d95');
    const ch=p.type==='spread'?'S':(p.type==='shield'?'O':'T');
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(Math.sin(p.t*3)*0.5);
    ctx.shadowColor=col;ctx.shadowBlur=18;
    ctx.strokeStyle=col;ctx.lineWidth=2;
    ctx.strokeRect(-11,-11,22,22);
    ctx.fillStyle=col;ctx.font='bold 14px monospace';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(ch,0,1);
    ctx.restore();
  }
  if(state==='playing'){
    const blink=player.inv>0&&Math.floor(time*18)%2===0;
    if(!blink)drawShipShape(player.x,player.y,1,'#00e5ff');
    if(player.shield>0){
      ctx.save();ctx.globalCompositeOperation='lighter';
      const a=0.4+0.25*Math.sin(time*9)+(player.shield<1.5?(1-player.shield)*0.6:0);
      ctx.strokeStyle='rgba(0,229,255,'+Math.min(1,a).toFixed(2)+')';
      ctx.lineWidth=2.5;ctx.shadowColor='#00e5ff';ctx.shadowBlur=20;
      ctx.beginPath();ctx.arc(player.x,player.y,28+Math.sin(time*9)*2.5,0,7);ctx.stroke();
      ctx.restore();
    }
  }
}
function drawFx(){
  ctx.save();ctx.globalCompositeOperation='lighter';
  for(const p of particles){
    ctx.globalAlpha=Math.max(0,p.life/p.max);
    ctx.fillStyle=p.c;
    ctx.fillRect(p.x-p.r/2,p.y-p.r/2,p.r,p.r);
  }
  for(const s of shocks){
    const a=Math.max(0,s.life/s.max);
    ctx.globalAlpha=a*0.9;
    ctx.strokeStyle=s.c;ctx.lineWidth=2+a*4;
    ctx.shadowColor=s.c;ctx.shadowBlur=8;
    ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,7);ctx.stroke();
  }
  ctx.restore();ctx.globalAlpha=1;
}
function drawPopups(){
  ctx.save();ctx.textAlign='center';
  for(const p of popups){
    ctx.globalAlpha=Math.min(1,p.life/p.max*2);
    ctx.font='bold '+p.size+'px monospace';
    ctx.shadowColor=p.c;ctx.shadowBlur=12;
    ctx.fillStyle=p.c;
    ctx.fillText(p.txt,p.x,p.y);
  }
  ctx.restore();ctx.globalAlpha=1;
}
function drawCombo(){
  if(combo<2)return;
  const a=Math.min(1,comboT/0.5);
  const scale=1+0.08*Math.sin(time*6);
  const sz=Math.min(36,22+combo*0.8);
  ctx.save();
  ctx.globalAlpha=a;
  ctx.translate(W/2,60);ctx.scale(scale,scale);
  ctx.textAlign='center';
  ctx.font='bold '+sz+'px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=20;
  ctx.fillStyle='#76B900';
  ctx.fillText('×'+mult(),0,0);
  ctx.font='bold 13px monospace';
  ctx.fillStyle='rgba(118,185,0,0.8)';
  ctx.fillText('COMBO',0,-sz*0.55-4);
  // Bar
  const bw=60,frac=comboT/3;
  ctx.shadowBlur=4;
  ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(-bw/2,10,bw,4);
  ctx.fillStyle='#76B900';ctx.fillRect(-bw/2,10,bw*frac,4);
  ctx.restore();ctx.globalAlpha=1;
}
function drawHUD(){
  ctx.save();
  ctx.textAlign='left';
  ctx.font='bold 24px monospace';
  ctx.shadowColor='#00e5ff';ctx.shadowBlur=12;
  ctx.fillStyle='#00e5ff';
  ctx.fillText(Math.round(dispScore).toString().padStart(7,'0'),16,34);
  ctx.font='12px monospace';ctx.fillStyle='rgba(255,255,255,0.55)';ctx.shadowBlur=0;
  ctx.fillText('BEST '+best,16,52);
  ctx.textAlign='right';
  ctx.font='bold 20px monospace';
  ctx.shadowColor='#ff8a00';ctx.shadowBlur=12;ctx.fillStyle='#ff8a00';
  ctx.fillText('WAVE '+wave,W-16,34);
  for(let i=0;i<player.lives;i++)drawShipShape(30+i*32,80,0.5,'#00e5ff');
  let py=106;
  ctx.textAlign='left';ctx.font='11px monospace';
  if(player.spread>0){ctx.fillStyle='#76B900';ctx.fillText('SPREAD '+Math.ceil(player.spread)+'s',16,py);py+=15;}
  if(player.shield>0){ctx.fillStyle='#00e5ff';ctx.fillText('SHIELD '+Math.ceil(player.shield)+'s',16,py);py+=15;}
  if(slowT>0){ctx.fillStyle='#ff2d95';ctx.fillText('TIME WARP '+Math.ceil(slowT)+'s',16,py);py+=15;}
  if(muted){ctx.textAlign='right';ctx.fillStyle='rgba(255,255,255,0.45)';ctx.fillText('MUTED [M]',W-16,H-16);}
  ctx.restore();
  drawCombo();
}
function drawWaveMsg(){
  if(waveMsgT<=0)return;
  const total=waveMsgT>2?0:2.5-waveMsgT;
  const inA=Math.min(1,total*3.5);
  const outA=waveMsgT<0.5?waveMsgT*2:1;
  const scale=0.85+0.15*Math.min(1,total*2.5);
  const isBoss=waveMsg.indexOf('BOSS')>=0;
  ctx.save();
  ctx.globalAlpha=Math.min(inA,outA);
  ctx.translate(W/2,H*0.34);ctx.scale(scale,scale);
  ctx.textAlign='center';
  ctx.font='bold '+(isBoss?48:44)+'px monospace';
  const c=isBoss?'#ff8a00':'#00e5ff';
  ctx.shadowColor=c;ctx.shadowBlur=28;
  ctx.fillStyle=c;
  ctx.fillText(waveMsg,0,0);
  if(isBoss){
    ctx.font='bold 18px monospace';
    ctx.shadowBlur=12;
    ctx.fillStyle='#ffe14d';
    ctx.fillText('PREPARE FOR BATTLE',0,36);
  }
  ctx.restore();
}

/* ================= TITLE SCREEN ================= */
function easeOutCubic(t){return 1-Math.pow(1-t,3);}
function easeOutBack(t){const s=1.8;return 1+((t-1)*(t-1)*((s+1)*(t-1)+s));}

function drawTitle(){
  const t=titleT;
  // Phase 1: black fade in (0-0.6s)
  const fadeIn=Math.min(1,t/0.6);
  // Phase 2: sun rises (0.5-2.5s)
  const sunT=Math.min(1,Math.max(0,(t-0.5)/2));
  const sunEase=easeOutCubic(sunT);
  const sunY=horizonY+sunR*1.1 - sunEase*(sunR*1.3);
  const sunA=Math.min(1,sunT*2);
  // Phase 3: grid + mountains (0.8-2s)
  const gridA=Math.min(1,Math.max(0,(t-0.8)/1.2));
  // Phase 4: title (2-3.5s)
  const titleT2=Math.min(1,Math.max(0,(t-2)/1.5));
  const titleScale=easeOutBack(Math.min(1,titleT2));
  const titleA=Math.min(1,titleT2*2);
  // Phase 5: tagline (3-3.8s)
  const tagA=Math.min(1,Math.max(0,(t-3)/0.8));
  // Phase 6: CTA (3.8s+)
  const ctaA=Math.max(0,Math.min(1,(t-3.8)/0.6));

  // Black overlay for intro
  if(t<0.6){
    ctx.fillStyle='rgba(2,0,8,'+(1-fadeIn).toFixed(2)+')';
    ctx.fillRect(0,0,W,H);
  }

  drawSun(sunY,sunA);
  drawMtn(mtnBack,'rgba(255,45,149,0.5)','#160b2e',0,gridA);
  drawMtn(mtnFront,'rgba(0,229,255,0.55)','#0b0518',0,gridA);
  drawGrid(gridA);

  const cx=W/2,cy=horizonY-sunR*0.5;

  // Title with sweep effect
  if(titleT2>0){
    ctx.save();
    ctx.globalAlpha=titleA;
    const fs=Math.min(W*0.105,72);
    ctx.font='bold '+fs+'px monospace';
    ctx.textAlign='center';
    // Sweep line position
    const sweepX=cx - (1-titleT2)*(W*0.35);
    // Glow pulse
    const pulse=0.8+0.2*Math.sin(time*3);
    ctx.translate(cx,cy);ctx.scale(titleScale,titleScale);
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=35*pulse;
    ctx.fillStyle='#fff';
    ctx.fillText('NEON SPARK',0,0);
    ctx.shadowColor='#00e5ff';ctx.shadowBlur=18;
    ctx.strokeStyle='rgba(0,229,255,0.85)';ctx.lineWidth=1.5;
    ctx.strokeText('NEON SPARK',0,0);
    ctx.restore();
    // Sweep bright line
    if(titleT2<1){
      ctx.save();
      ctx.globalAlpha=(1-titleT2)*0.8;
      const swX=cx - (1-titleT2)*(W*0.4);
      ctx.strokeStyle='#fff';ctx.lineWidth=3;
      ctx.shadowColor='#00e5ff';ctx.shadowBlur=20;
      ctx.beginPath();ctx.moveTo(swX,cy-50);ctx.lineTo(swX,cy+30);ctx.stroke();
      ctx.restore();
    }
  }

  // Tagline
  if(tagA>0){
    ctx.save();
    ctx.globalAlpha=tagA;
    ctx.textAlign='center';
    ctx.font='16px monospace';
    ctx.shadowColor='#76B900';ctx.shadowBlur=10;
    ctx.fillStyle='#76B900';
    ctx.fillText('S Y N T H W A V E   A R C A D E',cx,cy+38);
    ctx.restore();
  }

  // CTA
  if(ctaA>0){
    const pa=0.35+0.65*Math.abs(Math.sin(time*2.2));
    ctx.save();
    ctx.globalAlpha=ctaA*pa;
    ctx.textAlign='center';
    ctx.font='bold 22px monospace';
    ctx.shadowColor='#ffe14d';ctx.shadowBlur=18;
    ctx.fillStyle='#ffe14d';
    ctx.fillText('CLICK OR TAP TO START',cx,H*0.72);
    ctx.globalAlpha=ctaA*0.6;
    ctx.font='12px monospace';
    ctx.shadowBlur=4;ctx.shadowColor='#00e5ff';
    ctx.fillStyle='#9fe8ff';
    ctx.fillText('MOUSE / TOUCH / WASD   ·   P PAUSE   ·   M MUTE',cx,H*0.72+28);
    if(best>0){
      ctx.globalAlpha=ctaA*0.85;
      ctx.font='bold 14px monospace';
      ctx.fillStyle='#00e5ff';ctx.shadowColor='#00e5ff';
      ctx.fillText('BEST SCORE: '+best,cx,H*0.78);
    }
    ctx.restore();
  }

  // Intro flash at t≈0.5
  if(t>0.4&&t<0.8){
    const fa=1-Math.abs(t-0.6)/0.2;
    if(fa>0){
      ctx.save();ctx.globalCompositeOperation='lighter';
      ctx.globalAlpha=fa*0.3;
      const fg=ctx.createRadialGradient(cx,horizonY,0,cx,horizonY,Math.max(W,H)*0.6);
      fg.addColorStop(0,'rgba(255,200,100,1)');fg.addColorStop(1,'rgba(255,50,200,0)');
      ctx.fillStyle=fg;ctx.fillRect(0,0,W,H);
      ctx.restore();
    }
  }
}

/* ================= OVERLAYS ================= */
function drawOverlays(){
  if(slowT>0&&state==='playing'){
    ctx.save();
    const a=Math.min(0.1,slowT*0.18);
    ctx.fillStyle='rgba(118,185,0,'+a.toFixed(3)+')';
    ctx.fillRect(0,0,W,H);
    ctx.strokeStyle='rgba(118,185,0,0.3)';ctx.lineWidth=5;
    ctx.strokeRect(3,3,W-6,H-6);
    ctx.restore();
  }
  // Chromatic flash
  if(flash>0){
    ctx.save();ctx.globalCompositeOperation='lighter';
    const o=16*flash;
    let g=ctx.createRadialGradient(W/2-o,H/2,0,W/2-o,H/2,Math.max(W,H)*0.75);
    g.addColorStop(0,'rgba(255,45,149,'+(0.35*flash).toFixed(3)+')');g.addColorStop(1,'rgba(255,45,149,0)');
    ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    g=ctx.createRadialGradient(W/2+o,H/2,0,W/2+o,H/2,Math.max(W,H)*0.75);
    g.addColorStop(0,'rgba(0,229,255,'+(0.35*flash).toFixed(3)+')');g.addColorStop(1,'rgba(0,229,255,0)');
    ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    ctx.restore();
  }
  // White flash
  if(whiteFlash>0){
    ctx.save();
    ctx.globalAlpha=whiteFlash*0.35;
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,W,H);
    ctx.restore();
  }
  if(scanC)ctx.drawImage(scanC,0,0,W,H);
}
function drawPause(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.65)';ctx.fillRect(0,0,W,H);
  ctx.textAlign='center';
  ctx.font='bold 48px monospace';
  ctx.shadowColor='#00e5ff';ctx.shadowBlur=26;
  ctx.fillStyle='#00e5ff';
  ctx.fillText('PAUSED',W/2,H*0.45);
  ctx.font='14px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';ctx.shadowBlur=0;
  ctx.fillText('PRESS P TO RESUME',W/2,H*0.52);
  ctx.restore();
}
function drawGameOver(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.74)';ctx.fillRect(0,0,W,H);
  const a=Math.min(1,goT*2.5);
  ctx.globalAlpha=a;
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.09,62)+'px monospace';
  ctx.shadowColor='#ff2d95';ctx.shadowBlur=32;
  ctx.fillStyle='#ff2d95';
  ctx.fillText('GAME OVER',W/2,H*0.34);
  ctx.font='bold 28px monospace';
  ctx.shadowColor='#00e5ff';ctx.shadowBlur=16;
  ctx.fillStyle='#00e5ff';
  ctx.fillText('FINAL SCORE  '+score,W/2,H*0.46);
  ctx.font='bold 18px monospace';
  const isBest=score>=best&&score>0;
  ctx.shadowColor=isBest?'#76B900':'rgba(255,255,255,0.3)';
  ctx.fillStyle=isBest?'#76B900':'rgba(255,255,255,0.65)';
  ctx.fillText(isBest?'★ NEW BEST ★':'BEST  '+best,W/2,H*0.53);
  if(goT>0.8){
    const pa=0.35+0.65*Math.abs(Math.sin(time*2.2));
    ctx.globalAlpha=pa*a;
    ctx.font='bold 22px monospace';
    ctx.shadowColor='#ffe14d';ctx.shadowBlur=18;
    ctx.fillStyle='#ffe14d';
    ctx.fillText('CLICK OR TAP TO RESTART',W/2,H*0.66);
  }
  ctx.restore();
}

/* ================= MAIN LOOP ================= */
let last=0;
function frame(ts){
  requestAnimationFrame(frame);
  const rdt=Math.min(0.05,(ts-last)/1000||0);
  last=ts;
  time+=rdt;
  gridScroll=(gridScroll+rdt*0.45)%1;
  scheduleMusic();

  let dt=rdt;
  if(hitStop>0){hitStop-=rdt;dt=0;}
  else{
    const target=slowT>0?0.32:1;
    timeScale+=(target-timeScale)*Math.min(1,rdt*7);
    dt=rdt*timeScale;
  }

  if(state==='title'){titleT+=rdt;}
  else if(state==='gameover'){goT+=rdt;updateFx(dt||rdt*0.4);}
  else if(state==='playing'&&!paused){
    slowT=Math.max(0,slowT-dt);
    updatePlayer(dt);
    updateWaves(dt);
    updateEnemies(dt);
    updateBullets(dt);
    updatePowerups(dt);
    updateFx(dt);
  }

  render();
}
function render(){
  ctx.save();
  if(shake>0)ctx.translate((Math.random()-0.5)*shake,(Math.random()-0.5)*shake);
  drawSky();
  drawStars();
  if(state==='title'){
    drawTitle();
  }else{
    drawSun(horizonY-sunR*0.35,1);
    drawMtn(mtnBack,'rgba(255,45,149,0.5)','#160b2e',Math.sin(time*0.04)*10,1);
    drawMtn(mtnFront,'rgba(0,229,255,0.55)','#0b0518',Math.sin(time*0.06+2)*14,1);
    drawGrid(1);
    drawEntities();
    drawFx();
    drawPopups();
    drawWaveMsg();
    drawHUD();
    if(state==='gameover')drawGameOver();
  }
  ctx.restore();
  drawOverlays();
  if(state==='playing'&&paused)drawPause();
}

/* ================= INPUT ================= */
const keys={};
function action(){
  if(state==='title'&&titleT>1)startGame();
  else if(state==='gameover'&&goT>0.8)startGame();
}
window.addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  keys[k]=true;
  if(k===' '||k==='enter'){e.preventDefault();action();}
  if(k==='p'&&state==='playing')paused=!paused;
  if(k==='m')toggleMute();
});
window.addEventListener('keyup',e=>{keys[e.key.toLowerCase()]=false;});
window.addEventListener('mousemove',e=>{if(state==='playing')player.tx=e.clientX;});
window.addEventListener('mousedown',()=>{initAudio();action();});
window.addEventListener('touchstart',e=>{
  e.preventDefault();initAudio();
  const t=e.touches[0];
  if(state==='playing')player.tx=t.clientX;
  action();
},{passive:false});
window.addEventListener('touchmove',e=>{
  e.preventDefault();
  const t=e.touches[0];
  if(state==='playing')player.tx=t.clientX;
},{passive:false});

resize();
player.x=player.tx=W/2;
player.y=H*0.86;
requestAnimationFrame(frame);
</script>
</body>
</html>
```