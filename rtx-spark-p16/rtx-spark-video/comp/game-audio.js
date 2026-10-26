// NEON SPARK's audio, lifted unchanged from the final game (coding/neon-spark-final/index.html) by
// bench/render_arcade_audio.py; only its effects start at SFX_T instead of AC.currentTime, and its snare
// and arp call HOOK (the film's room and echo, arcade-audio.html; the game itself has neither).
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
  if(!AC)return;const t=SFX_T;
  const o=AC.createOscillator();o.type='square';
  o.frequency.setValueAtTime(920,t);o.frequency.exponentialRampToValueAtTime(220,t+0.07);
  const g=AC.createGain();g.gain.setValueAtTime(0.07,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.08);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.09);
}
function sfxBoom(big){
  if(!AC)return;const t=SFX_T;
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
  if(!AC)return;const t=SFX_T;
  [523.25,659.25,783.99,1046.5].forEach((f,i)=>{
    const o=AC.createOscillator();o.type='triangle';o.frequency.value=f;
    const g=AC.createGain();const t0=t+i*0.06;
    g.gain.setValueAtTime(0.13,t0);g.gain.exponentialRampToValueAtTime(0.001,t0+0.15);
    o.connect(g);g.connect(sfxG);o.start(t0);o.stop(t0+0.16);
  });
}
function sfxShield(){
  if(!AC)return;const t=SFX_T;
  const o=AC.createOscillator();o.type='sine';
  o.frequency.setValueAtTime(280,t);o.frequency.exponentialRampToValueAtTime(880,t+0.18);
  const g=AC.createGain();g.gain.setValueAtTime(0.18,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.22);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.23);
}
function sfxOver(){
  if(!AC)return;const t=SFX_T;
  const o=AC.createOscillator();o.type='sawtooth';
  o.frequency.setValueAtTime(120,t);o.frequency.exponentialRampToValueAtTime(1600,t+0.5);
  const g=AC.createGain();g.gain.setValueAtTime(0.3,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.6);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.6);
}
function sfxBlip(){
  if(!AC)return;const t=SFX_T;
  const o=AC.createOscillator();o.type='square';o.frequency.value=1800;
  const g=AC.createGain();g.gain.setValueAtTime(0.02,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.03);
  o.connect(g);g.connect(sfxG);o.start(t);o.stop(t+0.04);
}
function sfxClear(){
  if(!AC)return;const t=SFX_T;
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
    s.connect(nf);nf.connect(ng);ng.connect(musicG);if(window.HOOK)HOOK('snare',ng);s.start(t);s.stop(t+0.12);
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
  ao.connect(af);af.connect(ag);ag.connect(musicG);if(window.HOOK)HOOK('arp',ag);ao.start(t);ao.stop(t+0.14);
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

