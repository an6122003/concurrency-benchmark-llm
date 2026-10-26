Let me build a comprehensive, polished game. I need to write a complete HTML file that includes the canvas game. Let me do this systematically:

- Canvas setup, DPR scaling, resize handling
- Audio: WebAudio, master gain, mute, music loop (bassline + drums via scheduler), SFX (laser, explosion, power-up arpeggio)
- Game state: title, playing, gameover, paused
- Background: stars, striped sun, parallax mountains, scrolling grid floor
- Player ship, auto-fire, movement (mouse/touch/keyboard)
- Enemies: weaver (sine wave), diver (dive at player), shooter (fires bullets)
- Every 5th wave, a boss with health bar, bullet patterns, multi-stage death
- Power-ups: spread shot, shield, slow-motion
- Particles, shockwaves, screen shake, hit stop, score popups, combo decay
- HUD, title screen, game-over screen using localStorage
- Scanlines + vignette overlay (either pre-render to offscreen or draw every frame — drawing a pattern is fine too; for performance, generate scanlines once as an offscreen canvas)

Let me write it efficiently, but completely. Aim for a solid ~800–1000 lines.

Main architecture:

```js
const canvas, ctx; let W, H, DPR.
resize(): DPR = min(devicePixelRatio,2); canvas.width = innerWidth*DPR etc; ctx.setTransform(DPR,0,0,DPR,0,0).
```

Game loop: last time, dt clamped, timeScale for slow-mo, hitStop timer.

World coordinates = CSS pixels.

Background elements:
- stars: array of {x,y,r,phase,speed} twinkling via sin.
- sun: large circle in upper center, gradient magenta→orange, horizontal stripe cutouts (draw stripes as sky-colored rectangles with increasing thickness toward the bottom). Actually the classic look is: a sun with the lower half striped. Draw the sun, then clip and draw transparent stripes — the easiest way: use the composite 'destination-out' trick on an offscreen sun canvas to draw stripes, then draw the offscreen with a glow. Pre-render the sun once per resize.
- mountains: two layers, generated as a random-ridge point cloud, parallax-scroll horizontally slowly? Mountains usually don't move; give them a slight horizontal drift. Draw as neon-outlined dark-filled polygons. Regenerate on resize.
- grid floor: perspective grid — horizon at about 62% of height. Vertical lines converge to the vanishing point; horizontal lines move toward the viewer using a scroll offset with exponential spacing. Draw with glowing cyan/magenta lines.

Player:
- x follows target (mouse/touch x, or keyboard speed), y is fixed near the bottom (y movable? Keep y fixed at ~H*0.85, only x movement, allow a little y too? Keep only x, simple). Actually allow slight vertical too via keyboard? Just x is fine.
- Flame particles.
- Auto-fires about every 0.22s.
- Power-up states: spread (timer), shield (hp or timer), slow-mo handled globally.

Enemies:
- spawner: waves. Each wave has a count based on wave number. Spawn at the top with type weighting.
- weaver: moves downward while x = baseX + sin(t)*amp, magenta, diamond shape.
- diver: descends, accelerates toward player x, cyan, triangle pointing down.
- shooter: hovers in the upper area, slowly drifts, fires aimed bullets, orange, hexagon.
- When off the bottom of the screen, they disappear (or count as nothing).

Boss: big ship at the top, health bar, phases based on hp: aimed spread, ring burst, spiral. On death: multiple explosion stages (sequenced explosions), big shake, score.

Bullets: player bullets (upward), enemy bullets (various). Collision via AABB or circles.

Particles: pool array with life, no need for gravity, additive drawing.

Shockwave: expanding ring.

Popups: floating text.

Combo: increases per kill, decays after 3 seconds with no kills, multiplier = 1 + floor(combo/5)? Or multiplier = min(1+combo*0.1...). Use combo count; score = base * mult, mult = 1+floor(combo/4) with a cap. Show "x3" etc.

Hit stop: on kill, freeze game updates for ~60–100ms (timeScale 0) but continue rendering.

Screen shake: shake magnitude with decay; translate ctx by a random offset.

Chromatic aberration flash: on big explosions, draw a magenta/cyan radial overlay with 'lighter' for a few frames.

Slow-mo: timeScale target 0.4, lerp, with timer; tint the screen with acid green.

Audio:
- Create AudioContext on first user gesture.
- masterGain, musicGain, sfxGain.
- Music: 132bpm scheduler, bassline pattern (e.g., A minor: A1...), kick (sine drop), hi-hat (noise HP), bass (square/saw with filter). Use look-ahead scheduling.
- SFX: laser (descending square-wave blip), explosion (noise burst + lowpass sweep), powerup (arpeggio 3–4 notes), hit (short), boss death big sound, player explosion.

Mute: M toggles masterGain.

Pause: P toggles.

Lives: 3, small ship icons in the HUD. When hit: lose a life, explosion, respawn with invulnerability, clear nearby bullets.

Game over: overlay with final score, best from localStorage 'neonSparkBest', press to restart.

Title screen: sun rises behind the logo (animate sunY), "NEON SPARK" logo with glow, pulsating prompt, grid still animating.

Let me write the code carefully.

Structure:

```html
<!DOCTYPE html><html><head><meta charset><meta viewport><title>NEON SPARK</title><style>...</style></head>
<body><canvas id="c"></canvas><script>...</script></body></html>
```

CSS: html,body margin 0, overflow hidden, background black, canvas block, cursor none? Leave cursor as crosshair.

Next the JS. Let me draft it.

```js
'use strict';
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let W=0,H=0,DPR=1,horizonY=0;
function resize(){DPR=Math.min(window.devicePixelRatio||1,2);W=window.innerWidth;H=window.innerHeight;canvas.width=W*DPR;canvas.height=H*DPR;canvas.style.width=W+'px';canvas.style.height=H+'px';ctx.setTransform(DPR,0,0,DPR,0,0);horizonY=H*0.62;buildStars();buildMountains();buildSun();buildScan();}
window.addEventListener('resize',resize);
```

Stars:

```js
let stars=[];
function buildStars(){stars=[];const n=Math.floor(W*H/6000);for(...)stars.push({x:rand*W,y:rand*horizonY*0.95,r:...,ph:...,sp:...});}
```

Mountains: generate points across the width.

```js
let mtnA=[],mtnB=[];
function ridge(peak,min,step){let p=[];let x=-step; while(x<W+step){p.push({x,y:min+Math.random()*(peak-min)});x+=step;}p.push({x:W+step,y:min});return p;}
```

Draw the mountain layer: path from (0,horizonY) through the points to (W,horizonY), dark gradient fill, stroke the top with a neon color, shadowBlur for glow.

Sun: offscreen canvas with radius r.

```js
let sunCanvas;
function buildSun(){const r=Math.min(W,H)*0.28;sunCanvas=document.createElement('canvas');sunCanvas.width=sunCanvas.height=Math.ceil(r*2+80);const s=sunCanvas.getContext('2d');const cx=(r*2+80)/2;
// gradient
const g=s.createRadialGradient... or linear top magenta? Classic: yellow/orange at top fading to magenta at bottom.
g=s.createLinearGradient(0,cx-r,0,cx+r);
g.addColorStop(0,'#ffd319');g.addColorStop(0.5,'#ff8a00');g.addColorStop(1,'#ff00c8');
s.fillStyle=g;s.beginPath();s.arc(cx,cx,r,0,7);s.fill();
// stripes: erase horizontal bands from the middle downward, increasing in thickness
s.globalCompositeOperation='destination-out';
let y=cx+ r*0.05, h=3;
while(y<cx+r){const th=h*(1+ (y-(cx+r*0.05))/(r)*2); s.fillRect(cx-r, y, r*2, th); y+=th+ (h+6);}
// Actually the classic is: gaps between stripes shrink toward the top. Simplified: bands of increasing thickness downward.
}
```

Hmm, classic sun: stripes (transparent gaps) are thicker at the bottom. My loop: y starts just below center; draw an erase band of increasing height, spacing also increases. Good.

Sun position: cx = W/2, cy = horizonY - r*0.25 (title animates sunRise from below the horizon). Sun is drawn clipped to above the horizon? It's behind mountains and grid, so just draw it before those; the grid covers the lower part. Actually the grid floor is drawn after the mountains; the sun should be above the horizon — clip the sun to y < horizonY. Use ctx.save(); clip with a rectangle above the horizon.

Grid:

```js
let gridScroll=0; // advances with dt
function drawGrid(dt){gridScroll+=dt* (slow? ...)*speed;
ctx.save();
// floor fill: dark gradient from horizon down
// vertical lines: for i in -N..N: x at the bottom = W/2 + i*spacing; line from vanishing point (W/2,horizonY) to (x, H+40)? Perspective: lines radiate from VP.
ctx.globalCompositeOperation='lighter';
// vertical:
const sp=W/14;
for(let i=-12;i<=12;i++){x1=W/2+i*sp*1.6... draw line from (W/2+i*sp*0.35?,horizonY) ...
```

Easiest perspective grid: VP=(W/2,horizonY). Vertical lines: from VP to (W/2 + i*spread, H*1.2), spread ~ W/6. Horizontal lines: rows of z positions; use t = ((k - gridScroll) mod 1); y = horizonY + (H - horizonY) * t^3 (ease to push rows toward the viewer). Line from x=0..W at that y, with alpha increasing closer to the viewer. k iterates 0..rows.

Grid color: cyan-ish with alpha; also add a magenta tint line for the horizon.

Grid glow: set ctx.shadowBlur? Costly for many lines; instead just draw with 'lighter' and 2px. OK.

Player:

```js
const player={x:W/2,y:0,tx:W/2,vx:0,speed:520,fireCd:0,lives:3,inv:0,spread:0,shield:0};
player.y = H*0.86;
```

Draw the ship: neon cyan outline path, magenta accents, engine flame particles spawned every frame.

Ship shape: sleek: nose up. Path: moveTo(0,-18) tip, curve to wings (-14,10), notch (-4,6), (0,10) tail, mirror.

Enemies stored as objects with type, x, y, t, hp, fireCd, baseX, amp, sp.

Wave system:

```js
let wave=0, waveTimer=0, spawnQueue=[], state='title';
function startWave(n){wave=n; spawnQueue=[];
 if(n%5===0){bossActive... spawn boss}
 else{const count=6+ n*2; build queue with delay}
}
```

Spawn queue items {t, type}. Wave is over when the queue is empty and enemies are empty → next wave after a 2s delay, with a "WAVE n" popup.

Boss:

```js
let boss=null;
function spawnBoss(){boss={x:W/2,y:-150,ty:H*0.2, hp:40+wave*6, max:..., t:0, pattern:0, fireCd:0, phase:0, dying:0};}
```

Boss draw: large shape, pulsating. Patterns:
- pattern 0: aimed 5-spread every 1.6s.
- pattern 1: ring of 16 bullets every 1.4s.
- pattern 2: rotating spiral bullets.
Phase changes at 2/3 and 1/3 of hp.
Death: dying timer; spawn explosions every 0.12s at random offsets, after 1.2s a final big explosion + shockwave + chromatic flash + big score.

Bullets: arrays pBullets, eBullets. Objects {x,y,vx,vy,r,color}.

Player fire: fireCd 0.22; if spread>0 spawn 3 bullets (straight, ±0.25 rad).

Collision: circles.

Particles:

```js
function boom(x,y,color,n,power){ for... particles.push({x,y,vx:cos*sp,vy:sin*sp,life:rand(0.4,1),max:...,r:rand(1,3),color}); shocks.push({x,y,r:4,v:600*power,life:0.5,max:0.5}); }
```

Popups: {x,y,txt,life,color,size}.

Screen shake: shake=Math.min(shake+amount, 40); each frame offset = (rand-0.5)*shake; shake *= exp(-8*dt) or shake-=shake*10*dt.

Hit stop: hitStop>0: hitStop-=realDt; while hitStop>0 skip world update (but background animates slightly?). Simplest: if hitStop>0, decrement with real dt and skip game update, keep drawing.

Time scale: target = slowT>0?0.35:1; lerp timeScale.

Combo: combo=0, comboT=0; on kill combo++, comboT=3; score+=base*mult; mult=1+Math.min(10, Math.floor(combo/5)). Display "COMBO x{mult} (n)"?

HUD draw: score top-left, best, wave top-right, combo in the center top when >1, lives as small ships at bottom-left? Top-left under score. Mute indicator.

Slow-mo: acid-green tint overlay + "TIME WARP" flash.

Scanline overlay: offscreen canvas with horizontal lines every 3px, low alpha; draw with drawImage each frame. Plus a radial vignette overlay (pre-rendered). Combine into one overlay canvas: scanlines + vignette.

Chromatic aberration flash: flash=1 decays; draw two offset radial gradients with 'lighter', magenta offset left, cyan right; alpha*flash.

Audio implementation:

```js
let AC=null, master, musicG, sfxG, muted=false, musicOn=false;
function initAudio(){if(AC)return;AC=new (window.AudioContext||webkitAudioContext)();master=AC.createGain();master.gain.value=0.7;master.connect(AC.destination);musicG=AC.createGain();musicG.gain.value=0.5;musicG.connect(master);sfxG=AC.createGain();sfxG.gain.value=0.8;sfxG.connect(master);}
```

SFX:

```js
function laser(){if(!AC)return;const t=AC.currentTime;const o=AC.createOscillator();o.type='square';o.frequency.setValueAtTime(880,t);o.frequency.exponentialRampToValueAtTime(220,t+0.08);const g=AC.createGain();g.gain.setValueAtTime(0.12,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.09);o.connect(g).connect(sfxG);o.start(t);o.stop(t+0.1);}
```

Explosion: noise buffer.

```js
function noiseBuffer(){if(nb)return nb;nb=AC.createBuffer(1,AC.sampleRate,AC.sampleRate);const d=nb.getChannelData(0);for(i)d[i]=Math.random()*2-1;return nb;}
function boomSfx(big){const t=AC.currentTime;const s=AC.createBufferSource();s.buffer=noiseBuffer();const f=AC.createBiquadFilter();f.type='lowpass';f.frequency.setValueAtTime(big?800:1400,t);f.frequency.exponentialRampToValueAtTime(60,t+(big?1.2:0.35));const g=AC.createGain();g.gain.setValueAtTime(big?0.6:0.35,t);g.gain.exponentialRampToValueAtTime(0.001,t+(big?1.3:0.4));s.connect(f).connect(g).connect(sfxG);s.start(t);s.stop(t+1.4);}
```

powerup: arpeggio notes [523,659,784,1047], scheduled square blips.

Music: 132bpm scheduler, 8th-note bass pattern, notes in semitones from A1 (55Hz). Pattern: [0,0,7,0, 3,3,10,3, 5,5,12,5, 7,10,7,0]? Let me try: 16 steps per bar (eighth = 2 steps? use 16th notes). Simpler: 8th note = 1 step, 16 steps per bar (2 bars). Bassline (Hz via midi): root A=21? midi A1=33? A1 midi=33? A0=21, A1=33. 55Hz = midi 33. Pattern semitones: [0,0,12,0, 3,3,15,3, 5,5,17,5, 10,7,3,0] as 16 eighth notes = 2 bars at 132bpm → eighth = 60/132/2 = 0.2273s.

Drums: kick on step 0,4,8,12 (four-on-the-floor per bar → in 16-step pattern steps 0,4,8,12). Hat on off-beats: odd steps (steps 2,6,10,14) open-ish, or every step small. Snare-like on 4,12 (noise burst bandpass).

Scheduler:

```js
let nextNote=0,step=0;
function scheduleMusic(){if(!AC||!musicOn)return;const spb=60/132/2; while(nextNote<AC.currentTime+0.15){playStep(step,nextNote);step=(step+1)%16;nextNote+=spb;}}
```

Call from rAF loop.

playStep(step,t): bass: if pattern[step]!=-1: saw osc, frequency midiToFreq(33+semi), lowpass 300Hz, gain envelope 0.18→0. Kick: sine 120→40 0.12s, gain 0.5. Hat: small noise burst, highpass 6000, gain 0.08.

midiToFreq=m=>440*Math.pow(2,(m-69)/12).

Mute toggle: master.gain.value = muted?0:0.7.

Input:

- mousemove: player.tx = e.clientX (only while playing).
- touchstart/move: tx = e.touches[0].clientX; on title/gameover, tap starts.
- mousedown: start / also start on gameover restart.
- keydown: track keys (a,d,arrowleft,right), p pause, m mute, space/enter start.
- keyboard movement: in update if left/right keys then tx += speed*dt.

Game flow:

State 'title' → click/key → resetGame(), state 'playing', start music (initAudio, musicOn=true, nextNote=AC.currentTime+0.1).

resetGame: player lives 3, score 0, wave 0, arrays clear, startWave(1) with delay.

Wave management:

```js
let waveState='inter', waveDelay=2;
update: if(!boss){ if(waveState==='inter'){waveDelay-=dt; if(waveDelay<=0){wave++; startWave(wave);} } else { // spawn queue
 for q items with t<=0: t+=dt; if t<=0 spawn
 if(queue empty && enemies.length===0){waveState='inter';waveDelay=2.2; popup "WAVE "+(wave+1)?? }
}}
```

Popup "WAVE X" at the start of a wave.

Enemy spawn:

```js
function spawnEnemy(type){const e={type,x:rand(W*0.15,W*0.85),y:-30,t:0,hp:1,fireCd:rand(0.5,1.5),...};
 weaver: amp rand(40,110), sp rand(70,120), baseX=x;
 diver: sp rand(120,180), vy...
 shooter: ty rand(H*0.15,H*0.35), sp 30;
}
```

Enemy update:

- weaver: t+=dt; y+=sp*dt; x=baseX+sin(t*2.2)*amp; hp=1.
- diver: y+=sp*dt; x+= (player.x - x)*dt*1.5; sp increases slightly; hp=1.
- shooter: y approaches ty (easing), x slowly drifts with sin; fireCd-=dt; if y>0 && fireCd<=0 && y<H*0.6: aimed bullet at player speed 160; fireCd=1.8+rand.
- If y> H*0.8 (past player line), remove, no penalty (or small one? none).

Enemy-player collision: if player not invulnerable: lose life, destroy enemy with explosion.

Enemy draw:
- weaver: magenta diamond (#ff2d95) with glow.
- diver: cyan downward triangle.
- shooter: orange hexagon.
shadowBlur=12, shadowColor=color, fill dark + stroke neon.

Boss draw: big magenta/orange ship, width ~ min(W*0.4, 300). Health bar at top: gradient.

Player bullet: cyan bolt (rect glow). Enemy bullet: orange circle with glow; boss bullet maybe acid.

Power-up: {x,y,vy:60,type} falling; types: 'spread' (green #76B900 "S"), 'shield' (cyan "O"?), 'slow' (magenta). Draw as glowing rotating square with a letter. Spawn probability 0.18 on enemy death; boss drops 2.

Effects:
- spread: player.spread=10s.
- shield: player.shield=8s (absorbs hits; drawn as a bubble).
- slow: slowT=5s.

Player hit: if shield>0: shield=0 (or absorbs one), spark; else lives--, inv=2s, explosion at player position, shake, if lives<=0 → game over (state='gameover', save best, stop? keep music? stop music: musicOn=false; final boom sound).

Game over screen: "GAME OVER", final score, best, "CLICK TO RESTART", pulsating.

Title: sun rising: titleT grows; sunY goes from horizonY+ r to its final position in the first 2.5s with easing; logo with glow, letter spacing; prompt pulsing alpha.

Also show controls hint on the title.

HUD easing: display score lerps to score.

Perf: keep particle count reasonable; use ctx.globalCompositeOperation='lighter' for glow passes.

Order per frame:
1. clear with sky gradient (full draw).
2. stars.
3. sun (with clip).
4. mountains back, front.
5. grid.
6. if playing/gameover: entities (particles behind? draw enemies, bullets, player, powerups with lighter glow).
7. particles + shocks (lighter).
8. popups.
9. HUD.
10. overlays: chromatic flash, slow tint, scan+vignette (normal composite), pause text.

Hit stop: on kill set hitStop=0.05 (0.25 on boss stage death).

Time:

```js
let last=0;
function frame(ts){requestAnimationFrame(frame);const rdt=Math.min(0.05,(ts-last)/1000||0);last=ts;
 if(!paused){ // always animate background?
 }
 if(hitStop>0){hitStop-=rdt; dt=0;} else {
  timeScale+= (targetScale-timeScale)*Math.min(1,rdt*6);
  dt=rdt*timeScale;
 }
 // title anim uses rdt
 update(dt, rdt); draw();
}
```

Pause: freeze update, dim + "PAUSED" text.

Let me write the final code. Keep it tidy but complete. I'll also handle 'contextmenu' prevention, and touch.

Edge: localStorage in try/catch.

Draw small ship icon for lives: reuse ship draw scaled.

Let me write it.

Grid draw details:

```js
function drawGrid(){
const gy=horizonY;
// floor fill
const fg=ctx.createLinearGradient(0,gy,0,H);
fg.addColorStop(0,'#14002b');fg.addColorStop(1,'#03000a');
ctx.fillStyle=fg;ctx.fillRect(0,gy,W,H-gy);
ctx.save();ctx.globalCompositeOperation='lighter';
// vertical lines
ctx.strokeStyle='rgba(0,255,255,0.25)';ctx.lineWidth=1;
const vp=W/2;
for(let i=-14;i<=14;i++){
 const x0=vp+i*10; // slight fan at horizon
 const x1=vp+i*(W/10);
 ctx.beginPath();ctx.moveTo(x0,gy);ctx.lineTo(x1,H+50);ctx.stroke();
}
// horizontal lines
gridScroll=(gridScroll+dtGlobal*0.55)%1;
const rows=14;
for(let i=0;i<rows;i++){
 let t=((i+gridScroll)/rows);
 // t in 0..1, 1 = near viewer
 const y=gy+(H-gy)*(t*t*t); // perspective: actually use t^3 to bunch near horizon
 const a=0.05+0.35*(t*t);
 ctx.strokeStyle=`rgba(255,45,149,${a})`? or mix: magenta lines.
 ctx.lineWidth=1+t*1.5;
 ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();
}
// horizon glow line
ctx.strokeStyle='rgba(255,211,0,0.8)';shadowBlur...
}
```

dtGlobal: pass dt to the draw function — simpler to advance gridScroll in update.

I'll pass the needed dt.

Sky gradient:

```js
const g=ctx.createLinearGradient(0,0,0,horizonY);
g.addColorStop(0,'#05010f');g.addColorStop(0.55,'#1b0340');g.addColorStop(1,'#4a0a5e');
```

Mountains: 2 arrays of points.

```js
function buildMountains(){
 mtnBack=ridge(0.45,0.18, 90); // height above horizon in fraction of H? use pixels: h1=H*0.35
}
```

ridge(peakH, step): points across the width: y = horizonY - (0.3+0.7*rand)*peakH? Make jagged: each point has random height.

Draw:

```js
function drawMtn(pts,color,fill){
ctx.beginPath();ctx.moveTo(0,horizonY+2);
for(p of pts)ctx.lineTo(p.x,p.y);
ctx.lineTo(W,horizonY+2);ctx.closePath();
ctx.fillStyle=fill;ctx.fill();
ctx.save();ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.shadowColor=color;ctx.shadowBlur=14;ctx.beginPath();
for... stroke just the ridge line (not closed);
ctx.restore();
}
```

Points: x from -40 to W+40 in step 60–110. y=horizonY - (0.25+0.75*rand)*H*0.32 (back), front layer smaller? Front is usually closer/lower: front H*0.18, back H*0.3. Back is darker with magenta line, front darker fill with cyan line? Synthwave: back mountains with magenta outline, front darker with cyan? Let's do back: fill '#160b2e', stroke '#ff2d95' faint; front: fill '#0b0518', stroke '#00e5ff'.

Drift: offset the whole ridge slowly with xoff = (t*8 % step)? That shifts the shape; simpler: draw the points with (x + off) mod? Wraparound is complex. Just have a very slow horizontal drift where we draw the ridge at x+off with off oscillating slightly: off = sin(time*0.05)*10. Good.

Sun draw:

```js
function drawSun(){
const r=sunR; const sx=W/2; const sy=sunYcur;
ctx.save();
ctx.beginPath();ctx.rect(0,0,W,horizonY);ctx.clip();
ctx.globalCompositeOperation='lighter';
ctx.shadowColor='#ff8a00';ctx.shadowBlur=60; // expensive on big image; instead draw twice with low alpha?
ctx.drawImage(sunCanvas, sx-(sunCanvas.width/2), sy-(sunCanvas.height/2));
ctx.restore();
}
```

shadowBlur on a large drawImage is expensive; instead draw the image normally + an additive radial glow behind it:

```js
const gl=ctx.createRadialGradient(sx,sy,r*0.4,sx,sy,r*1.6);
gl.addColorStop(0,'rgba(255,80,180,0.35)');gl.addColorStop(1,'rgba(255,80,180,0)');
```

Draw the glow first, then the sun image (normal composite).

Title sun rise: sunY = horizonY + r*0.9 → lerp to horizonY - r*0.35 with ease-out over titleT.

During play, sun at horizonY - r*0.35.

Now let me write the ship draw function:

```js
function shipPath(s){ // s = scale
 ctx.beginPath();
 ctx.moveTo(0,-20*s);
 ctx.quadraticCurveTo(6*s,-8*s, 16*s,10*s);
 ctx.lineTo(7*s,6*s);
 ctx.lineTo(0,12*s);
 ctx.lineTo(-7*s,6*s);
 ctx.lineTo(-16*s,10*s);
 ctx.quadraticCurveTo(-6*s,-8*s,0,-20*s);
 ctx.closePath();
}
function drawShip(x,y,s,color){
 ctx.save();ctx.translate(x,y);
 ctx.shadowColor=color;ctx.shadowBlur=16;
 shipPath(s);
 ctx.fillStyle='rgba(0,20,40,0.9)';ctx.fill();
 ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();
 // cockpit
 ctx.beginPath();ctx.arc(0,-6*s,3.5*s,0,7);ctx.fillStyle='#76B900';ctx.shadowColor='#76B900';ctx.fill();
 ctx.restore();
}
```

Engine flame: spawn 3 particles per frame at (x±3, y+12), vy positive, color orange/cyan, small.

Player invuln blink: skip draw when (t*20)%2<1.

Shield bubble: circle around player, cyan, alpha pulsing, lighter.

Boss draw:

```js
function drawBoss(){
 const w=Math.min(W*0.42,340), x=boss.x, y=boss.y;
 ctx.save();ctx.translate(x,y);
 const pulse=1+0.05*Math.sin(boss.t*5);
 ctx.shadowColor='#ff2d95';ctx.shadowBlur=25;
 ctx.beginPath();
 ctx.moveTo(-w/2,0);
 ctx.lineTo(-w*0.3,-h*0.35); ...
```

Keep it simpler: an angular saucer shape:

```js
const h=w*0.32;
ctx.moveTo(-w/2,0);ctx.lineTo(-w*0.35,-h*0.5);ctx.lineTo(-w*0.1,-h*0.25);ctx.lineTo(0,-h);ctx.lineTo(w*0.1,-h*0.25);ctx.lineTo(w*0.35,-h*0.5);ctx.lineTo(w/2,0);ctx.lineTo(w*0.3,h*0.4);ctx.lineTo(-w*0.3,h*0.4);close.
```

Fill with a dark gradient, stroke magenta, plus a central acid-green core circle that pulses with hp.

Boss health bar: top center: width W*0.5.

OK — boss movement: x = W/2 + sin(t*0.6)*W*0.22; y eases to H*0.2.

Boss bullets: aimed spread: compute angle to player + offsets. Ring: 18 bullets. Spiral: keep an angle, every 0.06s spawn 2 bullets at angle and angle+π, angle+=0.35.

Boss phase: phase = hp>2/3?0 : hp>1/3?1:2 → pattern selection.

Boss death sequence: boss.dying>0; boss.dying+=dt; every 0.12 spawn explosion at random within boss rect, small shake, hitStop 0.03; after 1.1: big boom, flash=1, shock, score += 5000*mult, popup, drop 2 powerups, boss=null, waveState='inter'.

Player bullet vs boss: damage 1; hit spark.

Now popups float up and fade.

HUD:

```js
ctx.font='bold 20px monospace'; etc.
score display: dispScore+= (score-dispScore)*min(1,dt*10).
```

Combo: draw "COMBO ×{mult}" top-center when combo>=2, alpha based on comboT.

Life icons: draw small ships top-left at scale 0.5.

Mute: if muted show "MUTED" small bottom-right.

Pause overlay.

Chromatic flash draw:

```js
if(flash>0){
 ctx.save();ctx.globalCompositeOperation='lighter';
 const a=flash*0.5;
 const g1=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,Math.max(W,H)*0.7);
 ... magenta on one side: actually easier: 2 full-screen semi-transparent gradient rects offset.
```

Simpler chromatic: draw two big radial gradients offset ±10*flash px, magenta and cyan, alpha flash*0.35. Good.

Slow-mo tint: acid green alpha 0.08 full-screen + border glow.

Scanlines overlay canvas: build on resize:

```js
function buildScan(){
 scanC=document.createElement('canvas');scanC.width=W;scanC.height=H;
 const s=scanC.getContext('2d');
 s.fillStyle='rgba(0,0,0,0.16)';
 for(let y=0;y<H;y+=3)s.fillRect(0,y,W,1);
 const v=s.createRadialGradient(W/2,H/2,Math.min(W,H)*0.4,W/2,H/2,Math.max(W,H)*0.75);
 v.addColorStop(0,'rgba(0,0,0,0)');v.addColorStop(1,'rgba(0,0,0,0.55)');
 s.fillStyle=v;s.fillRect(0,0,W,H);
}
```

Draw at the end with ctx.drawImage(scanC,0,0).

Now input handlers:

```js
const keys={};
addEventListener('keydown',e=>{keys[e.key.toLowerCase()]=true;
 if(e.key===' '||e.key==='Enter'){action();}
 if(e.key.toLowerCase()==='p')togglePause();
 if(e.key.toLowerCase()==='m')toggleMute();
});
```

action(): if state title → start; if gameover → start (restart); if playing → nothing.

Mouse: mousedown → action(). mousemove: if playing player.tx=e.clientX.

Touch: touchstart: action(); tx=...; touchmove: tx.

Gameover: small delay before allowing restart (0.8s) to avoid mis-tap.

Also start music on start().

Score values: weaver 100, diver 150, shooter 200, boss 5000.

Combo multiplier: mult = 1+Math.floor(combo/5), cap 8? Combo decays: comboT-=dt; when <=0 combo=0.

Hit stop on kill: hitStop=Math.max(hitStop,0.045).

Screen shake: add shake on kill (3), player hit (14), boss stage (8), boss death (30).

Now let me assemble everything into the final answer. I'll write it carefully to avoid syntax errors.

Also, "auto-fire" only during play and when not paused.

Let me write the update function:

```js
function update(dt,rdt){
 time+=rdt; // global anim time (for title etc.)
 // background grid scroll: gridScroll+=rdt*0.6 (always, even in title)
 if(state==='title'){ titleT+=rdt; return; }
 if(state==='gameover'){ goT+=rdt; updateFx(dt); return; }
 if(paused) return;
 if(state!=='playing') return;
 // slow-mo
 slowT=Math.max(0,slowT-dt);
 // player
 updatePlayer(dt);
 // spawn
 updateWaves(dt);
 updateEnemies(dt);
 updateBoss(dt);
 updateBullets(dt);
 updatePowerups(dt);
 updateFx(dt);
 // combo
 if(comboT>0){comboT-=dt;if(comboT<=0)combo=0;}
}
```

updateFx handles particles, shocks, popups, shake decay, flash decay, hitStop? hitStop handled in frame loop.

Collisions inside updateBullets and enemy updates.

OK let me write the final code. Being thorough. Rough length is fine.

One caveat: `time` is global for twinkles and such.

Let me write it all.

For boss spiral pattern: store boss.spiralA.

Enemy aimed bullet:

```js
const a=Math.atan2(player.y-e.y,player.x-e.x);
eBullets.push({x:e.x,y:e.y+10,vx:Math.cos(a)*170,vy:Math.sin(a)*170,r:5,c:'#ff8a00'});
```

Player bullet: {x,y,vx:0,vy:-620, r:3, c:'#00e5ff'} plus spread ones with angles.

Spread: angle -0.28, 0, 0.28; vx=sin*620, vy=-cos*620.

Bullet draw: lighter, shadowBlur.

Player bullet vs enemy: for each bullet, for each enemy, dist < enemy.r+bullet.r → enemy.hp--; remove bullet; spark; if hp<=0 killEnemy.

killEnemy(e): boom, score popup, combo++, hitStop, chance drop, music? no.

Boss collision radius ~w/2.

Enemy radius: 14–18.

Player radius 12.

Player bullet vs boss: same loop if boss && !boss.dying.

Enemy bullet vs player: dist< r+12 → if inv>0 nothing; else hit.

Player hit:

```js
function hitPlayer(){
 if(player.inv>0)return;
 if(player.shield>0){player.shield=0; boom(player.x,player.y,'#00e5ff',20,0.6); sfx shield; return;}
 player.lives--;player.inv=2; shake=Math.min(30,shake+16); boom(player.x,player.y,'#ff2d95',40,1); hitStop=0.12; boomSfx(false);
 if(player.lives<=0){gameOver();}
}
```

gameOver: state='gameover', goT=0, musicOn=false, save best, flash=0.6, big boom.

On respawn also clear nearby enemy bullets: eBullets = eBullets.filter(dist>200).

Wave popup: popups.push big centered "WAVE 3" — use a separate waveText timer: waveMsg, waveMsgT; draw with easing scale in the center.

OK. Also show "CLICK OR TAP TO START" and on title show a control hint line: "MOUSE / TOUCH / WASD · P PAUSE · M MUTE".

Best shown on title.

Now let me finalize the code text. I'll try to keep it clean.

Note: shadowBlur is used a lot; should be OK if counts are low. Particles drawn without shadow (lighter only) for performance.

Let me write the final HTML.
