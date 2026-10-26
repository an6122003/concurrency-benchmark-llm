```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>NEON SPARK</title>
<style>
html,body{margin:0;padding:0;overflow:hidden;background:#020008;height:100%;}
canvas{display:block;cursor:crossroach;touch-action:none;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
'use strict';
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let W=0,H=0,DPR=1,horizonY=0,sunR=100,sunCY=0;
let stars=[],mtnBack=[],mtnFront=[],sunCanvas=null,scanC=null;
let gridScroll=0,time=0,last=0;

/* ================= PALETTES / CAMPAIGN ================= */
const sectors=[
 { name:'SUNSET BOULEVARD', sub:'The last sunset. Hold the light.', accent:'#ff2d95',
   pal:{ skyTop:'#04000e',skyMid:'#1c043a',skyHor:'#5a0c6e',
     sun:['#ffe14d','#ff9500','#ff3080','#e000a0'],
     grid:'255,45,149', gridV:'rgba(0,229,255,0.16)', horizon:'#ffd319',
     mtnBack:'rgba(255,45,149,0.55)', mtnBackFill:'#1a0b2e',
     mtnFront:'rgba(0,229,255,0.55)', mtnFrontFill:'#0d0518' },
   mix:{weaver:0.42,diver:0.28,shooter:0.30},
   boss:{name:'GLITCHWING', taunt:'“You are just a flicker.”', defeat:'“The… static… it slips away…”', color:'#ff2d95'} },
 { name:'CHROME CANYON', sub:'Steel canyons. Fast and cold.', accent:'#00e5ff',
   pal:{ skyTop:'#000a10',skyMid:'#00203a',skyHor:'#00506a',
     sun:['#d0fff5','#5ff0ff','#00b0ff','#0050ff'],
     grid:'0,229,255', gridV:'rgba(118,185,0,0.16)', horizon:'#a0fff0',
     mtnBack:'rgba(0,229,255,0.5)', mtnBackFill:'#031a24',
     mtnFront:'rgba(118,185,0,0.5)', mtnFrontFill:'#02141a' },
   mix:{weaver:0.25,diver:0.32,shooter:0.25,armored:0.18},
   boss:{name:'CANYON WARDEN', taunt:'“This canyon is mine.”', defeat:'“The canyon… will outlast us all.”', color:'#00e5ff'} },
 { name:'THE CORE', sub:'The heart of the signal. End this.', accent:'#ff8a00',
   pal:{ skyTop:'#0a0004',skyMid:'#300418',skyHor:'#6e0a2e',
     sun:['#fff2a0','#ff6a20','#ff2020','#7a0000'],
     grid:'255,138,0', gridV:'rgba(255,45,149,0.16)', horizon:'#ff5020',
     mtnBack:'rgba(255,138,0,0.5)', mtnBackFill:'#1a0308',
     mtnFront:'rgba(255,45,149,0.5)', mtnFrontFill:'#120208' },
   mix:{weaver:0.22,diver:0.26,shooter:0.22,armored:0.16,splitter:0.14},
   boss:{name:'THE STATIC', taunt:'“I am the noise between your stars.”', defeat:'“I… will… persist… in… the… void… forever.”', color:'#ff8a00', finale:true} }
];
let pal=sectors[0].pal;

const introLines=[
 'The Static is a corrupting signal — a living glitch',
 'eating the Neon Grid, district by district.',
 'The Grid is dark. Everyone is gone.',
 'Except you.  SPARK — the last light-runner.'
];
const totalIntroChars=introLines.join('').length;

/* ================= AUDIO ================= */
let AC=null,master,musicG,sfxG,muted=false,musicOn=false,nb=null,mStep=0,mNext=0,mTempo=132,musicMode=null;
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
  const g=AC.createGain();g.gain.setValueAtTime(0.07,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.08);
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
function sfxOver(){
  if(!AC)return;const t=AC.currentTime;
  const o=AC.createOscillator();o.type='sawtooth';
  o.frequency.setValueAtTime(120,t);o.frequency.exponentialRampToValueAtTime(1600,t+0.5);
  const g=AC.createGain();g.gain.setValueAtTime(0.3,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.6);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.6);
}
function sfxBlip(){
  if(!AC)return;const t=AC.currentTime;
  const o=AC.createOscillator();o.type='square';o.frequency.value=1800;
  const g=AC.createGain();g.gain.setValueAtTime(0.02,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.03);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.04);
}
function sfxClear(){
  if(!AC)return;const t=AC.currentTime;
  [659.25,880,1108.73,1318.5].forEach((f,i)=>{
    const o=AC.createOscillator();o.type='triangle';o.frequency.value=f;
    const g=AC.createGain();const t0=t+i*0.09;
    g.gain.setValueAtTime(0.12,t0);g.gain.exponentialRampToValueAtTime(0.001,t0+0.3);
    o.connect(g);g.connect(sfxG);o.start(t0);o.stop(t0+0.32);
  });
}
const TRACKS=[
 {tempo:128,bass:[0,0,12,0,3,3,15,3,5,5,17,5,10,7,3,0],wave:'sawtooth',cut:520,arp:48,arpNotes:[24,27,31,24]},
 {tempo:140,bass:[3,3,3,10,10,10,3,3,5,5,5,12,12,12,5,5],wave:'square',cut:780,arp:60,arpNotes:[40,43,47,40]},
 {tempo:152,bass:[0,0,3,3,5,5,3,3,0,0,12,12,10,10,7,7],wave:'sawtooth',cut:900,arp:72,arpNotes:[45,48,52,45]}
];
const BOSS_TRACK={tempo:168,bass:[0,0,0,7,0,0,0,7,12,12,12,7,10,10,7,3],wave:'square',cut:1400,arp:96,arpNotes:[3,10,7,12]};
function currentTrack(){if(musicMode==='boss')return BOSS_TRACK;return TRACKS[Math.max(0,Math.min(2,currentSector))];}
function playStep(step,t){
  const tr=currentTrack();
  const b=tr.bass[step];
  const o=AC.createOscillator();o.type=tr.wave;o.frequency.value=mtof(33+b);
  const o2=AC.createOscillator();o2.type=tr.wave;o2.frequency.value=mtof(33+b)/2;o2.detune.value=6;
  const f=AC.createBiquadFilter();f.type='lowpass';f.frequency.value=tr.cut;
  const g=AC.createGain();g.gain.setValueAtTime(0.16,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.18);
  const g2=AC.createGain();g2.gain.value=0.7;
  o.connect(f);o2.connect(g2);g2.connect(f);f.connect(g);g.connect(musicG);
  o.start(t);o.stop(t+0.2);o2.start(t);o2.stop(t+0.2);
  if(step%4===0){
    const d=AC.createOscillator();d.type='sine';
    d.frequency.setValueAtTime(140,t);d.frequency.exponentialRampToValueAtTime(45,t+0.12);
    const dg=AC.createGain();dg.gain.setValueAtTime(0.42,t);dg.gain.exponentialRampToValueAtTime(0.001,t+0.15);
    d.connect(dg);dg.connect(musicG);d.start(t);d.stop(t+0.16);
  }
  if(step%4===2){
    const s=AC.createBufferSource();s.buffer=noiseBuf();
    const nf=AC.createBiquadFilter();nf.type='bandpass';nf.frequency.value=1900;nf.Q.value=0.8;
    const ng=AC.createGain();ng.gain.setValueAtTime(0.13,t);ng.gain.exponentialRampToValueAtTime(0.001,t+0.1);
    s.connect(nf);nf.connect(ng);ng.connect(musicG);s.start(t);s.stop(t+0.12);
  }
  if(step%2===1){
    const s=AC.createBufferSource();s.buffer=noiseBuf();
    const hf=AC.createBiquadFilter();hf.type='highpass';hf.frequency.value=6500;
    const hg=AC.createGain();hg.gain.setValueAtTime(0.045,t);hg.gain.exponentialRampToValueAtTime(0.001,t+0.04);
    s.connect(hf);hf.connect(hg);hg.connect(musicG);s.start(t);s.stop(t+0.05);
  }
  const an=tr.arpNotes[step%4];
  const ao=AC.createOscillator();ao.type='triangle';ao.frequency.value=mtof(69+an);
  const af=AC.createBiquadFilter();af.type='lowpass';af.frequency.value=2600;
  const ag=AC.createGain();ag.gain.setValueAtTime(0.045,t);ag.gain.exponentialRampToValueAtTime(0.001,t+0.12);
  ao.connect(af);af.connect(ag);ag.connect(musicG);ao.start(t);ao.stop(t+0.14);
}
function scheduleMusic(){
  if(!AC||!musicOn)return;
  const spb=60/mTempo/2;
  while(mNext<AC.currentTime+0.15){playStep(mStep,mNext);mStep=(mStep+1)%16;mNext+=spb;}
}
function updateMusic(){
  const t=currentTrack();
  if(mTempo!==t.tempo)mTempo=t.tempo;
}

/* ================= STATE ================= */
let state='title',paused=false,titleT=0,goT=0,vicT=0,introT=0;
let sectorCardT=0,sectorCardDur=2.6;
let score=0,dispScore=0,best=0,combo=0,maxCombo=0,comboT=0;
let waveInSector=1,waveState='inter',waveDelay=1.2,waveMsg='',waveMsgT=0,taunt='';
let spawnQueue=[],enemies=[],pBullets=[],eBullets=[],powerups=[],particles=[],shocks=[],popups=[];
let boss=null,slowT=0,timeScale=1,hitStop=0,shake=0,flash=0,whiteFlash=0;
let shotsFired=0,shotsHit=0,runTime=0,hardMode=false,currentSector=0;
let upgradeCards=[];
let secKill=0,secHit=0,secFired=0,secNoHit=true,sectorClearT=0,clearPts=0;
let bossDefeatMsg='',defeatShown=false;
let isTouch=matchMedia('(pointer:coarse)').matches;
let lastTap=0;
try{best=+localStorage.getItem('neonSparkBest')||0;}catch(e){}

const player={x:0,tx:0,y:0,lives:3,inv:0,fireCd:0,spread:0,shield:0,r:12,upg:null,overdrive:0};

function resetGame(){
  score=0;dispScore=0;combo=0;maxCombo=0;comboT=0;
  waveInSector=1;waveState='inter';waveDelay=1.2;waveMsg='';waveMsgT=0;taunt='';
  spawnQueue.length=0;enemies.length=0;pBullets.length=0;eBullets.length=0;powerups.length=0;
  particles.length=0;shocks.length=0;popups.length=0;
  boss=null;slowT=0;timeScale=1;hitStop=0;shake=0;flash=0;whiteFlash=0;paused=false;
  shotsFired=0;shotsHit=0;runTime=0;secKill=0;secHit=0;secFired=0;secNoHit=true;
  bossDefeatMsg='';defeatShown=false;
  player.x=player.tx=W/2;player.y=H*0.86;
  player.lives=3;player.inv=1.5;player.fireCd=0;player.spread=0;player.shield=0;
  player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1};player.overdrive=0;
  mStep=0;if(AC)mNext=AC.currentTime+0.1;
}
function startRun(hard){
  hardMode=hard;
  initAudio();
  if(AC&&AC.state==='suspended')AC.resume();
  resetGame();
  state='intro';introT=0;musicOn=true;musicMode='sector';
}
function gameOver(){
  state='gameover';goT=0;musicOn=false;
  flash=1;whiteFlash=0.6;shake=40;
  sfxBoom(true);
  if(score>best){best=score;try{localStorage.setItem('neonSparkBest',best);}catch(e){}}
}
function victory(){
  state='victory';vicT=0;musicOn=false;
  flash=1;whiteFlash=0.8;
  const cols=['#ff2d95','#ff8a00','#00e5ff','#76B900'];
  for(let i=0;i<6;i++)setTimeout(()=>boom(W*0.2+Math.random()*W*0.6,H*0.2+Math.random()*H*0.4,cols[i],26,1.3),i*120);
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
  if(pw>0.5)shocks.push({x,y,r:2,v:380*pw,life:0.35,max:0.35,c:'#fff'});
}
function bigBoom(x,y){
  const cols=['#ff2d95','#ff8a00','#00e5ff','#76B900','#ffe14d'];
  for(let r=0;r<6;r++)boom(x+(Math.random()-0.5)*70,y+(Math.random()-0.5)*46,cols[r%5],28,1.2+Math.random()*0.5);
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

/* ================= WAVES / ENEMIES / BOSS ================= */
function rollMix(m){
  const r=Math.random();let acc=0;
  for(const t in m){acc+=m[t];if(r<=acc)return t;}
  return'weaver';
}
function enterSector(sec){
  currentSector=sec;setSectorPalette(sec);waveInSector=1;
  enemies.length=0;eBullets.length=0;pBullets.length=0;powerups.length=0;
  secKill=0;secHit=0;secFired=0;secNoHit=true;
  musicMode='sector';
  state='sector';sectorCardT=0;
}
function beginPlayingSector(){state='playing';waveState='inter';waveDelay=1.4;waveMsg='';waveMsgT=0;}
function setSectorPalette(i){pal=sectors[i].pal;buildSun();}
function beginWave(){
  const sec=sectors[currentSector];
  if(waveInSector>=5){
    spawnBoss(sec);waveState='boss';
    musicMode='boss';mStep=0;if(AC)mNext=AC.currentTime+0.05;
    waveMsg=sec.boss.name;waveMsgT=2.6;taunt=sec.boss.taunt;
    sfxBoom(false);
  }else{
    const diff=hardMode?1.6:1;
    const count=Math.round((6+currentSector*3+waveInSector*2)*diff);
    spawnQueue.length=0;
    for(let i=0;i<count;i++)spawnQueue.push({t:i*0.45+Math.random()*0.25,type:rollMix(sec.mix)});
    waveState='spawning';
    waveMsg='WAVE '+waveInSector;waveMsgT=1.6;
  }
}
function spawnEnemy(type){
  const e={type,t:0,hp:1,flash:0,x:W*0.15+Math.random()*W*0.7,y:-30,fireCd:1+Math.random(),dive:false,diveAt:Infinity,sp:160};
  if(type==='weaver'){e.amp=50+Math.random()*80;e.baseX=Math.max(e.amp+40,Math.min(W-e.amp-40,e.x));e.sp=75+Math.random()*60;}
  if(type==='diver'){e.sp=140+Math.random()*60;}
  if(type==='shooter'){e.ty=H*(0.1+Math.random()*0.22);e.drift=Math.random()*6.28;e.diveAt=7+Math.random()*6;}
  if(type==='armored'){e.hp=3;e.sp=55+Math.random()*30;}
  if(type==='splitter'){e.sp=60;e.drift=Math.random()*6.28;e.ty=H*(0.12+Math.random()*0.2);}
  enemies.push(e);
}
function spawnSplitterChild(x,y){
  const e={type:'split',t:0,hp:1,flash:0,x,y,sp:220,drift:(Math.random()-0.5)*2,fireCd:999,dive:false,diveAt:Infinity};
  enemies.push(e);
}
function spawnBoss(sec){
  const diff=hardMode?1.6:1;
  const hp=Math.round((38+currentSector*30)*diff+18);
  boss={id:currentSector,name:sec.boss.name,defeat:sec.boss.defeat,x:W/2,y:-180,ty:H*(0.16+currentSector*0.02),
    hp,max:hp,t:0,fireCd:1.5,spiralCd:0,spiralA:0,phase:0,dying:0,dieT:0,dieBoom:0,finale:!!sec.boss.finale};
}
function fb(x,y,vx,vy,c,r){eBullets.push({x,y,vx,vy,r:r||5,c});}
function aimedSpread(x,y,n,spread,speed,c){
  const base=Math.atan2(player.y-y,player.x-x);
  for(let k=-(n-1)/2;k<=(n-1)/2;k++)fb(x,y,Math.cos(base+k*spread)*speed,Math.sin(base+k*spread)*speed,c,5);
}
function ring(x,y,n,speed,c,off){
  for(let k=0;k<n;k++){const a=(off||0)+k/n*6.283;fb(x,y,Math.cos(a)*speed,Math.sin(a)*speed,c,5);}
}
function killEnemy(e,idx){
  enemies.splice(idx,1);
  const col=e.type==='weaver'?'#ff2d95':(e.type==='diver'?'#00e5ff':(e.type==='armored'?'#76B900':(e.type==='splitter'?'#ffe14d':(e.type==='split'?'#76B900':'#ff8a00'))));
  boom(e.x,e.y,col,e.type==='armored'?30:(e.type==='splitter'?26:20),e.type==='split'?0.5:0.8);
  sfxBoom(e.type==='armored'||e.type==='splitter');
  shake=Math.min(30,shake+4);
  hitStop=Math.max(hitStop,0.045);
  whiteFlash=Math.max(whiteFlash,0.15);
  combo++;maxCombo=Math.max(maxCombo,combo);comboT=3;
  player.overdrive=Math.min(1,player.overdrive+(0.05+combo*0.004)*player.upg.odGain);
  const pts=(e.type==='weaver'?100:e.type==='diver'?150:e.type==='shooter'?200:e.type==='armored'?300:e.type==='splitter'?250:120)*mult();
  score+=pts;
  popup(e.x,e.y,'+'+pts,col,15);
  secKill++;
  if(e.type==='splitter'){spawnSplitterChild(e.x-18,e.y);spawnSplitterChild(e.x+18,e.y);}
  if(Math.random()<0.16){
    const r=Math.random();
    powerups.push({x:e.x,y:e.y,vy:70,type:r<0.4?'spread':(r<0.75?'shield':'slow'),t:0});
  }
}
function hitPlayer(){
  if(player.inv>0)return;
  if(player.shield>0){
    player.shield=0;sfxShield();
    boom(player.x,player.y,'#00e5ff',28,0.9);
    whiteFlash=Math.max(whiteFlash,0.1);
    return;
  }
  player.lives--;player.inv=2;secNoHit=false;
  shake=Math.min(40,shake+18);hitStop=Math.max(hitStop,0.1);
  whiteFlash=Math.max(whiteFlash,0.4);
  boom(player.x,player.y,'#ff2d95',50,1.4);
  sfxBoom(true);
  eBullets=eBullets.filter(b=>{const dx=b.x-player.x,dy=b.y-player.y;return dx*dx+dy*dy>220*220;});
  if(player.lives<=0)gameOver();
}
function updateWaves(dt){
  if(boss){updateBoss(dt);return;}
  if(waveState==='inter'){
    waveDelay-=dt;
    if(waveDelay<=0)beginWave();
    return;
  }
  if(waveState==='spawning'){
    for(let i=spawnQueue.length-1;i>=0;i--){
      spawnQueue[i].t-=dt;
      if(spawnQueue[i].t<=0){spawnEnemy(spawnQueue[i].type);spawnQueue.splice(i,1);}
    }
    if(spawnQueue.length===0&&enemies.length===0){
      waveInSector++;waveState='inter';waveDelay=2.0;
    }
  }
}
function updateEnemies(dt){
  for(let i=enemies.length-1;i>=0;i--){
    const e=enemies[i];e.t+=dt;
    if(e.flash>0)e.flash-=dt;
    if(e.type==='weaver'){e.y+=e.sp*dt;e.x=e.baseX+Math.sin(e.t*2.2)*e.amp;}
    else if(e.type==='diver'){e.y+=e.sp*dt;e.sp+=55*dt;e.x+=(player.x-e.x)*Math.min(1,dt*2.2);}
    else if(e.type==='shooter'){
      if(!e.dive){
        e.y+=(e.ty-e.y)*Math.min(1,dt*2);
        e.x+=Math.sin(e.t*0.8+e.drift)*45*dt;
        e.fireCd-=dt;
        if(e.fireCd<=0&&e.y>20){
          const a=Math.atan2(player.y-e.y,player.x-e.x);
          eBullets.push({x:e.x,y:e.y+12,vx:Math.cos(a)*180,vy:Math.sin(a)*180,r:5,c:'#ff8a00'});
          e.fireCd=1.6+Math.random()*0.9;
        }
        if(e.t>e.diveAt){e.dive=true;e.sp=170;}
      }
      if(e.dive){e.y+=e.sp*dt;e.sp+=120*dt;e.x+=(player.x-e.x)*Math.min(1,dt*3);}
    }
    else if(e.type==='armored'){
      e.y+=e.sp*dt;
      e.x+=(player.x-e.x)*Math.min(1,dt*0.6);
    }
    else if(e.type==='splitter'){
      e.y+=(e.ty-e.y)*Math.min(1,dt*1.5);
      e.x+=Math.sin(e.t*0.9+e.drift)*55*dt;
    }
    else if(e.type==='split'){
      e.y+=e.sp*dt;e.sp+=80*dt;
      e.x+=Math.sin(e.t*8+e.drift)*120*dt;
    }
    if(e.t>30||e.y>H*0.92){enemies.splice(i,1);continue;}
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
        boom(boss.x+(Math.random()-0.5)*w,boss.y+(Math.random()-0.5)*w*0.4,cols[Math.floor(Math.random()*5)],25,1);
        sfxBoom(false);shake=Math.min(35,shake+7);hitStop=Math.max(hitStop,0.03);whiteFlash=Math.max(whiteFlash,0.1);
        boss.dieBoom=0.09;
      }
    }
    if(boss.dieT>1.4){
      bigBoom(boss.x,boss.y);
      flash=1;whiteFlash=0.85;shake=45;hitStop=0.25;sfxBoom(true);
      const pts=5000*mult();score+=pts;
      popup(boss.x,boss.y,'+'+pts,'#76B900',28);
      powerups.push({x:boss.x-50,y:boss.y,vy:70,type:'spread',t:0});
      powerups.push({x:boss.x+50,y:boss.y,vy:70,type:Math.random()<0.5?'shield':'slow',t:0});
      boss=null;
      if(currentSector===2)victory();
      else{state='sectorclear';sectorClearT=0;clearPts=0;musicMode='sector';sfxClear();}
    }
    return;
  }
  boss.y+=(boss.ty-boss.y)*Math.min(1,dt*1.5);
  const frac=boss.hp/boss.max;
  boss.phase=frac>0.66?0:(frac>0.33?1:2);
  switch(boss.id){
    case 0:
      boss.x=W/2+Math.sin(boss.t*0.5)*W*0.22;
      if(boss.phase===0){boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+24,5,0.2,210,'#ff2d95');boss.fireCd=1.4;}}
      else if(boss.phase===1){
        boss.fireCd-=dt;if(boss.fireCd<=0){for(let k=0;k<13;k++){const a=-Math.PI/2+(k-6)/6*1.6+Math.sin(boss.t*0.7)*0.5;fb(boss.x,boss.y,Math.cos(a)*190,Math.sin(a)*190,'#ff2d95');}boss.fireCd=0.8;}
        boss.spiralCd-=dt;if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+24,3,0.15,240,'#ff8a00');boss.spiralCd=2.0;}
      }else{
        boss.fireCd-=dt;if(boss.fireCd<=0){ring(boss.x,boss.y,20,160,'#ff2d95',boss.t);boss.fireCd=1.2;}
        boss.spiralCd-=dt;if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+24,5,0.18,240,'#ff8a00');boss.spiralCd=0.9;}
      }
      break;
    case 1:
      boss.x=W/2+Math.sin(boss.t*0.38)*W*0.26;
      if(boss.phase===0){boss.fireCd-=dt;if(boss.fireCd<=0){fb(boss.x,boss.y,Math.cos(2.4)*210,Math.sin(2.4)*210,'#00e5ff');fb(boss.x,boss.y,Math.cos(0.74)*210,Math.sin(0.74)*210,'#00e5ff');boss.fireCd=0.55;}}
      else if(boss.phase===1){
        boss.spiralCd-=dt;if(boss.spiralCd<=0){boss.spiralA+=0.5;for(let k=0;k<2;k++){const a=boss.spiralA+k*Math.PI;fb(boss.x,boss.y,Math.cos(a)*200,Math.sin(a)*200,'#00e5ff');}boss.spiralCd=0.06;}
        boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+20,3,0.16,230,'#76B900');boss.fireCd=1.6;}
      }else{
        boss.spiralCd-=dt;if(boss.spiralCd<=0){boss.spiralA+=0.45;for(let k=0;k<3;k++){const a=boss.spiralA+k*Math.PI*2/3;fb(boss.x,boss.y,Math.cos(a)*210,Math.sin(a)*210,'#00e5ff');}boss.spiralCd=0.07;}
        boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+20,5,0.18,240,'#ff2d95');boss.fireCd=1.0;}
      }
      break;
    case 2:
      boss.x=W/2+Math.sin(boss.t*0.55)*W*0.2+Math.sin(boss.t*1.8)*45;
      if(boss.phase===0){boss.fireCd-=dt;if(boss.fireCd<=0){for(let k=0;k<16;k++){const a=Math.random()*6.283;fb(boss.x,boss.y,Math.cos(a)*(150+Math.random()*120),Math.sin(a)*(150+Math.random()*120),Math.random()<0.5?'#ff8a00':'#ff2d95');}boss.fireCd=0.75;}}
      else if(boss.phase===1){
        boss.fireCd-=dt;if(boss.fireCd<=0){const yy=boss.y+20;for(let k=-6;k<=6;k++)fb(boss.x+k*26,yy,k*6,150,'#ff8a00');boss.fireCd=0.6;}
        boss.spiralCd-=dt;if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+20,3,0.15,240,'#ff2d95');boss.spiralCd=1.4;}
      }else{
        boss.spiralCd-=dt;if(boss.spiralCd<=0){boss.spiralA+=0.5;for(let k=0;k<4;k++){const a=boss.spiralA+k*Math.PI/2;fb(boss.x,boss.y,Math.cos(a)*200,Math.sin(a)*200,'#76B900');}boss.spiralCd=0.08;}
        boss.fireCd-=dt;if(boss.fireCd<=0){ring(boss.x,boss.y,24,150,'#ff8a00',boss.t);aimedSpread(boss.x,boss.y+20,5,0.18,250,'#ff2d95');boss.fireCd=0.9;}
      }
      break;
  }
  const bw=Math.min(W*0.4,320)/2;
  const dx=boss.x-player.x,dy=boss.y-player.y;
  if(Math.abs(dx)<bw+player.r&&dy<60+player.r&&dy>-40+player.r)hitPlayer();
}
function unleashOverdrive(){
  if(state!=='playing'||paused||player.overdrive<1)return;
  player.overdrive=0;
  flash=1;whiteFlash=0.7;shake=42;hitStop=0.14;
  bigBoom(W/2,H*0.5);
  shocks.push({x:player.x,y:player.y,r:20,v:2400,life:0.6,max:0.6,c:'#76B900'});
  sfxBoom(true);sfxOver();
  for(let i=enemies.length-1;i>=0;i--){
    const e=enemies[i];boom(e.x,e.y,'#76B900',16,0.7);
    const pts=(e.type==='weaver'?100:e.type==='diver'?150:e.type==='shooter'?200:e.type==='armored'?300:e.type==='splitter'?250:120)*mult();
    score+=pts;secKill++;enemies.splice(i,1);
  }
  eBullets.length=0;
  if(boss&&boss.dying===0){
    boss.hp-=Math.round(boss.max*0.30);
    boom(boss.x,boss.y,'#76B900',30,1);
    if(boss.hp<=0){boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;}
  }
}

/* ================= UPGRADES ================= */
function upgLevel(kind){
  const u=player.upg;
  if(kind==='rapid')return Math.min(5,Math.round(5/(u.fireRate*1.25)));
  if(kind==='twin')return u.twin;
  if(kind==='hull')return Math.min(6,player.lives-3);
  if(kind==='shield')return Math.min(5,Math.round(Math.log(u.shieldDur)/Math.log(1.5)));
  if(kind==='magnet')return u.magnet;
  if(kind==='od')return Math.min(5,Math.round(Math.log(u.odGain)/Math.log(1.4)));
  return 0;
}
function upgMax(kind){
  if(kind==='twin')return 3;
  if(kind==='hull')return 6;
  return 5;
}
const upgPool=[
 {label:'RAPID FIRE',desc:'-20% fire cooldown',color:'#00e5ff',kind:'rapid',apply:u=>{u.fireRate=Math.max(0.5,u.fireRate*0.8);}},
 {label:'TWIN CANNON',desc:'+1 laser bolt',color:'#ff2d95',kind:'twin',apply:u=>{u.twin=Math.min(3,u.twin+1);}},
 {label:'+1 HULL',desc:'Gain a spare life',color:'#76B900',kind:'hull',apply:u=>{player.lives++;}},
 {label:'AEGIS FIELD',desc:'Shields last 60% longer',color:'#00b0ff',kind:'shield',apply:u=>{u.shieldDur*=1.5;}},
 {label:'MAGNET CORE',desc:'Pull power-ups to you',color:'#ffe14d',kind:'magnet',apply:u=>{u.magnet+=1;}},
 {label:'OVERDRIVE CELL',desc:'Overdrive charges faster',color:'#ff8a00',kind:'od',apply:u=>{u.odGain*=1.4;}}
];
function buildUpgradeCards(){
  const arr=upgPool.slice();
  for(let i=arr.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]];}
  upgradeCards=arr.slice(0,3);
}
function upgradeCardRects(){
  const cw=Math.min(240,(W-40)/3),ch=170,gap=Math.max(8,(W-cw*3)/3);
  const total=cw*3+gap*2,x0=(W-total)/2,y=H*0.40;
  return upgradeCards.map((c,i)=>({x:x0+i*(cw+gap),y,w:cw,h:ch,i}));
}
function chooseCard(i){
  if(state!=='upgrade'||!upgradeCards[i])return;
  upgradeCards[i].apply(player.upg);
  player.overdrive=Math.min(1,player.overdrive+0.15);
  sfxPower();
  enterSector(currentSector+1);
}

/* ================= PLAYER / BULLETS / POWERUPS ================= */
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
    player.fireCd=(player.spread>0?0.16:0.22)*player.upg.fireRate;
    sfxLaser();
    const n=1+player.upg.twin;
    for(let i=0;i<n;i++){const a=(i-(n-1)/2)*0.13;pBullets.push({x:player.x+a*10,y:player.y-16,vx:Math.sin(a)*660,vy:-Math.cos(a)*660,r:3.5,c:'#00e5ff'});shotsFired++;secFired++;}
    if(player.spread>0){for(const a of[-0.3,0,0.3]){pBullets.push({x:player.x,y:player.y-16,vx:Math.sin(a)*660,vy:-Math.cos(a)*660,r:3.5,c:'#76B900'});shotsFired++;secFired++;}}
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
        hit=true;shotsHit++;secHit++;
        e.hp--;boom(b.x,b.y,'#00e5ff',6,0.3);
        if(e.type==='armored'){e.flash=0.15;shake=Math.min(20,shake+3);hitStop=Math.max(hitStop,0.03);}
        if(e.hp<=0)killEnemy(e,j);
        break;
      }
    }
    if(!hit&&boss&&boss.dying===0){
      const bw=Math.min(W*0.4,320)/2;
      if(Math.abs(b.x-boss.x)<bw&&Math.abs(b.y-boss.y)<60){
        hit=true;shotsHit++;secHit++;boss.hp--;boom(b.x,b.y,'#ff2d95',5,0.25);
        if(boss.hp<=0){boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;}
      }
    }
    if(hit)pBullets.splice(i,1);
  }
  for(let i=eBullets.length-1;i>=0;i--){
    const b=eBullets[i];b.x+=b.vx*dt;b.y+=b.vy*dt;
    if(b.y>H+30||b.y<-40||b.x<-30||b.x>W+30){eBullets.splice(i,1);continue;}
    const dx=b.x-player.x,dy=b.y-player.y;
    if(dx*dx+dy*dy<(player.r+b.r)*(player.r+b.r)){eBullets.splice(i,1);hitPlayer();}
  }
}
function updatePowerups(dt){
  for(let i=powerups.length-1;i>=0;i--){
    const p=powerups[i];p.t+=dt;p.y+=p.vy*dt;
    if(player.upg.magnet>0){const rad=120+player.upg.magnet*110;const dx=player.x-p.x,dy=player.y-p.y;const d=Math.hypot(dx,dy);if(d<rad&&d>1){p.x+=dx/d*300*dt;p.y+=dy/d*300*dt;}}
    if(p.y>H+30){powerups.splice(i,1);continue;}
    const dx=p.x-player.x,dy=p.y-player.y;
    if(dx*dx+dy*dy<32*32){
      powerups.splice(i,1);
      sfxPower();
      const col=p.type==='spread'?'#76B900':(p.type==='shield'?'#00e5ff':'#ff2d95');
      boom(p.x,p.y,col,18,0.5);
      if(p.type==='spread'){player.spread=10;popup(player.x,player.y-34,'SPREAD','#76B900',16);}
      else if(p.type==='shield'){player.shield=8*player.upg.shieldDur;popup(player.x,player.y-34,'SHIELD','#00e5ff',16);}
      else{slowT=5;popup(player.x,player.y-34,'TIME WARP','#ff2d95',16);}
    }
  }
}

/* ================= LAYOUT / BUILDERS ================= */
function hexA(hex,a){const h=hex.replace('#','');const r=parseInt(h.substr(0,2),16),g=parseInt(h.substr(2,2),16),b=parseInt(h.substr(4,2),16);return`rgba(${r},${g},${b},${a})`;}
function resize(){
  DPR=Math.min(window.devicePixelRatio||1,2);
  W=window.innerWidth;H=window.innerHeight;
  canvas.width=Math.floor(W*DPR);canvas.height=Math.floor(H*DPR);
  canvas.style.width=W+'px';canvas.style.height=H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);
  horizonY=H*0.62;
  sunR=Math.min(W,H)*0.28;
  sunCY=horizonY-sunR*0.45;
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
function buildMountains(){mtnBack=ridge(H*0.11,90);mtnFront=ridge(H*0.07,70);}
function buildSun(){
  const pad=100,size=Math.ceil(sunR*2+pad);
  sunCanvas=document.createElement('canvas');
  sunCanvas.width=sunCanvas.height=size;
  const s=sunCanvas.getContext('2d'),cx=size/2;
  const g=s.createLinearGradient(0,cx-sunR,0,cx+sunR);
  g.addColorStop(0,pal.sun[0]);g.addColorStop(0.35,pal.sun[1]);g.addColorStop(0.7,pal.sun[2]);g.addColorStop(1,pal.sun[3]);
  s.fillStyle=g;
  s.beginPath();s.arc(cx,cx,sunR,0,Math.PI*2);s.fill();
  s.globalCompositeOperation='destination-out';
  s.fillStyle='#000';
  let y=cx+sunR*0.03,band=Math.max(2,sunR*0.02),gap=sunR*0.035;
  while(y<cx+sunR){
    s.fillRect(0,y,size,band);
    y+=band+gap;
    band=Math.max(2,band*1.5);gap*=1.35;
  }
  s.globalCompositeOperation='source-over';
}
function buildScan(){
  scanC=document.createElement('canvas');
  scanC.width=Math.max(2,Math.floor(W));scanC.height=Math.max(2,Math.floor(H));
  const s=scanC.getContext('2d');
  s.fillStyle='rgba(0,0,0,0.28)';
  for(let y=0;y<H;y+=2)s.fillRect(0,y,W,1);
  s.fillStyle='rgba(255,0,80,0.03)';
  for(let y=1;y<H;y+=2)s.fillRect(0,y,W,1);
  const v=s.createRadialGradient(W/2,H/2,Math.min(W,H)*0.28,W/2,H/2,Math.max(W,H)*0.85);
  v.addColorStop(0,'rgba(0,0,0,0)');v.addColorStop(0.55,'rgba(0,0,0,0.12)');v.addColorStop(1,'rgba(0,0,0,0.72)');
  s.fillStyle=v;s.fillRect(0,0,W,H);
}

/* ================= DRAWING ================= */
function drawSky(){
  const g=ctx.createLinearGradient(0,0,0,horizonY);
  g.addColorStop(0,pal.skyTop);g.addColorStop(0.5,pal.skyMid);g.addColorStop(1,pal.skyHor);
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
  gl.addColorStop(0,hexA(pal.sun[2],0.35));gl.addColorStop(0.5,hexA(pal.sun[1],0.12));gl.addColorStop(1,hexA(pal.sun[2],0));
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
  fg.addColorStop(0,hexA(pal.skyHor,0.5));fg.addColorStop(0.35,'#0b0120');fg.addColorStop(1,'#020008');
  ctx.fillStyle=fg;ctx.fillRect(0,gy,W,H-gy);
  ctx.save();
  ctx.globalAlpha=alpha||1;
  ctx.globalCompositeOperation='lighter';
  ctx.strokeStyle=pal.gridV;ctx.lineWidth=1;
  const vp=W/2;
  for(let i=-14;i<=14;i++){
    ctx.beginPath();ctx.moveTo(vp+i*8,gy);ctx.lineTo(vp+i*(W/8.5),H+60);ctx.stroke();
  }
  const rows=15;
  for(let i=0;i<rows;i++){
    const t=(i+gridScroll)/rows;
    const y=gy+(H-gy)*t*t*t;
    const a=0.05+0.45*t*t;
    ctx.strokeStyle='rgba('+pal.grid+','+a.toFixed(3)+')';
    ctx.lineWidth=1+t*2.2;
    ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();
  }
  ctx.strokeStyle=pal.horizon;
  ctx.shadowColor=pal.horizon;ctx.shadowBlur=16;ctx.lineWidth=2.5;
  ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(W,gy);ctx.stroke();
  ctx.restore();
}
function drawBackground(){
  drawSky();drawStars();
  drawSun(sunCY,1);
  drawMtn(mtnBack,pal.mtnBack,pal.mtnBackFill,Math.sin(time*0.04)*10,1);
  drawMtn(mtnFront,pal.mtnFront,pal.mtnFrontFill,Math.sin(time*0.06+2)*14,1);
  drawGrid(1);
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
  }else if(e.type==='shooter'){
    ctx.shadowColor='#ff8a00';ctx.shadowBlur=16;
    ctx.rotate(e.t*0.8);
    ctx.beginPath();
    for(let k=0;k<6;k++){const a=k/6*6.283;const px=Math.cos(a)*14,py=Math.sin(a)*14;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}
    ctx.closePath();
    ctx.fillStyle='rgba(60,25,0,0.9)';ctx.fill();
    ctx.strokeStyle='#ff8a00';ctx.lineWidth=2;ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,5,0,7);ctx.fillStyle='#ffe14d';ctx.fill();
  }else if(e.type==='armored'){
    ctx.shadowColor='#76B900';ctx.shadowBlur=18;
    ctx.beginPath();
    for(let k=0;k<6;k++){const a=k/6*6.283+Math.PI/6;const px=Math.cos(a)*17,py=Math.sin(a)*17;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}
    ctx.closePath();
    ctx.fillStyle='rgba(20,40,0,0.92)';ctx.fill();
    ctx.strokeStyle='#76B900';ctx.lineWidth=3;ctx.stroke();
    ctx.strokeStyle='#4a8a00';ctx.lineWidth=1.5;
    for(let k=0;k<6;k++){const a=k/6*6.283+Math.PI/6;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*15,Math.sin(a)*15);ctx.stroke();}
    ctx.beginPath();ctx.arc(0,0,6,0,7);ctx.fillStyle='#76B900';ctx.fill();
    const hp=Math.min(3,e.hp);
    for(let k=0;k<hp;k++){
      ctx.beginPath();ctx.arc(-8+k*8,-22,2.2,0,7);
      ctx.fillStyle='#76B900';ctx.fill();
    }
    if(e.flash>0){
      ctx.globalCompositeOperation='lighter';
      ctx.beginPath();
      for(let k=0;k<6;k++){const a=k/6*6.283+Math.PI/6;const px=Math.cos(a)*18,py=Math.sin(a)*18;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}
      ctx.closePath();
      ctx.fillStyle='rgba(255,255,255,'+Math.min(1,e.flash*6).toFixed(2)+')';ctx.fill();
    }
  }else if(e.type==='splitter'){
    ctx.shadowColor='#ffe14d';ctx.shadowBlur=18;
    ctx.rotate(e.t*1.2);
    ctx.beginPath();
    for(let k=0;k<8;k++){const a=k/8*6.283;const rr=k%2?11:17;const px=Math.cos(a)*rr,py=Math.sin(a)*rr;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}
    ctx.closePath();
    ctx.fillStyle='rgba(50,40,0,0.9)';ctx.fill();
    ctx.strokeStyle='#ffe14d';ctx.lineWidth=2.5;ctx.stroke();
    ctx.beginPath();ctx.moveTo(-10,0);ctx.lineTo(10,0);ctx.moveTo(0,-10);ctx.lineTo(0,10);
    ctx.strokeStyle='#ffe14d';ctx.lineWidth=1.5;ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,4,0,7);ctx.fillStyle='#ffe14d';ctx.fill();
  }else if(e.type==='split'){
    ctx.shadowColor='#76B900';ctx.shadowBlur=12;
    ctx.rotate(e.t*6);
    ctx.beginPath();ctx.moveTo(0,-9);ctx.lineTo(7,0);ctx.lineTo(0,9);ctx.lineTo(-7,0);ctx.closePath();
    ctx.fillStyle='rgba(20,40,0,0.9)';ctx.fill();
    ctx.strokeStyle='#76B900';ctx.lineWidth=1.8;ctx.stroke();
  }
  if(e.type!=='armored'&&e.flash>0){
    ctx.globalCompositeOperation='lighter';
    ctx.beginPath();ctx.arc(0,0,15,0,7);
    ctx.fillStyle='rgba(255,255,255,'+Math.min(1,e.flash*6).toFixed(2)+')';ctx.fill();
  }
  ctx.restore();
}
function drawBoss(){
  if(!boss)return;
  const x=boss.x,y=boss.y;
  ctx.save();ctx.translate(x,y);
  const fl=1+0.06*Math.sin(boss.t*6);
  if(boss.id===0){
    const w=Math.min(W*0.4,300)/2,wing=Math.sin(boss.t*3)*0.4;
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=28;
    ctx.fillStyle='rgba(50,0,30,0.85)';ctx.strokeStyle='#ff2d95';ctx.lineWidth=2.5;
    for(const sgn of[-1,1]){
      ctx.save();ctx.scale(sgn,1);
      ctx.beginPath();ctx.moveTo(0,-8);ctx.lineTo(w,-42+wing*28);ctx.lineTo(w*0.7,12);ctx.lineTo(0,10);ctx.closePath();
      ctx.fill();ctx.stroke();ctx.restore();
    }
    ctx.beginPath();ctx.moveTo(0,-30);ctx.lineTo(20,0);ctx.lineTo(0,30);ctx.lineTo(-20,0);ctx.closePath();
    ctx.fillStyle='#1a0018';ctx.fill();ctx.stroke();
    const core=ctx.createRadialGradient(0,0,0,0,0,16*fl);
    core.addColorStop(0,'#f0ffb0');core.addColorStop(0.5,'#76B900');core.addColorStop(1,'rgba(118,185,0,0)');
    ctx.fillStyle=core;ctx.beginPath();ctx.arc(0,0,16*fl,0,7);ctx.fill();
  }else if(boss.id===1){
    const r=92;
    ctx.shadowColor='#00e5ff';ctx.shadowBlur=28;
    function hex(rr,rot){ctx.beginPath();for(let k=0;k<6;k++){const a=rot+k/6*6.283;const px=Math.cos(a)*rr,py=Math.sin(a)*rr;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}ctx.closePath();}
    hex(r,boss.t*0.2);ctx.fillStyle='rgba(0,30,40,0.9)';ctx.fill();ctx.strokeStyle='#00e5ff';ctx.lineWidth=3;ctx.stroke();
    hex(r*0.62,-boss.t*0.4);ctx.strokeStyle='#76B900';ctx.lineWidth=2;ctx.stroke();
    const core=ctx.createRadialGradient(0,0,0,0,0,r*0.4*fl);
    core.addColorStop(0,'#e8fff8');core.addColorStop(0.5,'#00e5ff');core.addColorStop(1,'rgba(0,229,255,0)');
    ctx.fillStyle=core;ctx.beginPath();ctx.arc(0,0,r*0.4*fl,0,7);ctx.fill();
  }else{
    const R=112;
    ctx.shadowColor='#ff8a00';ctx.shadowBlur=30;
    ctx.fillStyle='#0a0004';ctx.beginPath();ctx.arc(0,0,R,0,7);ctx.fill();
    ctx.strokeStyle='#ff2d95';ctx.lineWidth=3;ctx.stroke();
    ctx.globalAlpha=0.5;
    for(let k=0;k<90;k++){const a=Math.random()*6.283,rr=Math.sqrt(Math.random())*R;const px=Math.cos(a)*rr,py=Math.sin(a)*rr;
      ctx.fillStyle=Math.random()<0.5?'#ff8a00':'#76B900';ctx.fillRect(px,py,3,3);}
    ctx.globalAlpha=1;
    ctx.fillStyle='#fff';ctx.shadowColor='#fff';ctx.shadowBlur=14;
    ctx.fillRect(-34,-18,22,10);ctx.fillRect(12,-18,22,10);
    ctx.strokeStyle='#ff2d95';ctx.shadowColor='#ff2d95';ctx.shadowBlur=12;ctx.lineWidth=3;
    for(let k=-2;k<=2;k++){ctx.beginPath();ctx.moveTo(k*18,18);ctx.lineTo(k*18+(Math.random()*8-4),34);ctx.stroke();}
  }
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
    ctx.strokeStyle=col;ctx.lineWidth=2;ctx.strokeRect(-11,-11,22,22);
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
  const sz=Math.min(34,20+combo*0.7);
  const cy=(boss||waveState==='boss')?112:84;
  ctx.save();
  ctx.globalAlpha=a;
  ctx.translate(W/2,cy);ctx.scale(scale,scale);
  ctx.textAlign='center';
  ctx.font='bold '+sz+'px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=20;
  ctx.fillStyle='#76B900';
  ctx.fillText('×'+mult(),0,0);
  ctx.font='bold 11px monospace';
  ctx.fillStyle='rgba(118,185,0,0.8)';
  ctx.fillText('COMBO',0,-sz*0.55-4);
  const bw=54,frac=comboT/3;
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
  const isBoss=(waveState==='boss');
  const secX=isBoss?W-16:W/2,secA=isBoss?'right':'center';
  const secY=isBoss?46:26;
  ctx.textAlign=secA;
  const acc=sectors[currentSector].accent;
  ctx.font='bold 16px monospace';
  ctx.shadowColor=acc;ctx.shadowBlur=10;ctx.fillStyle=acc;
  ctx.fillText('SECTOR '+(currentSector+1)+' / 3',secX,secY);
  ctx.font='12px monospace';ctx.shadowBlur=0;ctx.fillStyle='rgba(255,255,255,0.7)';
  ctx.fillText(isBoss?'BOSS':'WAVE '+waveInSector+' / 4',secX,secY+18);
  for(let i=0;i<player.lives;i++)drawShipShape(30+i*32,80,0.5,'#00e5ff');
  let py=106;
  ctx.textAlign='left';ctx.font='11px monospace';
  if(player.spread>0){ctx.fillStyle='#76B900';ctx.fillText('SPREAD '+Math.ceil(player.spread)+'s',16,py);py+=15;}
  if(player.shield>0){ctx.fillStyle='#00e5ff';ctx.fillText('SHIELD '+Math.ceil(player.shield)+'s',16,py);py+=15;}
  if(slowT>0){ctx.fillStyle='#ff2d95';ctx.fillText('TIME WARP '+Math.ceil(slowT)+'s',16,py);py+=15;}
  const ow=Math.min(W*0.4,340),ox=(W-ow)/2,oy=H-30;
  ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(ox,oy,ow,10);
  const fr=player.overdrive;
  ctx.fillStyle=fr>=1?'#76B900':'rgba(118,185,0,0.7)';
  ctx.shadowColor='#76B900';ctx.shadowBlur=fr>=1?18:6;
  ctx.fillRect(ox,oy,ow*fr,10);
  ctx.shadowBlur=0;ctx.strokeStyle='rgba(118,185,0,0.6)';ctx.lineWidth=1;ctx.strokeRect(ox,oy,ow,10);
  ctx.font='11px monospace';ctx.textAlign='center';
  if(fr>=1){
    const pa=0.5+0.5*Math.abs(Math.sin(time*6));ctx.globalAlpha=pa;ctx.fillStyle='#76B900';ctx.shadowColor='#76B900';ctx.shadowBlur=8;
    ctx.fillText('OVERDRIVE READY — SPACE / TAP',W/2,oy-8);ctx.globalAlpha=1;
  }else{ctx.fillStyle='rgba(118,185,0,0.6)';ctx.shadowBlur=0;ctx.fillText('OVERDRIVE',W/2,oy-8);}
  if(muted){ctx.textAlign='right';ctx.fillStyle='rgba(255,255,255,0.45)';ctx.fillText('MUTED [M]',W-16,H-16);}
  ctx.restore();
  drawCombo();
}
function drawOverdriveBtn(){
  if(!isTouch||!player||player.overdrive<1)return;
  const bx=W-70,by=H-90,r=38;
  const pulse=0.7+0.3*Math.abs(Math.sin(time*5));
  ctx.save();
  ctx.globalAlpha=0.92*pulse;
  ctx.beginPath();ctx.arc(bx,by,r,0,7);
  ctx.fillStyle='rgba(20,50,0,0.5)';ctx.fill();
  ctx.strokeStyle='#76B900';ctx.lineWidth=3;ctx.shadowColor='#76B900';ctx.shadowBlur=22;
  ctx.stroke();
  ctx.font='bold 13px monospace';ctx.textAlign='center';ctx.fillStyle='#76B900';
  ctx.fillText('OVER',bx,by-4);ctx.fillText('DRIVE',bx,by+12);
  ctx.restore();
}
function drawWaveMsg(){
  if(waveMsgT>0){
    const total=waveMsgT>2?0:2.6-waveMsgT;
    const inA=Math.min(1,total*4);
    const outA=waveMsgT<0.5?waveMsgT*2:1;
    const scale=0.9+0.1*Math.min(1,total*2.5);
    ctx.save();ctx.globalAlpha=Math.min(inA,outA);
    ctx.translate(W/2,H*0.32);ctx.scale(scale,scale);
    ctx.textAlign='center';
    ctx.font='bold 44px monospace';
    const c=sectors[currentSector].accent;
    ctx.shadowColor=c;ctx.shadowBlur=26;ctx.fillStyle=c;
    ctx.fillText(waveMsg,0,0);
    ctx.restore();
  }
  if(tauntT>0&&boss){
    const a=Math.min(1,tauntT);
    ctx.save();ctx.globalAlpha=a;
    ctx.textAlign='center';ctx.font='italic 20px monospace';
    ctx.shadowColor='#fff';ctx.shadowBlur=8;ctx.fillStyle='#fff';
    ctx.fillText(taunt,W/2,H*0.32+40);
    ctx.restore();
  }
}
function easeOutCubic(t){return 1-Math.pow(1-t,3);}
function easeOutBack(t){const s=1.8;return 1+((t-1)*(t-1)*((s+1)*(t-1)+s));}
function drawTitle(){
  const t=titleT;
  const fadeIn=Math.min(1,t/0.6);
  const sunT=Math.min(1,Math.max(0,(t-0.5)/2));
  const sunEase=easeOutCubic(sunT);
  const sunY=horizonY+sunR*1.1-sunEase*(sunR*1.3);
  const sunA=Math.min(1,sunT*2);
  const gridA=Math.min(1,Math.max(0,(t-0.8)/1.2));
  const titleT2=Math.min(1,Math.max(0,(t-2)/1.5));
  const titleScale=easeOutBack(Math.min(1,titleT2));
  const titleA=Math.min(1,titleT2*2);
  const tagA=Math.min(1,Math.max(0,(t-3)/0.8));
  const ctaA=Math.max(0,Math.min(1,(t-3.8)/0.6));
  if(t<0.6){ctx.fillStyle='rgba(2,0,8,'+(1-fadeIn).toFixed(2)+')';ctx.fillRect(0,0,W,H);}
  drawSun(sunY,sunA);
  drawMtn(mtnBack,pal.mtnBack,pal.mtnBackFill,0,gridA);
  drawMtn(mtnFront,pal.mtnFront,pal.mtnFrontFill,0,gridA);
  drawGrid(gridA);
  const cx=W/2,cy=horizonY-sunR*0.5;
  if(titleT2>0){
    ctx.save();ctx.globalAlpha=titleA;
    const fs=Math.min(W*0.105,72);
    ctx.font='bold '+fs+'px monospace';ctx.textAlign='center';
    const pulse=0.8+0.2*Math.sin(time*3);
    ctx.translate(cx,cy);ctx.scale(titleScale,titleScale);
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=35*pulse;ctx.fillStyle='#fff';
    ctx.fillText('NEON SPARK',0,0);
    ctx.shadowColor='#00e5ff';ctx.shadowBlur=18;
    ctx.strokeStyle='rgba(0,229,255,0.85)';ctx.lineWidth=1.5;ctx.strokeText('NEON SPARK',0,0);
    ctx.restore();
    if(titleT2<1){
      ctx.save();ctx.globalAlpha=(1-titleT2)*0.8;
      const swX=cx-(1-titleT2)*(W*0.4);
      ctx.strokeStyle='#fff';ctx.lineWidth=3;ctx.shadowColor='#00e5ff';ctx.shadowBlur=20;
      ctx.beginPath();ctx.moveTo(swX,cy-50);ctx.lineTo(swX,cy+30);ctx.stroke();
      ctx.restore();
    }
  }
  if(tagA>0){
    ctx.save();ctx.globalAlpha=tagA;ctx.textAlign='center';
    ctx.font='16px monospace';ctx.shadowColor='#76B900';ctx.shadowBlur=10;ctx.fillStyle='#76B900';
    ctx.fillText('S Y N T H W A V E   A R C A D E',cx,cy+38);
    ctx.restore();
  }
  if(ctaA>0){
    const pa=0.35+0.65*Math.abs(Math.sin(time*2.2));
    ctx.save();ctx.globalAlpha=ctaA*pa;ctx.textAlign='center';
    ctx.font='bold 22px monospace';ctx.shadowColor='#ffe14d';ctx.shadowBlur=18;ctx.fillStyle='#ffe14d';
    ctx.fillText('CLICK OR TAP TO START',cx,H*0.72);
    ctx.globalAlpha=ctaA*0.6;ctx.font='12px monospace';ctx.shadowBlur=4;ctx.shadowColor='#00e5ff';ctx.fillStyle='#9fe8ff';
    ctx.fillText('MOUSE / TOUCH / WASD   ·   P PAUSE   ·   M MUTE',cx,H*0.72+28);
    if(best>0){ctx.globalAlpha=ctaA*0.85;ctx.font='bold 14px monospace';ctx.fillStyle='#00e5ff';ctx.shadowColor='#00e5ff';ctx.fillText('BEST SCORE: '+best,cx,H*0.78);}
    ctx.restore();
  }
  if(t>0.4&&t<0.8){
    const fa=1-Math.abs(t-0.6)/0.2;
    if(fa>0){
      ctx.save();ctx.globalCompositeOperation='lighter';ctx.globalAlpha=fa*0.3;
      const fg=ctx.createRadialGradient(cx,horizonY,0,cx,horizonY,Math.max(W,H)*0.6);
      fg.addColorStop(0,'rgba(255,200,100,1)');fg.addColorStop(1,'rgba(255,50,200,0)');
      ctx.fillStyle=fg;ctx.fillRect(0,0,W,H);
      ctx.restore();
    }
  }
}
function drawIntro(){
  const t=introT;
  const fadeIn=Math.min(1,t/0.5);
  ctx.save();
  ctx.globalAlpha=fadeIn;
  ctx.fillStyle='rgba(2,0,10,0.6)';ctx.fillRect(0,0,W,H);
  // glitch bars
  const glitch=Math.random()<0.15;
  if(glitch){
    ctx.globalCompositeOperation='lighter';
    ctx.fillStyle='rgba(0,229,255,0.15)';
    ctx.fillRect(0,Math.random()*H,W,4);
    ctx.fillStyle='rgba(255,45,149,0.15)';
    ctx.fillRect(0,Math.random()*H,W,4);
  }
  ctx.globalAlpha=fadeIn;
  // header
  ctx.textAlign='center';
  const headerA=Math.min(1,t*3);
  ctx.globalAlpha=fadeIn*headerA;
  ctx.font='bold 18px monospace';
  const flicker=glitch?0.5:1;
  ctx.shadowColor='#00e5ff';ctx.shadowBlur=20;
  ctx.fillStyle='#00e5ff';
  const hx=Math.random()<0.15?(Math.random()-0.5)*4:0;
  ctx.fillText('▸▸ INCOMING TRANSMISSION ◄◄',W/2+hx,H*0.28);
  // decorative lines
  ctx.strokeStyle='rgba(0,229,255,0.5)';ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(W*0.2,H*0.31);ctx.lineTo(W*0.8,H*0.31);ctx.stroke();
  // typewriter text
  const lineH=42;
  ctx.font=Math.min(W*0.035,24)+'px monospace';
  let maxW=0;
  for(const l of introLines)maxW=Math.max(maxW,ctx.measureText(l).width);
  maxW=Math.min(maxW,W*0.9);
  const x0=W/2-maxW/2, y0=H*0.42-(introLines.length-1)*lineH/2;
  let remaining=Math.floor(t*28);
  ctx.textAlign='left';
  for(let i=0;i<introLines.length;i++){
    const line=introLines[i];
    let take=line.length;
    if(remaining>=take){
      ctx.shadowColor='#00e5ff';ctx.shadowBlur=8;ctx.fillStyle='#cfe8ff';
      ctx.fillText(line,x0,y0+i*lineH);
      remaining-=take;
    }else{
      ctx.shadowColor='#00e5ff';ctx.shadowBlur=8;ctx.fillStyle='#cfe8ff';
      ctx.fillText(line.slice(0,remaining),x0,y0+i*lineH);
      if(Math.floor(time*3)%2===0){const w=ctx.measureText(line.slice(0,remaining)).width;ctx.fillRect(x0+w+4,y0+i*lineH-16,12,20);}
      remaining=0;
    }
  }
  // begin prompt
  const done=Math.min(1,Math.max(0,(t-totalIntroChars/28)/0.5));
  if(done>0){
    ctx.globalAlpha=done*(0.4+0.6*Math.abs(Math.sin(time*3)));
    ctx.textAlign='center';
    ctx.font='bold 22px monospace';
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=18;ctx.fillStyle='#ff2d95';
    ctx.fillText('CLICK TO BEGIN ▸',W/2,H*0.74);
  }
  ctx.restore();
}
function drawSectorCard(){
  const t=sectorCardT;
  const a=Math.min(1,t*3)*(t>sectorCardDur-0.5?(sectorCardDur-t)*2:1);
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.5)';ctx.fillRect(0,0,W,H);
  ctx.globalAlpha=Math.max(0,a);
  ctx.textAlign='center';
  const acc=sectors[currentSector].accent;
  ctx.font='14px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';
  ctx.fillText('SECTOR '+(currentSector+1)+' / 3',W/2,H*0.4);
  ctx.font='bold '+Math.min(W*0.09,54)+'px monospace';
  ctx.shadowColor=acc;ctx.shadowBlur=30;ctx.fillStyle=acc;
  ctx.fillText(sectors[currentSector].name,W/2,H*0.47);
  ctx.font='18px monospace';ctx.shadowBlur=8;ctx.fillStyle='#cfe8ff';
  ctx.fillText(sectors[currentSector].sub,W/2,H*0.54);
  ctx.restore();ctx.globalAlpha=1;
}
function drawUpgradeIcon(kind,cx,cy,color){
  ctx.save();
  ctx.translate(cx,cy);
  ctx.strokeStyle=color;ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=18;ctx.lineWidth=2.5;
  if(kind==='rapid'){
    for(const o of[-8,0,8]){
      ctx.beginPath();ctx.moveTo(o-5,14);ctx.lineTo(o+5,2);ctx.lineTo(o+1,2);ctx.lineTo(o+8,-14);ctx.lineTo(o-4,-2);ctx.lineTo(o-1,-2);ctx.closePath();
      ctx.fill();
    }
  }else if(kind==='twin'){
    for(const o of[-7,7]){
      ctx.beginPath();ctx.moveTo(o,-16);ctx.lineTo(o+5,6);ctx.lineTo(o,3);ctx.lineTo(o-5,6);ctx.closePath();
      ctx.fill();
    }
  }else if(kind==='hull'){
    shipPath(1.0);
    ctx.fillStyle='rgba(0,16,38,0.94)';ctx.fill();
    ctx.shadowColor=color;ctx.shadowBlur=18;
    ctx.stroke();
  }else if(kind==='shield'){
    ctx.beginPath();ctx.arc(0,0,14,0,7);ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,8,0,7);ctx.stroke();
    ctx.beginPath();ctx.arc(0,-2,3,0,7);ctx.fill();
  }else if(kind==='magnet'){
    ctx.beginPath();ctx.arc(0,-2,10,Math.PI,Math.PI*2);ctx.stroke();
    ctx.beginPath();ctx.moveTo(-10,-2);ctx.lineTo(-10,12);ctx.lineTo(-3,12);ctx.lineTo(-3,-2);
    ctx.moveTo(10,-2);ctx.lineTo(10,12);ctx.lineTo(3,12);ctx.lineTo(3,-2);
    ctx.stroke();
    ctx.beginPath();
    for(const o of[-10,10]){ctx.moveTo(o,14);ctx.lineTo(o-4,19);ctx.lineTo(o+4,19);}
    ctx.stroke();
  }else if(kind==='od'){
    ctx.beginPath();ctx.arc(0,0,14,0,7);ctx.stroke();
    for(let k=0;k<12;k++){const a=k/12*6.283;const rr=k%2?8:14;
      ctx.beginPath();ctx.moveTo(Math.cos(a)*rr,Math.sin(a)*rr);ctx.lineTo(Math.cos(a)*8,Math.sin(a)*8);ctx.stroke();}
    ctx.beginPath();ctx.arc(0,0,5,0,7);ctx.fill();
  }
  ctx.restore();
}
function drawUpgrade(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.68)';ctx.fillRect(0,0,W,H);
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.06,34)+'px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=24;ctx.fillStyle='#76B900';
  ctx.fillText('CHOOSE AN UPGRADE',W/2,H*0.26);
  const rects=upgradeCardRects();
  for(const r of rects){
    const c=upgradeCards[r.i];
    const delay=r.i*0.15;
    const animT=Math.min(1,Math.max(0,(sectorT-delay)/0.4));
    const ease=easeOutBack(animT);
    const isHover=hoverCard===r.i;
    const lift=isHover?14:0;
    const yy=r.y+ (1-ease)*80 - lift;
    ctx.save();
    ctx.globalAlpha=Math.min(1,animT*1.5);
    ctx.fillStyle=isHover?'rgba(0,40,30,0.95)':'rgba(0,20,30,0.85)';
    ctx.fillRect(r.x,yy,r.w,r.h);
    const glow=isHover?28:14;
    ctx.strokeStyle=c.color;ctx.lineWidth=isHover?3:2;ctx.shadowColor=c.color;ctx.shadowBlur=glow;
    ctx.strokeRect(r.x,yy,r.w,r.h);
    ctx.shadowBlur=0;
    // icon
    drawUpgradeIcon(c.kind,r.x+r.w/2,yy+62,c.color);
    // label
    ctx.font='bold '+Math.min(17,r.w*0.075)+'px monospace';
    ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=8;
    ctx.fillText(c.label,r.x+r.w/2,yy+r.h*0.62);
    // level
    const lv=upgLevel(c.kind),max=upgMax(c.kind);
    ctx.font='bold 12px monospace';
    ctx.fillStyle='rgba(255,255,255,0.75)';ctx.shadowBlur=0;
    ctx.fillText('LV '+(lv+1)+' / '+(max+1),r.x+r.w/2,yy+r.h*0.72);
    // pips
    const pw=24,gap=6,tot=pw*(max+1)+gap*max;let px=r.x+r.w/2-tot/2;
    for(let k=0;k<=max;k++){
      ctx.fillStyle=k<=lv?c.color:'rgba(255,255,255,0.18)';
      if(k<=lv){ctx.shadowColor=c.color;ctx.shadowBlur=6;}else ctx.shadowBlur=0;
      ctx.fillRect(px,yy+r.h*0.78,pw,5);
      px+=pw+gap;
    }
    ctx.shadowBlur=0;
    // description
    ctx.font='11px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';
    wrapText(c.desc,r.x+r.w/2,yy+r.h*0.88,r.w-24,14);
    ctx.restore();
  }
  ctx.font='12px monospace';ctx.fillStyle='rgba(255,255,255,0.5)';ctx.textAlign='center';
  ctx.fillText('CLICK A CARD  ·  OR PRESS 1 / 2 / 3',W/2,H*0.86);
  ctx.restore();
}
function wrapText(txt,x,y,maxW,lh){
  const words=txt.split(' ');let line='';
  for(let i=0;i<words.length;i++){
    const test=line+words[i]+' ';
    if(ctx.measureText(test).width>maxW&&i>0){ctx.fillText(line,x,y);line=words[i]+' ';y+=lh;}
    else line=test;
  }
  ctx.fillText(line,x,y);
}
function drawSectorClear(){
  const t=sectorClearT;
  const a=Math.min(1,t*3);
  const total=3.5;
  const outA=t>total-0.4?(total-t)*2.5:1;
  const alpha=Math.max(0,Math.min(a,outA));
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,'+(0.75*alpha).toFixed(2)+')';ctx.fillRect(0,0,W,H);
  ctx.globalAlpha=alpha;
  const acc=sectors[currentSector].accent;
  // glitch header
  ctx.textAlign='center';
  const glitch=Math.random()<0.2;
  const gx=glitch?(Math.random()-0.5)*6:0;
  ctx.font='bold '+Math.min(W*0.08,52)+'px monospace';
  ctx.shadowColor=acc;ctx.shadowBlur=32;ctx.fillStyle=acc;
  ctx.fillText('SECTOR CLEAR',W/2+gx,H*0.30);
  if(glitch){
    ctx.globalCompositeOperation='lighter';
    ctx.fillStyle='rgba(0,229,255,'+(alpha*0.3)+')';
    ctx.fillRect(W/2-140,H*0.30-20,280,4);
  }
  ctx.globalAlpha=alpha;
  ctx.font='16px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';ctx.shadowBlur=0;
  ctx.fillText(sectors[currentSector].name,W/2,H*0.30+34);
  // tally
  const acc2=secFired?Math.round(100*secHit/secFired):100;
  const noHit=secNoHit;
  const stats=[
    ['ENEMIES DESTROYED',secKill.toString(),'#00e5ff'],
    ['ACCURACY',acc2+'%','#ff8a00'],
    [noHit?'NO-HIT BONUS':'TOOK A HIT',(noHit?'+2500':'+0'),noHit?'#76B900':'rgba(255,255,255,0.5)']
  ];
  ctx.font='15px monospace';
  let sy=H*0.44;
  const count=Math.min(1,Math.max(0,(t-0.4)/1.2));
  for(const s of stats){
    ctx.textAlign='right';ctx.fillStyle='rgba(255,255,255,0.6)';
    ctx.fillText(s[0],W/2-20,sy);
    ctx.textAlign='left';
    if(s[1].startsWith('+')){
      const val=Math.round((+s[1].slice(1))*easeOutCubic(count));
      ctx.fillText('+'+val,W/2+20,sy);
    }else{
      ctx.fillText(s[1],W/2+20,sy);
    }
    ctx.fillStyle=s[2];
    ctx.fillText(s[1].startsWith('+')?'+'+Math.round((+s[1].slice(1))*easeOutCubic(count)):s[1],W/2+20,sy);
    sy+=28;
  }
  // bonus points counting up
  const bonus=1000+(noHit?2500:0)+secKill*20;
  const shown=Math.round(bonus*easeOutCubic(count));
  ctx.textAlign='center';
  ctx.font='bold 24px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=16;ctx.fillStyle='#76B900';
  ctx.fillText('BONUS +'+shown.toLocaleString(),W/2,H*0.68);
  if(t>1.6){
    const pa=0.4+0.6*Math.abs(Math.sin(time*3));
    ctx.globalAlpha=alpha*pa;
    ctx.font='bold 16px monospace';ctx.fillStyle='#00e5ff';ctx.shadowColor='#00e5ff';ctx.shadowBlur=10;
    ctx.fillText('GETTING READY FOR UPGRADE…',W/2,H*0.76);
  }
  ctx.restore();
}
function drawGameOver(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.74)';ctx.fillRect(0,0,W,H);
  const a=Math.min(1,goT*2.5);
  ctx.globalAlpha=a;
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.09,62)+'px monospace';
  ctx.shadowColor='#ff2d95';ctx.shadowBlur=32;ctx.fillStyle='#ff2d95';
  ctx.fillText('GAME OVER',W/2,H*0.34);
  ctx.font='bold 28px monospace';ctx.shadowColor='#00e5ff';ctx.shadowBlur=16;ctx.fillStyle='#00e5ff';
  ctx.fillText('FINAL SCORE  '+score,W/2,H*0.46);
  ctx.font='bold 18px monospace';
  const isBest=score>=best&&score>0;
  ctx.shadowColor=isBest?'#76B900':'rgba(255,255,255,0.3)';
  ctx.fillStyle=isBest?'#76B900':'rgba(255,255,255,0.65)';
  ctx.fillText(isBest?'★ NEW BEST ★':'BEST  '+best,W/2,H*0.53);
  if(goT>0.8){
    const pa=0.35+0.65*Math.abs(Math.sin(time*2.2));
    ctx.globalAlpha=pa*a;ctx.font='bold 22px monospace';ctx.shadowColor='#ffe14d';ctx.shadowBlur=18;ctx.fillStyle='#ffe14d';
    ctx.fillText('CLICK OR TAP TO RESTART',W/2,H*0.66);
  }
  ctx.restore();
}
function victoryBtnRects(){
  const w=Math.min(W*0.5,300),h=52,x=(W-w)/2;
  return [
    {x,y:H*0.72-h/2,w,h,label:'PLAY AGAIN',act:()=>startRun(hardMode)},
    {x,y:H*0.80-h/2,w,h,label:hardMode?'EASY MODE':'HARD MODE',act:()=>startRun(!hardMode)}
  ];
}
function fmtTime(s){const m=Math.floor(s/60);const ss=Math.floor(s%60);return m+':'+String(ss).padStart(2,'0');}
function drawVictory(){
  const a=Math.min(1,vicT*2);
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,'+(0.78*a).toFixed(2)+')';ctx.fillRect(0,0,W,H);
  ctx.globalAlpha=a;
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.09,60)+'px monospace';
  const cols=['#ff2d95','#00e5ff','#76B900'];
  ctx.shadowColor=cols[Math.floor(time*4)%3];ctx.shadowBlur=34;
  ctx.fillStyle='#fff';
  ctx.fillText('THE GRID IS LIT',W/2,H*0.24);
  ctx.font='16px monospace';ctx.shadowColor='#76B900';ctx.shadowBlur=10;ctx.fillStyle='#76B900';
  ctx.fillText('SPARK held the light. The Static is gone.',W/2,H*0.31);
  ctx.fillStyle='rgba(255,255,255,0.75)';ctx.shadowBlur=0;
  ctx.fillText('The Neon Grid hums back to life, one district at a time.',W/2,H*0.35);
  const acc=shotsFired?Math.round(100*shotsHit/shotsFired):0;
  const stats=[
    ['FINAL SCORE',score.toLocaleString()],
    ['BEST',best.toLocaleString()],
    ['MAX COMBO',maxCombo+' hits'],
    ['ACCURACY',acc+'%'],
    ['TIME',fmtTime(runTime)]
  ];
  ctx.font='15px monospace';
  let sy=H*0.44;
  for(const s of stats){
    ctx.textAlign='right';ctx.fillStyle='rgba(255,255,255,0.6)';ctx.fillText(s[0],W/2-14,sy);
    ctx.textAlign='left';ctx.fillStyle='#00e5ff';ctx.shadowColor='#00e5ff';ctx.shadowBlur=8;ctx.fillText(s[1],W/2+14,sy);
    ctx.shadowBlur=0;sy+=26;
  }
  ctx.textAlign='center';
  const btns=victoryBtnRects();
  for(const b of btns){
    ctx.fillStyle='rgba(0,20,30,0.8)';ctx.fillRect(b.x,b.y,b.w,b.h);
    ctx.strokeStyle='#76B900';ctx.lineWidth=2;ctx.shadowColor='#76B900';ctx.shadowBlur=14;ctx.strokeRect(b.x,b.y,b.w,b.h);
    ctx.shadowBlur=0;ctx.font='bold 18px monospace';ctx.fillStyle='#76B900';
    ctx.fillText(b.label,b.x+b.w/2,b.y+b.h/2+6);
  }
  ctx.restore();
}
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
  ctx.shadowColor='#00e5ff';ctx.shadowBlur=26;ctx.fillStyle='#00e5ff';
  ctx.fillText('PAUSED',W/2,H*0.45);
  ctx.font='14px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';ctx.shadowBlur=0;
  ctx.fillText('PRESS P TO RESUME',W/2,H*0.52);
  ctx.restore();
}

/* ================= RENDER ================= */
function render(){
  ctx.save();
  if(shake>0)ctx.translate((Math.random()-0.5)*shake,(Math.random()-0.5)*shake);
  if(state==='title')drawTitle();
  else{
    drawBackground();
    if(state==='playing'||state==='gameover')drawEntities();
    drawFx();
    if(state==='playing'||state==='gameover')drawPopups();
  }
  ctx.restore();
  if(state==='playing'){drawWaveMsg();drawHUD();drawOverdriveBtn();if(paused)drawPause();}
  else if(state==='intro')drawIntro();
  else if(state==='sector')drawSectorCard();
  else if(state==='upgrade')drawUpgrade();
  else if(state==='sectorclear')drawSectorClear();
  else if(state==='gameover')drawGameOver();
  else if(state==='victory')drawVictory();
  drawOverlays();
}

/* ================= MAIN LOOP ================= */
let sectorT=0;
function frame(ts){
  requestAnimationFrame(frame);
  const rdt=Math.min(0.05,(ts-last)/1000||0);
  last=ts;
  time+=rdt;
  gridScroll=(gridScroll+rdt*0.5)%1;
  scheduleMusic();
  updateMusic();
  let dt=rdt;
  if(state==='playing'){
    if(paused){dt=0;}
    else{
      slowT=Math.max(0,slowT-rdt);
      const target=slowT>0?0.32:1;
      timeScale+=(target-timeScale)*Math.min(1,rdt*7);
      if(hitStop>0){hitStop-=rdt;dt=0;}
      else dt=rdt*timeScale;
      runTime+=dt;
      updatePlayer(dt);
      updateWaves(dt);
      updateEnemies(dt);
      updateBullets(dt);
      updatePowerups(dt);
      updateFx(dt);
    }
  }else if(state==='intro'){
    introT+=rdt;
    if(introT>totalIntroChars/28+1.4)enterSector(0);
  }else if(state==='sector'){
    sectorCardT+=rdt;
    if(sectorCardT>=sectorCardDur)beginPlayingSector();
  }else if(state==='upgrade'){
    sectorT+=rdt;
  }else if(state==='sectorclear'){
    sectorClearT+=rdt;
    updateFx(rdt*0.6);
    if(sectorClearT>3.5){
      score+=1000+(secNoHit?2500:0)+secKill*20;
      buildUpgradeCards();
      state='upgrade';sectorT=0;
    }
  }else if(state==='title'){
    titleT+=rdt;
  }else{
    updateFx(rdt*0.6);
    if(state==='gameover')goT+=rdt;
    if(state==='victory')vicT+=rdt;
  }
  render();
}

/* ================= INPUT ================= */
const keys={};
let hoverCard=-1;
function onPointer(x,y){
  initAudio();
  if(state==='title'&&titleT>1){startRun(false);return;}
  if(state==='intro'){enterSector(0);return;}
  if(state==='sector'){sectorCardT=sectorCardDur;return;}
  if(state==='upgrade'){
    const rects=upgradeCardRects();
    for(const r of rects){if(x>=r.x&&x<=r.x+r.w&&y>=r.y&&y<=r.y+r.h)chooseCard(r.i);}
    return;
  }
  if(state==='gameover'&&goT>0.6){startRun(false);return;}
  if(state==='victory'){
    const btns=victoryBtnRects();
    for(const b of btns){if(x>=b.x&&x<=b.x+b.w&&y>=b.y&&y<=b.y+b.h){b.act();return;}}
  }
}
window.addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  keys[k]=true;
  if(k===' '||k==='enter'){
    e.preventDefault();
    if(state==='title'&&titleT>1)startRun(false);
    else if(state==='intro')enterSector(0);
    else if(state==='sector')sectorCardT=sectorCardDur;
    else if(state==='playing')unleashOverdrive();
    else if(state==='gameover'&&goT>0.6)startRun(false);
    else if(state==='victory')startRun(hardMode);
  }
  if(k==='p'&&state==='playing')paused=!paused;
  if(k==='m')toggleMute();
  if(state==='upgrade'){if(k==='1')chooseCard(0);if(k==='2')chooseCard(1);if(k==='3')chooseCard(2);}
  if(state==='victory'){if(k==='1'||k==='r')startRun(hardMode);if(k==='2'||k==='h')startRun(!hardMode);}
});
window.addEventListener('keyup',e=>{keys[e.key.toLowerCase()]=false;});
window.addEventListener('mousemove',e=>{
  if(state==='playing')player.tx=e.clientX;
  if(state==='upgrade'){
    const rects=upgradeCardRects();
    hoverCard=-1;
    for(const r of rects){if(e.clientX>=r.x&&e.clientX<=r.x+r.w&&e.clientY>=r.y&&e.clientY<=r.y+r.h)hoverCard=r.i;}
  }
});
window.addEventListener('mousedown',e=>{onPointer(e.clientX,e.clientY);});
window.addEventListener('touchstart',e=>{
  e.preventDefault();
  const t=e.touches[0];
  if(state==='playing'){
    player.tx=t.clientX;
    // check overdrive button
    if(isTouch&&player.overdrive>=1){
      const bx=W-70,by=H-90,r=38;
      const dx=t.clientX-bx,dy=t.clientY-by;
      if(dx*dx+dy*dy<r*r){unleashOverdrive();return;}
    }
  }
  // double-tap detection
  const now=performance.now();
  if(now-lastTap<300&&state==='playing'&&isTouch&&player.overdrive>=1){
    unleashOverdrive();
    lastTap=0;
    return;
  }
  lastTap=now;
  onPointer(t.clientX,t.clientY);
},{passive:false});
window.addEventListener('touchmove',e=>{
  e.preventDefault();
  const t=e.touches[0];
  if(state==='playing')player.tx=t.clientX;
},{passive:false});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&state==='playing')paused=true;});

resize();
player.x=player.tx=W/2;
player.y=H*0.86;
player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1};
requestAnimationFrame(frame);
</script>
</body>
</html>
```