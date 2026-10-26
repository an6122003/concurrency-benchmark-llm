```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>GALAXY FORGE</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:100%; height:100%; overflow:hidden; background:#02030a; font-family:'Segoe UI',system-ui,sans-serif; }
  #c { position:fixed; inset:0; display:block; touch-action:none; cursor:grab; }
  #c:active { cursor:grabbing; }

  #title {
    position:fixed; top:18px; left:22px; color:#fff; z-index:10;
    pointer-events:none; user-select:none;
  }
  #title h1 {
    font-size:20px; letter-spacing:7px; font-weight:300;
    text-shadow:0 0 18px rgba(120,160,255,.8), 0 0 40px rgba(255,150,90,.35);
  }
  #title h1 b { font-weight:700; letter-spacing:7px; }
  #stats { margin-top:6px; font-size:11px; letter-spacing:2px; color:rgba(200,215,255,.75); }
  #stats span { color:#fff; }

  #panel {
    position:fixed; top:18px; right:18px; width:240px; z-index:20;
    background:rgba(12,18,38,.42);
    backdrop-filter:blur(14px) saturate(150%);
    -webkit-backdrop-filter:blur(14px) saturate(150%);
    border:1px solid rgba(160,190,255,.18);
    border-radius:16px; color:#dfe7ff;
    box-shadow:0 8px 40px rgba(0,0,10,.5), inset 0 1px 0 rgba(255,255,255,.08);
    overflow:hidden; transition:transform .35s cubic-bezier(.2,.9,.3,1), opacity .3s;
  }
  #panel.collapsed .body { display:none; }
  #phead {
    display:flex; justify-content:space-between; align-items:center;
    padding:11px 15px; cursor:pointer; user-select:none;
    font-size:11px; letter-spacing:3px; color:rgba(210,225,255,.9);
  }
  #phead:hover { color:#fff; }
  #chev { transition:transform .3s; font-size:13px; }
  #panel.collapsed #chev { transform:rotate(-90deg); }
  .body { padding:2px 15px 14px; }
  .row { margin-bottom:10px; }
  .row label { display:flex; justify-content:space-between; font-size:10px; letter-spacing:1px; color:rgba(190,205,245,.75); margin-bottom:4px; }
  .row label b { color:#fff; font-weight:600; }
  input[type=range] {
    width:100%; -webkit-appearance:none; appearance:none; height:4px; border-radius:2px;
    background:rgba(140,170,255,.25); outline:none;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance:none; width:13px; height:13px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #fff, #7fa8ff);
    box-shadow:0 0 8px rgba(140,180,255,.9); cursor:pointer;
  }
  .presets { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
  .pbtn {
    padding:6px 4px; font-size:10px; letter-spacing:1px; color:#dfe7ff;
    background:rgba(120,150,255,.12); border:1px solid rgba(160,190,255,.22);
    border-radius:8px; cursor:pointer; transition:all .2s;
  }
  .pbtn:hover { background:rgba(140,170,255,.28); }
  .pbtn.on { background:rgba(150,180,255,.4); border-color:rgba(200,220,255,.7); color:#fff; box-shadow:0 0 12px rgba(140,170,255,.35); }
  .togs { display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; }
  .tog {
    padding:6px 2px; font-size:9px; letter-spacing:1px; text-align:center; cursor:pointer;
    background:rgba(120,150,255,.1); border:1px solid rgba(160,190,255,.18);
    border-radius:8px; color:rgba(190,205,245,.6); transition:all .2s; user-select:none;
  }
  .tog.on { background:rgba(150,180,255,.35); color:#fff; border-color:rgba(200,220,255,.6); }
  #bang {
    width:100%; padding:9px 0; margin-top:4px; border-radius:10px; border:1px solid rgba(255,170,90,.5);
    background:linear-gradient(135deg, rgba(255,110,60,.35), rgba(255,200,90,.25));
    color:#ffe9c8; font-size:12px; letter-spacing:4px; font-weight:600; cursor:pointer;
    text-shadow:0 0 10px rgba(255,160,60,.9); transition:all .2s;
  }
  #bang:hover { background:linear-gradient(135deg, rgba(255,130,70,.6), rgba(255,210,110,.45)); box-shadow:0 0 22px rgba(255,150,60,.5); transform:scale(1.02); }

  #hint {
    position:fixed; bottom:16px; left:50%; transform:translateX(-50%);
    color:rgba(180,200,255,.55); font-size:11px; letter-spacing:2px;
    pointer-events:none; user-select:none; z-index:10; white-space:nowrap;
  }
  .hidden { opacity:0 !important; pointer-events:none !important; }
  #panel.hidden { transform:translateX(280px); }
</style>
</head>
<body>
<canvas id="c"></canvas>

<div id="title">
  <h1><b>GALAXY</b> FORGE</h1>
  <div id="stats">FPS <span id="fps">--</span> &nbsp;·&nbsp; ★ <span id="cnt">0</span></div>
</div>

<div id="panel">
  <div id="phead"><span>CONTROLS</span><span id="chev">▾</span></div>
  <div class="body">
    <div class="row"><label>STARS <b id="vStars">60,000</b></label>
      <input id="sStars" type="range" min="10000" max="120000" step="5000" value="60000"></div>
    <div class="row"><label>SPIRAL ARMS <b id="vArms">3</b></label>
      <input id="sArms" type="range" min="2" max="5" step="1" value="3"></div>
    <div class="row"><label>ROTATION SPEED <b id="vSpeed">1.0</b></label>
      <input id="sSpeed" type="range" min="0" max="3" step="0.1" value="1"></div>
    <div class="row"><label>ARM SPREAD <b id="vSpread">1.0</b></label>
      <input id="sSpread" type="range" min="0.2" max="2" step="0.1" value="1"></div>
    <div class="row"><label>COLOR PRESET</label>
      <div class="presets" id="presets">
        <div class="pbtn on" data-p="milky">MILKY WAY</div>
        <div class="pbtn" data-p="andromeda">ANDROMEDA</div>
        <div class="pbtn" data-p="nebula">NEBULA</div>
        <div class="pbtn" data-p="neon">NEON</div>
      </div>
    </div>
    <div class="row togs">
      <div class="tog on" id="tGlow">GLOW</div>
      <div class="tog on" id="tNeb">NEBULAE</div>
      <div class="tog on" id="tAuto">AUTO CAM</div>
    </div>
    <button id="bang">✦ BIG BANG ✦</button>
  </div>
</div>

<div id="hint">DRAG ORBIT · SCROLL ZOOM · CLICK = DWARF GALAXY · [H]UI [SPACE]PAUSE [R]RESET [S]SNAP</div>

<script>
(function(){
"use strict";
const TAU = Math.PI*2;
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl', {alpha:false, antialias:true, preserveDrawingBuffer:true, powerPreference:'high-performance'});
if(!gl){ document.body.innerHTML='<p style="color:#fff;padding:2em">WebGL not supported</p>'; return; }

// ---------- shaders ----------
const VS = `
attribute vec4 aOrb;   // r, angle0, angSpeed, y
attribute vec3 aCol;
attribute vec3 aMisc;  // size, phase, susceptibility
uniform mat4 uVP;
uniform vec3 uEye;
uniform vec3 uOffset;
uniform float uTime, uSpeed, uExplode, uDwarfAct, uTwinkle, uPointScale;
uniform vec3 uDwarfPos;
varying vec3 vColor;
void main(){
  float r = aOrb.x;
  float ang = aOrb.y + uTime * uSpeed * aOrb.z;
  float e = uExplode * (1.0 + aMisc.z * 1.5);
  r *= 1.0 + e*e*6.0;
  float y = aOrb.w * (1.0 + e*2.5);
  vec3 p = vec3(cos(ang)*r, y, sin(ang)*r) + uOffset;
  if(uDwarfAct > 0.002 && aMisc.z > 0.001){
    vec3 d = uDwarfPos - p;
    float dl = length(d) + 0.0001;
    float pull = uDwarfAct * aMisc.z * 2.4 / (dl*dl*0.12 + 0.09);
    pull = min(pull, 1.6);
    vec3 dn = d / dl;
    p += dn * pull * 0.14;
    vec3 tang = cross(vec3(0.0,1.0,0.0), dn);
    float tl = length(tang);
    if(tl > 0.001) p += (tang/tl) * pull * 0.11;
  }
  vec4 clip = uVP * vec4(p, 1.0);
  gl_Position = clip;
  float dist = max(0.4, length(p - uEye));
  float tw = mix(1.0, 0.72 + 0.5*sin(uTime*3.2 + aMisc.y*19.7), uTwinkle);
  gl_PointSize = clamp(aMisc.x * uPointScale * tw * (1.6 / dist), 1.0, 110.0);
  vColor = aCol * (0.55 + 0.45*tw);
}`;
const FS = `
precision mediump float;
varying vec3 vColor;
uniform float uGlow, uAlpha;
void main(){
  vec2 c = gl_PointCoord - 0.5;
  float d = dot(c,c) * 4.0;
  if(d > 1.0) discard;
  float core = exp(-d * 20.0);
  float halo = exp(-d * mix(9.0, 2.1, uGlow));
  float a = (core*1.25 + halo*0.55) * uAlpha;
  gl_FragColor = vec4(vColor * a, a);
}`;

function makeProgram(vsSrc, fsSrc){
  function sh(type, src){
    const s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(s);
    return s;
  }
  const p = gl.createProgram();
  gl.attachShader(p, sh(gl.VERTEX_SHADER, vsSrc));
  gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fsSrc));
  gl.linkProgram(p);
  if(!gl.getProgramParameter(p, gl.LINK_STATUS)) throw gl.getProgramInfoLog(p);
  return p;
}
const prog = makeProgram(VS, FS);
const A_ORB = gl.getAttribLocation(prog,'aOrb'), A_COL = gl.getAttribLocation(prog,'aCol'), A_MISC = gl.getAttribLocation(prog,'aMisc');
const U = {};
['uVP','uEye','uOffset','uTime','uSpeed','uExplode','uDwarfAct','uTwinkle','uPointScale','uDwarfPos','uGlow','uAlpha']
  .forEach(n => U[n] = gl.getUniformLocation(prog, n));

gl.disable(gl.DEPTH_TEST);
gl.enable(gl.BLEND);
gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
gl.clearColor(0.004, 0.006, 0.02, 1);

// ---------- matrices ----------
function perspective(fov, aspect, n, f){
  const t = 1/Math.tan(fov/2), nf = 1/(n-f);
  return new Float32Array([t/aspect,0,0,0, 0,t,0,0, 0,0,(f+n)*nf,-1, 0,0,2*f*n*nf,0]);
}
function lookAt(e, up){
  const zx=e[0], zy=e[1], zz=e[2];
  let yl=Math.hypot(zx,zz); let x0,x1;
  if(yl<1e-5){ x0=1; x1=0; yl=1; } else { x0=zx/yl; x1=zz/yl; }
  const xx=x1*zz-x0*0, xy=x0*zy-x1*zx, xz=0*zx-0*zy; // cross(up,z) with up=(0,1,0)
  const z=[zx,zy,zz], x=[x0, 0, x1];
  const y=[z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
  return new Float32Array([
    x[0],y[0],z[0],0,
    x[1],y[1],z[1],0,
    x[2],y[2],z[2],0,
    -(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]), -(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]), -(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]), 1
  ]);
}
function mul4(a,b){
  const o=new Float32Array(16);
  for(let c=0;c<4;c++) for(let r=0;r<4;r++){
    o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3];
  }
  return o;
}

// ---------- state ----------
const state = { stars:60000, arms:3, speed:1, spread:1, preset:'milky', glow:true, neb:true, auto:true };
let paused=false, simTime=0, explode=0;
let yaw=0.9, pitch=0.42, dist=3.4, targetDist=3.4;
let yawV=0, pitchV=0, lastInteract=0;
let dwarfAct=0, dwarfAge=0, dwarfTheta=Math.random()*TAU;
const dwarfPos=[0,0,0];

const PRESETS = {
  milky:     { arm:[[0.62,0.76,1.0],[1.0,0.93,0.82]], core:[1.0,0.83,0.55], neb:[[0.35,0.42,1.0],[1.0,0.38,0.66],[0.18,0.75,0.85]] },
  andromeda: { arm:[[0.85,0.8,1.0],[1.0,0.75,0.7]],  core:[1.0,0.72,0.62],  neb:[[0.8,0.3,0.9],[1.0,0.5,0.7],[0.5,0.5,1.0]] },
  nebula:    { arm:[[0.55,0.9,1.0],[0.8,0.5,1.0]],   core:[0.95,0.55,0.75], neb:[[0.2,0.8,1.0],[0.9,0.2,0.8],[0.4,0.4,1.0]] },
  neon:      { arm:[[0.2,1.0,0.9],[1.0,0.3,0.95]],   core:[1.0,0.4,1.0],    neb:[[0.1,1.0,0.7],[1.0,0.1,0.8],[0.2,0.4,1.0]] }
};

// ---------- rng ----------
function gauss(){ return (Math.random()+Math.random()+Math.random()+Math.random()-2)*0.85; }
function lerp3(a,b,t){ return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t]; }

// ---------- particle systems ----------
function System(n){
  this.n=n;
  this.orb=gl.createBuffer(); this.col=gl.createBuffer(); this.misc=gl.createBuffer();
}
function upload(sys, o, c, m){
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.orb); gl.bufferData(gl.ARRAY_BUFFER, o, gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.col); gl.bufferData(gl.ARRAY_BUFFER, c, gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.misc); gl.bufferData(gl.ARRAY_BUFFER, m, gl.STATIC_DRAW);
}
function drawSys(sys, alpha, offset){
  gl.uniform3fv(U.uOffset, offset);
  gl.uniform1f(U.uAlpha, alpha);
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.orb);
  gl.vertexAttribPointer(A_ORB, 4, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.col);
  gl.vertexAttribPointer(A_COL, 3, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, sys.misc);
  gl.vertexAttribPointer(A_MISC, 3, gl.FLOAT, false, 0, 0);
  gl.drawArrays(gl.POINTS, 0, sys.n);
}
let mainSys, nebSys, bgSys, coreSys, dwarfSys;

function buildMain(){
  const n = state.stars, arms = state.arms, spread = state.spread, P = PRESETS[state.preset];
  const o=new Float32Array(n*4), c=new Float32Array(n*3), m=new Float32Array(n*3);
  const nCore=(n*0.045)|0, nBulge=(n*0.20)|0, wind=3.0;
  let i=0;
  // hot bright core
  for(;i<nCore;i++){
    const r=Math.abs(gauss())*0.05, a=Math.random()*TAU, y=gauss()*0.05;
    const b=0.7+Math.random()*0.5;
    o[i*4]=r; o[i*4+1]=a; o[i*4+2]=0.35/(0.25+r); o[i*4+3]=y;
    c[i*3]=Math.min(1,1.0*b); c[i*3+1]=Math.min(1,0.9*b); c[i*3+2]=Math.min(1,0.75*b);
    m[i*3]=1.6+Math.random()*1.2; m[i*3+1]=Math.random(); m[i*3+2]=0.1;
  }
  // puffy bulge
  for(;i<nCore+nBulge;i++){
    const r=Math.abs(gauss())*0.17, a=Math.random()*TAU, y=gauss()*0.12;
    const t=Math.random();
    let col=lerp3(P.core, [1.0,0.62,0.35], t*0.7);
    const b=0.55+Math.random()*0.5;
    o[i*4]=r; o[i*4+1]=a; o[i*4+2]=0.30/(0.25+r); o[i*4+3]=y;
    c[i*3]=col[0]*b; c[i*3+1]=col[1]*b; c[i*3+2]=col[2]*b;
    m[i*3]=0.9+Math.random()*1.3; m[i*3+1]=Math.random(); m[i*3+2]=0.15*Math.random();
  }
  // disk / arms
  for(;i<n;i++){
    const r=Math.pow(Math.random(),0.62);
    const arm=(Math.random()*arms)|0;
    const base=arm*TAU/arms + r*wind;
    const sa=gauss()*spread*(0.11+0.30*r);
    const a=base+sa;
    const y=gauss()*(0.012+0.005*r);
    const tt=Math.min(1,Math.max(0,(r-0.12)/0.55));
    let col=lerp3(P.core, lerp3(P.arm[0],P.arm[1],Math.random()), tt);
    let b=0.5+Math.random()*0.6;
    if(Math.random()<0.08){ col=[0.75,0.85,1.0]; b=0.9+Math.random()*0.4; } // hot O/B stars in arms
    if(Math.abs(sa)<0.045 && r>0.1){ const d2=0.22+0.12*Math.random(); col=[col[0]*1.2*d2+0.05, col[1]*d2, col[2]*d2*0.8]; b=1; } // dust lane
    o[i*4]=r; o[i*4+1]=a; o[i*4+2]=0.24/(0.30+r); o[i*4+3]=y;
    c[i*3]=col[0]*b; c[i*3+1]=col[1]*b; c[i*3+2]=col[2]*b;
    const sz=Math.pow(Math.random(),2.4);
    m[i*3]=0.7+sz*2.4; m[i*3+1]=Math.random(); m[i*3+2]=(r>0.45? 0.2+Math.random()*0.8 : Math.random()*0.25);
  }
  if(!mainSys) mainSys=new System(n);
  else mainSys=n===mainSys.n?mainSys:new System(n);
  upload(mainSys,o,c,m);
  // halo glow core (big soft points)
  const nc=26, co=new Float32Array(nc*4), cc=new Float32Array(nc*3), cm=new Float32Array(nc*3);
  for(let j=0;j<nc;j++){
    co[j*4]=Math.abs(gauss())*0.03; co[j*4+1]=Math.random()*TAU; co[j*4+2]=0; co[j*4+3]=gauss()*0.03;
    const b=0.3+Math.random()*0.5;
    cc[j*3]=P.core[0]*b; cc[j*3+1]=P.core[1]*b; cc[j*3+2]=P.core[2]*b;
    cm[j*3]=60+Math.random()*90; cm[j*3+1]=Math.random(); cm[j*3+2]=0;
  }
  if(!coreSys||coreSys.n!==nc) coreSys=new System(nc);
  upload(coreSys,co,cc,cm);
}
function buildNebulae(){
  const N=2400, arms=state.arms, spread=state.spread, P=PRESETS[state.preset];
  const o=new Float32Array(N*4), c=new Float32Array(N*3), m=new Float32Array(N*3);
  for(let i=0;i<N;i++){
    const r=0.12+Math.random()*0.88;
    const arm=(Math.random()*arms)|0;
    const base=arm*TAU/arms + r*3.0 + gauss()*0.10*spread;
    const y=gauss()*0.06;
    const col=P.neb[(Math.random()*P.neb.length)|0];
    const b=0.5+Math.random()*0.5;
    o[i*4]=r; o[i*4+1]=base; o[i*4+2]=0.24/(0.30+r); o[i*4+3]=y;
    c[i*3]=col[0]*b; c[i*3+1]=col[1]*b; c[i*3+2]=col[2]*b;
    m[i*3]=34+Math.pow(Math.random(),1.6)*80; m[i*3+1]=Math.random(); m[i*3+2]=0;
  }
  if(!nebSys||nebSys.n!==N) nebSys=new System(N);
  upload(nebSys,o,c,m);
}
function buildBackground(){
  const N=3500;
  const o=new Float32Array(N*4), c=new Float32Array(N*3), m=new Float32Array(N*3);
  for(let i=0;i<N;i++){
    const u=Math.random()*TAU, v=Math.acos(2*Math.random()-1), R=26;
    const r=Math.random();
    let col;
    if(r<0.3) col=[0.7,0.8,1.0]; else if(r<0.6) col=[1,1,1]; else if(r<0.85) col=[1,0.9,0.7]; else col=[1,0.7,0.55];
    const b=0.25+Math.random()*0.6;
    o[i*4]=R; o[i*4+1]=u; o[i*4+2]=0; o[i*4+3]=0; // angle stored, radius const, y from v
    o[i*4+3]=Math.cos(v)*R;
    const x=Math.sin(v)*Math.cos(u)*R, z=Math.sin(v)*Math.sin(u)*R;
    o[i*4]=Math.hypot(x,z); o[i*4+1]=Math.atan2(z,x); o[i*4+2]=0;
    c[i*3]=col[0]*b; c[i*3+1]=col[1]*b; c[i*3+2]=col[2]*b;
    m[i*3]=1.0+Math.random()*2.2; m[i*3+1]=Math.random(); m[i*3+2]=0;
  }
  if(!bgSys||bgSys.n!==N) bgSys=new System(N);
  upload(bgSys,o,c,m);
}
function buildDwarf(){
  const N=3000;
  const o=new Float32Array(N*4), c=new Float32Array(N*3), m=new Float32Array(N*3);
  for(let i=0;i<N;i++){
    const r=Math.pow(Math.random(),0.5)*0.11;
    const a=Math.random()*TAU;
    const b=0.5+Math.random()*0.6;
    const t=Math.random();
    const col=lerp3([1.0,0.85,0.7],[1.0,0.55,0.6], t*0.6);
    o[i*4]=r; o[i*4+1]=a; o[i*4+2]=0.5/(0.15+r); o[i*4+3]=gauss()*0.07;
    c[i*3]=col[0]*b; c[i*3+1]=col[1]*b; c[i*3+2]=col[2]*b;
    m[i*3]=0.8+Math.random()*1.6; m[i*3+1]=Math.random(); m[i*3+2]=0;
  }
  if(!dwarfSys||dwarfSys.n!==N) dwarfSys=new System(N);
  upload(dwarfSys,o,c,m);
}

// ---------- resize ----------
let W,H,dpr;
function resize(){
  dpr=Math.min(window.devicePixelRatio||1, 2);
  W=window.innerWidth; H=window.innerHeight;
  canvas.width=W*dpr; canvas.height=H*dpr;
  canvas.style.width=W+'px'; canvas.style.height=H+'px';
  gl.viewport(0,0,canvas.width,canvas.height);
}
window.addEventListener('resize', resize);
resize();

// ---------- input ----------
let dragging=false, px=0, py=0, downT=0, downX=0, downY=0;
let pinchDist=0;
function interact(){ lastInteract=performance.now(); }
canvas.addEventListener('mousedown', e=>{
  dragging=true; px=e.clientX; py=e.clientY; downT=performance.now(); downX=e.clientX; downY=e.clientY; interact();
});
window.addEventListener('mousemove', e=>{
  if(!dragging) return;
  const dx=e.clientX-px, dy=e.clientY-py;
  px=e.clientX; py=e.clientY;
  yawV=-dx*0.0045; pitchV=dy*0.0045;
  interact();
});
window.addEventListener('mouseup', e=>{
  if(dragging && Math.hypot(e.clientX-downX, e.clientY-downY)<6 && performance.now()-downT<350){
    spawnDwarf();
  }
  dragging=false;
});
canvas.addEventListener('wheel', e=>{
  e.preventDefault();
  targetDist=Math.min(9, Math.max(0.5, targetDist*(1+Math.sign(e.deltaY)*0.12)));
  interact();
},{passive:false});
canvas.addEventListener('touchstart', e=>{
  e.preventDefault(); interact();
  if(e.touches.length===1){ dragging=true; px=e.touches[0].clientX; py=e.touches[0].clientY; downT=performance.now(); downX=px; downY=py; }
  else if(e.touches.length===2){
    pinchDist=Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
    dragging=false;
  }
},{passive:false});
canvas.addEventListener('touchmove', e=>{
  e.preventDefault();
  if(e.touches.length===1 && dragging){
    const dx=e.touches[0].clientX-px, dy=e.touches[0].clientY-py;
    px=e.touches[0].clientX; py=e.touches[0].clientY;
    yawV=-dx*0.005; pitchV=dy*0.005; interact();
  } else if(e.touches.length===2){
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
    if(pinchDist>0) targetDist=Math.min(9,Math.max(0.5,targetDist*(pinchDist/d)));
    pinchDist=d; interact();
  }
},{passive:false});
canvas.addEventListener('touchend', e=>{
  if(e.touches.length===0){
    if(dragging && performance.now()-downT<300 && Math.hypot(px-downX,py-downY)<10) spawnDwarf();
    dragging=false; pinchDist=0;
  }
});

// ---------- dwarf / big bang ----------
function spawnDwarf(){
  dwarfTheta=Math.random()*TAU;
  dwarfAct=0; dwarfAge=0;
}
document.getElementById('bang').addEventListener('click', ()=>{
  explode=1;
  interact();
});

// ---------- UI ----------
const $=id=>document.getElementById(id);
$('phead').onclick=()=>$('panel').classList.toggle('collapsed');
function bind(id, vid, fn, fmt){
  const el=$(id), lab=$(vid);
  el.addEventListener('input', ()=>{ const v=parseFloat(el.value); if(lab) lab.textContent=fmt?fmt(v):v; fn(v); });
}
let rebuildPend=false;
function queueRebuild(){
  if(rebuildPend) return; rebuildPend=true;
  requestAnimationFrame(()=>{ rebuildPend=false; buildMain(); buildNebulae(); updateCount(); });
}
bind('sStars','vStars', v=>{ state.stars=v|0; queueRebuild(); }, v=>v.toLocaleString());
bind('sArms','vArms', v=>{ state.arms=v|0; queueRebuild(); });
bind('sSpeed','vSpeed', v=>{ state.speed=v; }, v=>v.toFixed(1));
bind('sSpread','vSpread', v=>{ state.spread=v; queueRebuild(); }, v=>v.toFixed(1));
document.querySelectorAll('.pbtn').forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll('.pbtn').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    state.preset=b.dataset.p;
    buildMain(); buildNebulae();
  };
});
function bindTog(id, key){
  const el=$(id);
  el.onclick=()=>{ state[key]=!state[key]; el.classList.toggle('on', state[key]); };
}
bindTog('tGlow','glow'); bindTog('tNeb','neb'); bindTog('tAuto','auto');

const uiEls=[$('title'),$('panel'),$('hint')];
window.addEventListener('keydown', e=>{
  if(e.target.tagName==='INPUT') return;
  switch(e.key.toLowerCase()){
    case 'h': uiEls.forEach(el=>el.classList.toggle('hidden')); break;
    case ' ': e.preventDefault(); paused=!paused; break;
    case 'r':
      yaw=0.9; pitch=0.42; dist=targetDist=3.4; yawV=pitchV=0;
      dwarfAct=0; explode=0; paused=false; interact(); break;
    case 's':
      gl.clearColor(0.004,0.006,0.02,1);
      snapshot(); break;
  }
});
function snapshot(){
  const a=document.createElement('a');
  a.download='galaxy-forge.png';
  a.href=canvas.toDataURL('image/png');
  a.click();
}
const cntEl=$('cnt');
function updateCount(){ cntEl.textContent=(state.stars+3500).toLocaleString(); }

// ---------- render loop ----------
let last=performance.now(), fpsFrames=0, fpsTime=0;
const fpsEl=$('fps');
const ZERO3=[0,0,0];

function frame(now){
  const dt=Math.min(0.05,(now-last)/1000); last=now;
  if(!paused){ simTime+=dt*state.speed; }

  // inertia
  yaw+=yawV; pitch+=pitchV;
  yawV*=0.92; pitchV*=0.92;
  pitch=Math.min(1.45, Math.max(-1.45, pitch));
  dist+=(targetDist-dist)*0.12;

  // cinematic drift
  if(state.auto && !dragging && now-lastInteract>4000){
    yaw+=dt*0.06;
    const tP=Math.sin(now*0.00011)*0.30;
    pitch+=(tP-pitch)*dt*0.4;
    const tD=3.4+Math.sin(now*0.00007)*0.5;
    targetDist+=(tD-targetDist)*dt*0.25;
  }

  // dwarf update
  if(dwarfAct>0||dwarfAct===0&&dwarfAge>0){}
  if(dwarfAct>0||dwarfAge>0){
    if(dwarfAct<1) dwarfAct=Math.min(1, dwarfAct+dt*0.45);
    dwarfAge+=dt;
    if(dwarfAge>28) dwarfAct=Math.max(0, dwarfAct-dt*0.05);
  }
  if(dwarfAct>0){
    if(!paused) dwarfTheta+=dt*0.16*state.speed;
    dwarfPos[0]=Math.cos(dwarfTheta)*1.5;
    dwarfPos[1]=Math.sin(dwarfTheta*0.55)*0.42;
    dwarfPos[2]=Math.sin(dwarfTheta)*1.5*0.62;
  } else dwarfPos[0]=dwarfPos[1]=dwarfPos[2]=0;

  if(explode>0) explode=Math.max(0, explode*Math.exp(-dt*0.85));

  // camera
  const eye=[
    dist*Math.cos(pitch)*Math.sin(yaw),
    dist*Math.sin(pitch),
    dist*Math.cos(pitch)*Math.cos(yaw)
  ];
  const P=perspective(0.9, W/H, 0.01, 200);
  const V=lookAt(eye,[0,1,0]);
  const VP=mul4(P,V);

  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.useProgram(prog);
  gl.uniformMatrix4fv(U.uVP, false, VP);
  gl.uniform3fv(U.uEye, eye);
  gl.uniform1f(U.uTime, simTime);
  gl.uniform1f(U.uSpeed, 1);
  gl.uniform1f(U.uExplode, explode);
  gl.uniform1f(U.uDwarfAct, dwarfAct);
  gl.uniform1f(U.uTwinkle, 1);
  gl.uniform1f(U.uPointScale, canvas.height/850);
  gl.uniform3fv(U.uDwarfPos, dwarfPos);
  gl.uniform1f(U.uGlow, state.glow?1:0);

  gl.enableVertexAttribArray(A_ORB);
  gl.enableVertexAttribArray(A_COL);
  gl.enableVertexAttribArray(A_MISC);

  drawSys(bgSys, 0.7, ZERO3);
  if(state.neb) drawSys(nebSys, 0.05, ZERO3);
  drawSys(mainSys, 1.0, ZERO3);
  drawSys(coreSys, 0.5, ZERO3);
  if(dwarfAct>0) drawSys(dwarfSys, 1.0, dwarfPos);

  // fps
  fpsFrames++; fpsTime+=dt;
  if(fpsTime>=0.5){ fpsEl.textContent=Math.round(fpsFrames/fpsTime); fpsFrames=0; fpsTime=0; }

  requestAnimationFrame(frame);
}

buildMain(); buildNebulae(); buildBackground(); buildDwarf(); updateCount();
requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```