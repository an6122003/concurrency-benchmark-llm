The user wants a big update. Let me plan carefully and keep everything that works.

Key changes:
1. Sun stripes visible above mountains. The sun canvas has stripes in the lower half. The sun is drawn at horizonY - sunR*0.35, so its center is above horizon. Mountains are drawn after sun, and their peaks reach up to ~H*0.30 (back) and H*0.17 (front) above horizon. The sun center is at horizonY - sunR*0.35. With sunR = min(W,H)*0.28. On a 1920x1080 screen, H=1080, sunR~302, horizonY=670. Sun center y = 670-106=564. Sun top = 564-302=262, sun bottom=866 (below horizon). Mountains back peak reach up to horizonY - H*0.30 = 670-324=346. So mountains cover from ~346 down to horizon. Sun's striped region is in lower half of sun (from center+0.12R down). Lower half of sun = 564+36 to 866, i.e. y from 600 to 866. That's mostly behind mountains (346 to 670) and grid (670+). So stripes ARE hidden. 

Fix: I need to make sun stripes visible above the mountains. Options:
- Draw sun higher / bigger so stripes are above mountain peaks.
- Make the stripe cut-outs span the full disc (both halves) so they're visible even where disc is above mountains.
- Draw mountains lower (reduce peak height) so sun stripes show.
- Draw the sun after mountains (in front) but then sun occludes mountains which is weird.

Best approach: Make stripes span more of the disc (start from center going up a bit and down), and raise the sun so a good portion of the striped area is above the mountain line. Also reduce mountain peak heights so they don't cover as much. Actually the simplest robust fix: draw the sun ABOVE the horizon more (raise it), and extend the stripes to the upper portion too, and draw the grid/mountains only up to their height so stripes show.

Actually the classic synthwave look: stripes across the whole sun, with the top of the sun above the horizon and bottom cut off by horizon. Mountains are small. Let me make:
- Sun center higher: horizonY - sunR*0.5 (so more of it above horizon).
- Stripes across full disc height but with the upper stripes thinner/shorter so the top stays mostly solid (classic look has solid top, striped bottom). Actually classic sun has solid top portion and striped bottom portion. The bottom is cut by the horizon/grid. 

The problem is mountains covering it. Let me reduce mountain heights significantly (back peak H*0.18, front H*0.10) and make sun bigger relative, and draw sun so its striped band is above the mountain line.

Let me reconsider geometry. I want:
- Sun center at y = horizonY - sunR*0.55 (raised)
- Mountains peak at horizonY - H*0.18 max.
- The sun's striped region: from center+0.05R downward. Center = horizonY - 0.55R. Stripes from horizonY-0.5R downward. Bottom of sun at horizonY -0.55R + R = horizonY+0.45R (below horizon, cut). So stripes visible from horizonY-0.5R to horizonY = 0.5R tall region above horizon. Mountain peaks at horizonY - 0.18H. With H~1080, 0.18H=194, so mountains reach up to horizonY-194=476. Stripes region top at horizonY-0.5R = 670-151=519. So stripes start at 519, mountains reach 476 — mountains cover stripes from 476 down! Still partially hidden.

Hmm. The fundamental issue: mountains are tall relative to sun. Let me just make mountains shorter. Back peak H*0.12 (=130, up to 540), front H*0.08 (=86, up to 584). Stripes start at 519. Mountain back reaches 540 > 519, still a bit. 

Alternative: Draw sun stripes so they're visible in the clear sky. The cleanest is to make the sun mostly above the horizon with stripes on the upper-visible area. But that breaks the classic look.

Better: The classic look has the sun sitting ON the horizon with the bottom half striped and cut by horizon. Mountains should be small/low, in the distance, not overlapping much of the sun. Let me make mountains short (like low distant ridges) so they sit at the horizon line, and keep the sun's striped lower half visible above the horizon and above these low ridges.

Let me set:
- back peak: H*0.10
- front peak: H*0.06
- sun center: horizonY - sunR*0.45
- stripes: from center+0.0 to center+R (full lower region), but actually let me put stripes across the whole visible area with the top ~30% solid.

Let me recompute with back peak H*0.10=108 (up to 562), front 65 (up to 605). Sun center = 670 - 0.45*302 = 670-136 = 534. Sun top=232, bottom=836. Stripes from center+0.05R=549 down to 836. Visible above horizon (670): stripes from 549 to 670 = 121px tall striped band, above horizon. Mountains reach up to 562 (back). So the top ~13px of the striped band (549-562) is behind mountains, rest visible. That's fine — mostly visible!

Actually even better to make stripes start higher so they're clearly above mountains. Let me start stripes at center+0.0 (534) and make the band from 534 down. Mountains reach 562. So 534-562 (28px) behind mountains, 562-670 (108px) clearly visible striped. 

Also I should draw mountains BEHIND the sun? No, mountains in front of sun is normal (sun behind mountains). That's correct. The point is just that enough stripe shows above the mountain line.

Let me also make the sun a bit bigger: sunR = min(W,H)*0.32.

Let me finalize:
- sunR = min(W,H)*0.30
- sun center (playing) = horizonY - sunR*0.45
- mountains: back peak H*0.11, front peak H*0.07
- stripes: begin at center + 0.02R, increasing spacing downward, covering to bottom.

Also the title sun rises and I should ensure it looks striped there too — it uses same buildSun so fine.

Let me also ensure the stripe canvas cut-out region: currently `y=cx+sunR*0.12`. Let me change to `y=cx+sunR*0.02` and go to `y<cx+sunR`. Good. And make stripes a bit thicker for visibility.

Now let me also make sure the sun in title rises above mountains nicely — title uses sunY going from below to horizonY - sunR*0.35. Let me align title final position to playing position (horizonY - sunR*0.45) for consistency. Fine.

Now the other fixes:
- Shooter parking forever: add a lifetime to enemies. After e.g. 8-12 seconds, shooters should dive at the player or leave. I'll add e.life timer; when exceeded, convert to dive behavior (or remove after leaving). Simplest: give all enemies a max lifetime; shooters after life start diving at player (like divers). Also ensure if an enemy goes off screen it's removed. Divers dive and eventually go off bottom — removed. Weavers go down and off bottom — removed. So only shooters hover. Fix: shooters after e.life>8 dive.

Let me add: in shooter update, if e.t > e.diveAt (random 7-12s), set a dive flag making it descend toward player and increase speed; then it'll go off bottom and be removed. Also cap: if e.y>H*0.95 remove. Already have `if(e.y>H*0.9){enemies.splice}`. So diving shooter will descend and be removed. Good.

Now the big campaign features. This is a lot. Let me structure.

Game states: 'title', 'intro', 'playing', 'upgrade', 'gameover', 'victory'. Plus paused flag. Also 'sectortitle' could be a sub-state during playing or a separate state. Let me use separate states to keep it clean, but sector title card is brief. I'll add state 'sector' (title card) that auto-advances to playing.

Let me define campaign data:

sectors = [
 { name:'SUNSET BOULEVARD', 
   palette: {skyTop:'#04000e',skyMid:'#1a0338',skyHor:'#4a0a5e', sun:['#ffe14d','#ff9500','#ff3080','#e000a0'], grid:'#ff2d95', gridH:'rgba(0,229,255,0.18)', mtnBack:'#ff2d95', mtnFront:'#00e5ff'},
   enemyMix: {weaver:0.5,diver:0.3,shooter:0.2},
   waves:4,
   boss:{name:'GLITCHWING', ...} },
 { name:'CHROME CANYON',
   palette: {skyTop:'#000a0e',skyMid:'#002a38',skyHor:'#004a5e', sun:['#c0fff0','#00e5ff','#00a0ff','#0050ff'], grid:'#00e5ff', mtnBack:'#00e5ff', mtnFront:'#76B900'},
   enemyMix:{weaver:0.3,diver:0.4,shooter:0.3},
   waves:4, boss:{name:'CANYON WARDEN'} },
 { name:'THE CORE',
   palette: {skyTop:'#0a0005',skyMid:'#38031a',skyHor:'#7a0a2e', sun:['#fff0a0','#ff5020','#ff2020','#800000'], grid:'#ff8a00', mtnBack:'#ff8a00', mtnFront:'#ff2d95'},
   enemyMix:{weaver:0.33,diver:0.33,shooter:0.33},
   waves:4, boss:{name:'THE STATIC', finale:true} }
]

Each sector: 4 normal waves then 1 boss. So sector progress: waves 1..4 normal, wave 5 boss. After boss -> upgrade screen (except after final boss -> victory).

Let me track: sector index (0-based), waveInSector (1..5). When waveInSector<5 normal, ==5 boss. After boss death -> if sector==2 -> victory, else -> upgrade screen, then next sector with sector title card.

Let me restructure wave logic:
- state 'playing', sub state waveState: 'inter','spawning','boss'
- currentSector = 0
- waveInSector = 1
- On start: show sector title card? The first sector — after intro we could show sector 1 title card then start. Let me show a sector title card at the start of each sector including the first.

Flow:
intro (typewriter) -> [click skips to] sector title card (sector 1) -> playing (wave 1)... -> boss -> upgrade card -> sector title card (sector 2) -> playing ... -> boss -> upgrade -> sector title card (sector 3) -> playing ... -> final boss -> victory.

Let me define a function showSectorCard(sec) that sets state='sector', sectorCardT=0. In frame, when state 'sector', increment; after ~2.5s auto -> start playing with reset sector waves.

Let me define enterSector(sec):
 currentSector=sec; waveInSector=1;
 startWave with a "sector" context. Actually the first wave after sector card.

Let me rework startWave to take waveInSector and sector:
 function beginWave():
   if waveInSector===5 -> boss wave (create boss per sector)
   else normal spawn with sector enemy mix and count scaling with sector.

After boss defeated:
   if currentSector===2 -> victory
   else -> state='upgrade' (show 3 cards). On pick -> apply, enterSector(currentSector+1) (show sector card) -> playing.

Wave progression after normal wave clears:
   waveInSector++; if waveInSector>5 (shouldn't happen since 5 is boss) ... actually after boss handled separately. After normal wave 4 clears -> waveInSector becomes 5 -> next is boss. Good.

Let me track totalWave for display: totalWave = currentSector*5 + waveInSector.

Upgrades: keep an upgrades object: {fireRate, twin, extraLives, shieldDur, magnet}. Cards:
 - Faster Fire: fireRate *=0.8 (min 0.55)
 - Twin Shot: +1 bullet (spread base? Actually separate from powerup spread). Let me make twin add a second bolt; multiple stacks.
 - +1 Life: lives+1
 - Longer Shield: shieldDur*1.5 (also increases powerup shield duration)
 - Magnet: magnet radius bigger (attract powerups)
 - Overdrive boost: overdrive fills faster

I'll present 3 random distinct cards each time.

Overdrive: overdrive meter 0..1, fills with combo kills (and scoring). Space to unleash: screen-clearing burst — destroys all enemies, clears enemy bullets, big damage to boss. Cooldown: meter resets to 0 after use.

Let me store player.upgrades = {twin:0, fireRate:1, shieldDur:1, magnet:0, overdriveGain:1, extraLifeApplied:false...}. And lives separate.

Let me keep it manageable.

Stats for victory: score, maxCombo, accuracy (bullets hit / bullets fired), time (elapsed since game start). Track shotsFired, shotsHit.

Hard mode: on victory, button "HARD MODE". Hard mode = harder difficulty (enemy count up, boss hp up, faster). Store hardMode flag. In hard mode, enemies scale more. Also maybe start fresh.

Let me implement a difficulty multiplier: diff = hardMode?1.5:1. Enemy count = base + floor(sector*2)*... times diff. Boss hp scaled by diff.

Now intro typewriter lines:
"The Static is a corrupting signal — a living glitch in the Neon Grid.
It devours the light, one district at a time.
The Grid is dark. Everyone is gone.
Except you. SPARK. The last light-runner."

4 lines. Typewriter effect, click to skip.

Let me implement state 'intro': introT accumulates; reveal characters gradually. Click -> go to sector card.

Let me now also handle the sector title card content: sector name + a subtitle line.

Sector subtitles:
1. Sunset Boulevard — "The last sunset. Hold the light."
2. Chrome Canyon — "Steel canyons. Fast and cold."
3. The Core — "The heart of the signal. End this."

Boss taunts:
1. GLITCHWING: "You're just a flicker."
2. CANYON WARDEN: "This canyon is mine."
3. THE STATIC: "I am the noise between your stars."

Now let me code boss per sector. Boss object: {x,y,ty,hp,max,t,fireCd,phase,dying,dieT,dieBoom, spiralA,spiralCd, name, color, finale}. Attack patterns vary by sector:
- Boss 1 (GLITCHWING, magenta): 
   phase0: aimed spread (5 bolts)
   phase1: rotating fan / sine sweep
   phase2: aimed + ring
- Boss 2 (CANYON WARDEN, cyan):
   phase0: side walls of bullets (streams)
   phase1: spirals
   phase2: aimed rapid + rings
- Boss 3 (THE STATIC, finale, acid/orange):
   phase0: noise burst (random many bullets) 
   phase1: static scanline (horizontal waves) + aimed
   phase2: everything: dense spiral + aimed + rings

Let me keep patterns with switch by boss.id.

Boss look: 
- Boss1: winged triangle (glitch wing) magenta.
- Boss2: hexagonal chrome shield cyan.
- Boss3: big glitchy orb / face, static — finale. Make it a large pulsing core with glitch noise.

Let me write a drawBoss function with branches.

Now the big question: file size. It's going to be long but that's fine.

Let me also make sure existing mechanics still work and I keep: enemies (weaver/diver/shooter), powerups (spread/shield/slow), combo, hit-stop, screen shake, popups, particles, HUD, sound, music.

Let me integrate upgrades into player firing and powerups:
- fireRate: player.fireCd base = 0.22 * fireRate. With spread powerup 0.18*fireRate.
- twin: number of extra bolts. Base bolts: if spread>0: 3 bolts; plus twin adds? Let me combine: base shot count = 1 + twin; with spread, angles spread out. Simpler: compute angles array. If spread>0: base angles [-0.28,0,0.28] else [0]; then add twin offsets. Actually let me do: 
  bullets: always fire `1+twin` bolts at center-ish, and if spread, fire a wider 3-way. Let me keep simple: 
  const spread = player.spread>0;
  const n = 1+player.upg.twin;
  For i in 0..n-1: angle = (i-(n-1)/2)*0.12; fire bolt at angle.
  if spread: additionally fire 3 bolts at -0.3,0,0.3.
  That gives nice multi-shot. Good enough.

- shieldDur: when shield powerup picked, player.shield = 8*shieldDur.
- magnet: powerups within magnet radius get pulled toward player.
- overdriveGain: overdrive fills = base * overdriveGain.

Let me implement overdrive: player.overdrive (0..1). On kill: overdrive += 0.03*overdriveGain + combo*0.002, clamp 1. Space to unleash if >=1: clear enemies (kill all, award points), clear eBullets, damage boss by big chunk, big fx. Reset to 0.

HUD: show overdrive meter bar (acid green). Show "SPACE" hint when full.

Now let me also handle accuracy: shotsFired increments per bolt fired; shotsHit increments when a pBullet hits an enemy/boss.

Time: gameTime accumulates while state==='playing' (and not paused). Actually accumulate across whole run. Let me accumulate runTime in update while playing.

Max combo: track maxCombo.

Now the input for upgrade keys 1-3 and click. And victory buttons (play again / hard mode) - clickable regions on canvas. Let me implement canvas button hit-testing.

For victory screen buttons: "PLAY AGAIN" and "HARD MODE". Draw as boxes; store their rects for hit test. On click, check.

Also restart on game over (existing) should reset to intro? The requirement: "instant restart". Let me keep game over -> restart goes straight to playing (skip intro) or to title? Original did startGame directly. Let me have game-over restart go to intro (story) again? The spec says intro after clicking start. Let me keep it: game over "CLICK TO RESTART" -> startGame() which now goes to intro. And "play again" on victory -> intro (normal). Hard mode -> intro with hardMode.

Actually to be safe and match "instant restart", let me make game-over restart go directly into a fresh run (intro is short, click to skip). That's fine.

Let me now also handle: the sector card should be skippable? It's brief (2.5s) auto. Fine.

Let me now write the whole thing. This is big. Let me be careful with the palette theming — I'll store current palette in `pal` and use in drawSky/drawSun/drawGrid/drawMtn. But buildSun uses fixed gradient. I need sun color per sector. Let me rebuild sun when palette changes (on sector change). I'll call buildSunWithPalette().

Let me refactor:
- pal object with sky colors, sunStops (array of 4 colors), gridColor, gridV (vert line rgba), mtnBack, mtnFront, horizonColor.
- buildSun() uses pal.sun stops.
- setSectorPalette(i) sets pal and rebuilds sun.

drawSky uses pal.skyTop/Mid/Hor.
drawGrid uses pal.grid for horizontal lines and pal.gridV for vertical, pal.horizon for the bright horizon line.
drawMtn uses pal.mtnBack / mtnFront.

Good.

Now let me be careful: the sun is drawn with a glow gradient too; I'll base glow on pal.sun middle colors. Let me just use fixed-ish glow derived from pal.sun[2].

Let me write buildSun to accept stops.

Now for the sun position and mountains I'll set at resize and use.

Let me define geometry constants in resize:
 sunR=Math.min(W,H)*0.30
 sunCY (playing) = horizonY - sunR*0.45
 mtn back peak = H*0.11, front = H*0.07
Let me store mountainPeak in ridge building? ridge uses peak param. Let me set peaks: buildMountains uses H*0.11 and H*0.07.

Wait earlier ridge(peak,step) generated y=horizonY-(0.25+0.75*rand)*peak. So max peak ~horizonY-peak. With peak H*0.11, max y=horizonY-0.11H. Good.

Let me reduce step for smoother? keep as is.

Now stripes: in buildSun, stripes from y=cx+sunR*0.02. Let me make first band a bit larger and visible.

Let me verify stripes visible: sunCY=horizonY-0.45R. cx (canvas center of sun image) corresponds to sunCY on screen. Stripes in canvas from cx+0.02R. On screen that's sunCY+0.02R = horizonY-0.43R. With R=302 (H1080): horizonY=670, =670-130=540. Mountains max reach horizonY-0.11H=670-119=551. So stripes from 540 down; mountains reach 551; so top 11px behind mountains, stripes visible 551-670 above horizon =119px clearly striped, plus below horizon cut by grid. Wait below horizon the grid covers it. Grid drawn from horizonY down. So stripes below 670 hidden by grid. So visible striped band = 551..670 = 119px. 

But wait, is the sun's solid top visible above? Top of sun at sunCY-R=670-0.45R-R=670-1.45R=670-438=232. So solid top from 232 to ~540 (start stripes). That's a big solid disc region from 232 to 540 = 308px, above mountains (551). Wait mountains reach 551, and sun top region is 232-540 which is above 551, so fully visible solid. Then stripes 540-670 partly behind mountains(551). Good, stripes clearly visible in a band. 

Hmm but the classic look is the stripes are the "cut out" showing sky. Since we draw sun in front of mountains and grid, the striped (transparent) parts would show the sky behind = sky gradient. That's the classic look. And the mountains/grid don't overlap much now. 

Let me make sure the stripe region is tall enough to read as "stripes" not just a sliver. 119px band with increasing spacing: bands ~2,3,4,6,8,11,15... that gives maybe 6-7 stripes in 119px. Reasonable. Let me increase the band/gap growth so fewer, more distinct stripes. Actually classic has ~6-8 stripes in the lower half. Good.

Let me maybe make the whole sun a bit smaller so it doesn't dominate: R=0.26*min(W,H). Then sunCY=horizonY-0.45R. With R=281: top=670-1.45*281=670-407=263, stripes start 670-0.43*281=670-121=549, visible stripes 551-670. Solid top 263-549=286px. Fine. I'll use 0.27.

Actually let me just keep 0.28 and move on.

Let me now also make the title sun rise to the same playing position. In drawTitle I had sunY from below to horizonY-sunR*0.35. Change to horizonY-sunR*0.45. And it's drawn before mountains there (drawSun then mountains) — good, same order as playing.

Wait in playing I draw sun then mountains then grid. In title I draw sun, mountains, grid. Same. Good, stripes visible in both.

Now let me write code. I'll integrate everything.

Let me define the campaign/sector handling functions:

function startRun(hard){
  initAudio(); resume;
  hardMode=hard;
  resetGame(); // clears entities, sets player base
  applyUpgradesReset();
  runTime=0; maxCombo=0; shotsFired=0; shotsHit=0;
  state='intro'; introT=0; introLine=0;
}

resetGame (existing) sets player, waves, etc. I'll extend to reset sector stuff.

applyUpgradesReset: player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1}; player.overdrive=0;

enterSector(sec):
  currentSector=sec; setSectorPalette(sec);
  waveInSector=1;
  state='sector'; sectorCardT=0; sectorCardDur=2.6;
  (don't start waves yet)

After sector card ends -> beginWaveSequence: waveInSector=1; waveState='inter'; waveDelay=1.5; state='playing'.

Actually I can just set state='playing' with waveState='inter' at end of sector card. And waveInSector=1.

beginWave():
  const sec=sectors[currentSector];
  if(waveInSector===5){ // boss
    spawnBoss(sec); waveState='boss';
    waveMsg=sec.boss.name; waveMsgT=2.5; taunt=sec.boss.taunt; tauntT=3;
  } else {
    spawn normal wave using sec.enemyMix and count = base + waveInSector + sector.
    waveState='spawning';
  }

On wave clear (spawning empty && enemies empty):
  waveInSector++;
  waveState='inter'; waveDelay=2.0;

On boss death (in updateBoss dying complete):
  if(currentSector===2){ victory(); }
  else { state='upgrade'; showUpgradeCards(); }

Let me handle victory: state='victory'; compute stats; musicOn=false; big fx.

Let me handle upgrade pick: apply chosen, then enterSector(currentSector+1).

Now boss spawn:
function spawnBoss(sec){
  const diff=hardMode?1.6:1;
  const hp=(35+currentSector*30)*diff + 20;
  boss={id:currentSector, name:sec.boss.name, taunt:sec.boss.taunt, x:W/2,y:-180,ty:H*(0.18+currentSector*0.02), hp:Math.round(hp), max:Math.round(hp), t:0, fireCd:2, phase:0, dying:0,dieT:0,dieBoom:0, spiralA:0,spiralCd:0, finale:sec.boss.finale};
}

Boss patterns in updateBoss by boss.id.

Let me write updateBoss patterns:

General movement: boss.y ease to ty; boss.x = W/2 + sin(t*speed)*range. speed/range per id.
For finale maybe more erratic.

Phase based on hp fraction: >0.66 phase0, >0.33 phase1, else phase2.

Attacks:
Boss id 0 (GLITCHWING, magenta):
 p0: aimed 5-bolt spread every 1.4s
 p1: rotating fan: 12 bullets in a fan rotating, every 0.9s; also aimed single
 p2: ring of 20 + aimed 5 spread
Boss id 1 (CANYON WARDEN, cyan):
 p0: two side streams: every 0.5s fire from left and right edges aimed-ish; simpler: fire 2 bolts downward-left and downward-right
 p1: spiral (2 arms) every 0.06
 p2: spiral + aimed 3 spread + occasional ring
Boss id 2 (THE STATIC, finale):
 p0: noise burst: every 0.8s fire 16 random-direction bullets
 p1: scanline: horizontal row of bullets sweeping + aimed 3
 p2: everything: spiral + ring + aimed + noise, faster

I'll write helper fireBolt(x,y,vx,vy,c,r).

Let me keep bullet speeds moderate.

Now taunt: show a line under boss name when tauntT>0.

Let me now also make sure hitPlayer and enemies work with new enemies lifetime.

Enemy lifetime: in spawnEnemy set e.diveAt = (type==='shooter') ? (7+Math.random()*6) : Infinity; Actually only shooters hover; weavers/divers already move off screen. But divers aim at player and accelerate, they'll go off bottom. Weavers go straight down, off bottom. So only shooters need diving. But to be safe, also give a global e.maxLife; if t>maxLife, force removal or dive. Let me just handle shooters: if e.t>e.diveAt, set e.dive=true and treat like diver (accelerate toward player). That guarantees they leave.

Also, to be extra safe against any enemy that might stall (e.g., a weaver whose baseX off-screen? no). I'll add a global: if e.t>25, remove. Just in case.

Let me also ensure divers/weavers always go off bottom: their y increases, so eventually y>H*0.9 -> removed. Good.

Now let me also make sure enemy bullets cleanup when player dies etc. Already hitPlayer clears nearby bullets.

Now the Overdrive unleash:
function unleashOverdrive(){
  if(player.overdrive<1||state!=='playing')return;
  player.overdrive=0;
  // clear enemies
  for each enemy: kill without full combo? Award points, boom.
  eBullets.length=0;
  if(boss&&boss.dying===0) boss.hp-=boss.max*0.3 (big chunk), fx;
  big fx: flash=1, whiteFlash=0.6, shake=40, hitStop=0.12, bigBoom center? Let me do a big ring from player.
  sfxBoom(true);
  Actually clearing all enemies: loop and for each add points + boom.
}

Let me make it: overdrive clears enemies (award half points each to avoid inflating too much? just award normal). And damages boss 30%.

Let me write it.

Now stats accuracy = shotsHit/shotsFired (guard div0). Time formatted mm:ss.

Now the victory buttons hit test. I'll compute button rects in drawVictory and store in a global victoryButtons=[{label,x,y,w,h,action}]. On mousedown/touch, if state==='victory', check click. Also keyboard? space/enter -> play again. 1 -> play again, 2 -> hard. Let me support both.

Actually simpler: on click anywhere in victory -> if click in hard button -> hard, else -> play again? But ambiguous. Let me do explicit buttons with hit test; also keys: R=play again, H=hard. And space/enter=play again.

Let me store victoryButtons and check on pointer.

Now the upgrade cards: store upgradeCards=[{label,desc,color,apply}] (3). Draw 3 boxes. On click/key 1-3 -> pick.

Let me now write the full file. Given size, I'll be thorough but compact.

Let me define palette and sector data precisely.

sectors = [
{
 name:'SUNSET BOULEVARD', sub:'The last sunset. Hold the light.',
 pal:{ skyTop:'#04000e',skyMid:'#1c043a',skyHor:'#5a0c6e',
   sun:['#ffe14d','#ff9500','#ff3080','#e000a0'],
   grid:'255,45,149', gridV:'rgba(0,229,255,0.16)', horizon:'#ffd319',
   mtnBack:'rgba(255,45,149,0.55)', mtnBackFill:'#1a0b2e',
   mtnFront:'rgba(0,229,255,0.55)', mtnFrontFill:'#0d0518' },
 mix:{weaver:0.5,diver:0.3,shooter:0.2},
 boss:{name:'GLITCHWING', taunt:'"You are just a flicker."' , color:'#ff2d95'}
},
{
 name:'CHROME CANYON', sub:'Steel canyons. Fast and cold.',
 pal:{ skyTop:'#000a10',skyMid:'#00203a',skyHor:'#00506a',
   sun:['#d0fff5','#5ff0ff','#00b0ff','#0050ff'],
   grid:'0,229,255', gridV:'rgba(118,185,0,0.16)', horizon:'#a0fff0',
   mtnBack:'rgba(0,229,255,0.5)', mtnBackFill:'#031a24',
   mtnFront:'rgba(118,185,0,0.5)', mtnFrontFill:'#02141a' },
 mix:{weaver:0.3,diver:0.45,shooter:0.25},
 boss:{name:'CANYON WARDEN', taunt:'"This canyon is mine."', color:'#00e5ff'}
},
{
 name:'THE CORE', sub:'The heart of the signal. End this.',
 pal:{ skyTop:'#0a0004',skyMid:'#300418',skyHor:'#6e0a2e',
   sun:['#fff2a0','#ff6a20','#ff2020','#7a0000'],
   grid:'255,138,0', gridV:'rgba(255,45,149,0.16)', horizon:'#ff5020',
   mtnBack:'rgba(255,138,0,0.5)', mtnBackFill:'#1a0308',
   mtnFront:'rgba(255,45,149,0.5)', mtnFrontFill:'#120208' },
 mix:{weaver:0.34,diver:0.33,shooter:0.33},
 boss:{name:'THE STATIC', taunt:'"I am the noise between your stars."', color:'#ff8a00', finale:true}
}
];

Note: grid is an "r,g,b" string used in rgba templates. Let me use pal.grid as "255,45,149" and build rgba(grid, a). gridV and horizon separate.

Sun color for glow: use pal.sun[2].

Now buildSun(stops) - I'll pass pal.sun.

Let me write drawSky:
 g stops: skyTop, skyMid at 0.5, skyHor at 1.

drawGrid horizontal line color: 'rgba('+pal.grid+','+a+')', vertical pal.gridV, horizon pal.horizon with shadow.

drawMtn: I'll pass line color and fill.

Let me set current sector palette `pal = sectors[0].pal` initially.

On setSectorPalette(i): pal=sectors[i].pal; buildSun();

buildSun uses pal.sun.

Now for the intro, let me write typewriter.

introLines=[
 'The Static is a corrupting signal —',
 'a living glitch eating the Neon Grid.',
 'It devours the light, district by district.',
 'The Grid is dark. Everyone is gone.',
 'Except you. SPARK. The last light-runner.'
];
That's 5 lines; spec says 3-4. Let me do 4:
[
 'The Static is a corrupting signal — a living glitch',
 'eating the Neon Grid, district by district.',
 'The Grid is dark. Everyone is gone.',
 'Except you.  SPARK — the last light-runner.'
]
Typewriter: reveal total chars over time. Show all lines up to current char count. Click to skip.

Implementation: introT increments. chars = floor(introT * cps). Determine which line/char. Build display by iterating lines, subtract.

Let me do: total revealed = floor(introT*28). Build string line by line.

Draw centered, monospace, with a blinking cursor at end.

Now let me also handle: during intro, still render the background (sky/sun/grid) for beauty. I'll render the playing-style background (sun above mountains, grid) with sector 0 palette, plus intro text overlay. Good.

Let me make a helper drawBackground() that draws sky, stars, sun, mountains, grid using pal and current sunY (for playing/title). For playing use sunCY. For title use animating. For intro use sunCY (static). I'll param.

Actually to keep code simpler, I'll inline.

Let me now also keep title screen as before (animated logo etc.), but now "CLICK OR TAP TO START" leads to intro (startRun). And I could add "HARD MODE" hint? The spec says hard mode button on victory. Title just start.

Let me finalize input handling:
- pointerdown: initAudio; if title->startRun(false); if intro->skip to sector card; if playing-> (mouse move handles); if upgrade->pick card by pos; if gameover->startRun(false); if victory->buttons; if sector->skip (advance to playing).
- Also space: during playing -> unleash overdrive; during intro/sector skip; during gameover/victory -> play again.

Let me define a central onPointer(x,y).

Keys:
 space/enter: 
   playing -> overdrive
   intro -> skip
   sector -> skip
   gameover -> restart
   victory -> play again
   title -> start
 1/2/3: upgrade pick; victory 1=again 2=hard
 p: pause (playing only)
 m: mute
 arrows/wasd: move

Now let me write everything.

Let me be careful with updateBullets hitting boss: I have boss check there; keep. Also need shotsHit increment there. And on boss hp<=0 set dying.

Also overdrive damaging boss: set hp and if <=0 dying.

Let me write killEnemy to also add overdrive and maxCombo tracking.

Let me now also ensure combo increments on enemy kill (existing) — keep. maxCombo=max.

Let me write it all now.

One concern: file length. I'll write it fully.

Let me also double check the "sector title card" rendering: big name, subtitle, "SECTOR n/3", fade in/out. Auto after dur. Skippable by click.

Let me set sectorCardT and in frame if state==='sector': sectorCardT+=rdt; if >=dur -> beginPlayingSector(). Skippable on pointer/key.

beginPlayingSector(): state='playing'; waveInSector=1; waveState='inter'; waveDelay=1.4; enemies etc already empty (reset at enterSector? not cleared). Let me clear eBullets/pBullets/particles at enterSector for a clean start of sector. Actually after a boss death, entities are mostly cleared. Let me clear eBullets and remaining enemies at enterSector.

Let me in enterSector: enemies.length=0; eBullets.length=0; pBullets.length=0; powerups keep? clear too. Keep particles for continuity? clear to be clean.

Now victory: keep the last explosion visible? state='victory' overlays. Fine.

Let me write.

For accuracy tracking, shotsFired++ per bolt in updatePlayer. shotsHit++ in updateBullets on hit.

Let me also add runTime += dt in playing.

Let me now produce final code.

For overdrive HUD bar: bottom center, acid green. Show "OVERDRIVE READY [SPACE]" when full with pulse.

Let me place overdrive bar at bottom center: width min(W*0.4,340), at y=H-34.

Let me also show sector name small in HUD top-center? Maybe just wave indicator: "SECTOR 2 · WAVE 3" or "SECTOR 2 · BOSS". Let me show top center: currentSector+1 and wave.

Let me add to drawHUD: top center text "SECTOR {n} / 3" and below "WAVE {waveInSector} or BOSS".

Now let me write drawVictory with stats and two buttons.

Stats:
 FINAL SCORE, BEST, MAX COMBO, ACCURACY %, TIME.

Buttons: PLAY AGAIN (restart normal), HARD MODE (restart hard).

Let me store victoryButtons each frame for hit test.

Let me write.

Edge: On victory, hardMode might be true; "play again" should restart normal (false) or same? Let me make "PLAY AGAIN" restart with same difficulty? Ambiguous. Let me: "PLAY AGAIN" -> normal run (false) but if already hard, maybe keep? I'll make PLAY AGAIN restart the same mode, and there's also a "HARD MODE" that switches to hard. Hmm but if already in hard, PLAY AGAIN = hard again. And a separate button to go easy? Let me keep simple:
 - Button A: "PLAY AGAIN" -> startRun(hardMode) (same mode)
 - Button B: hardMode? "EASY MODE" : "HARD MODE" -> startRun(!hardMode)
That's clean: always offer the toggle.

Good.

Now let me finalize and write the code carefully.

Let me also keep the "P pause / M mute" and show in intro/hud.

Let me write the enemy update for shooter dive:
 if type shooter:
   if !e.dive:
     hover toward ty, drift; fire; if e.t>e.diveAt -> e.dive=true
   if e.dive: behave like diver (accelerate toward player, y increases)
Actually once dive, just set it to diver behavior. Let me implement: if(e.dive){ e.y+=e.sp*dt; e.sp+=120*dt; e.x+=(player.x-e.x)*min(1,dt*3);} but shooter.sp initial? set sp on dive to 160.

Let me set in spawnEnemy for shooter: e.dive=false; e.diveAt=7+Math.random()*6; e.sp=160.

Global safety: if e.t>30 -> remove.

Now let me write.

I need to be careful: updateWaves uses waveState inter/spawning/boss and boss. Let me rewrite updateWaves:

function updateWaves(dt){
 if(boss){ updateBoss(dt); return; }
 if(waveState==='inter'){
   waveDelay-=dt;
   if(waveDelay<=0) beginWave();
   return;
 }
 if(waveState==='spawning'){
   for spawnQueue...
   if(spawnQueue.length===0 && enemies.length===0){
     waveInSector++;
     waveState='inter'; waveDelay=2.0;
   }
 }
}

beginWave():
 const sec=sectors[currentSector];
 if(waveInSector>=5){ spawnBoss(sec); waveState='boss'; waveMsg=sec.boss.name; waveMsgT=2.6; taunt=sec.boss.taunt; tauntT=3.2; }
 else {
   const diff=hardMode?1.6:1;
   const count=Math.round((6+currentSector*3+waveInSector*2)*diff);
   spawnQueue.length=0;
   for i<count: type=rollMix(sec.mix); spawnQueue.push({t:i*0.45+rand*0.25,type});
   waveState='spawning';
   waveMsg='WAVE '+waveInSector; waveMsgT=1.6;
 }

rollMix(mix): r=Math.random(); if r<mix.weaver weaver; else if r<mix.weaver+mix.diver diver; else shooter.

On boss death in updateBoss:
 if currentSector===2 -> victory()
 else -> { state='upgrade'; buildUpgradeCards(); }

Let me ensure waveInSector reset handled by enterSector.

Now, the first sector start: startRun -> intro -> (skip) -> enterSector(0) -> sector card -> beginPlayingSector (waveInSector=1, waveState inter) -> beginWave wave1.

Let me code frame state machine:

if state==='title': titleT+=rdt;
else if state==='intro': introT+=rdt;
else if state==='sector': sectorCardT+=rdt; if>=dur beginPlayingSector();
else if state==='playing': runTime+=dt; update stuff (if not paused);
else if state==='upgrade': (wait for input) updateFx small;
else if state==='gameover': goT+=rdt; updateFx;
else if state==='victory': vicT+=rdt; updateFx;

For upgrade state, I still want background animating (grid scroll) — gridScroll always updates. And I render playing background + enemies frozen? Let me render the playing scene (background + remaining particles) but no enemies (cleared). I'll render drawBackground + particles + fx, and overlay upgrade cards. Let me keep enemies empty at that point (boss cleared). Fine.

Actually after boss death, enemies list may still have a few (non-boss) if it was a boss wave there are no other enemies. So empty. Good.

Let me render for upgrade: sky/stars/sun/mtn/grid + particles + shocks + popups + overlay cards. I'll just call the same scene render as playing but skip player/HUD. Simpler: I'll have a function renderScene() that draws background+entities+fx, then per-state overlays.

Let me structure render:
 function render(){
   ctx.save(); shake translate;
   if(state==='title') drawTitle();
   else {
     drawBackground();
     if(state!=='upgrade'&&state!=='victory') drawEntities();
     drawFx();
     if(state==='playing'||state==='gameover') drawPopups();
     ctx.restore(); // un-shake for overlays? Actually keep shake for scene, restore for UI.
     // UI overlays without shake:
     if(state==='playing'){ drawWaveMsg(); drawHUD(); if paused drawPause(); }
     if(state==='intro') drawIntro();
     if(state==='sector') drawSectorCard();
     if(state==='upgrade') drawUpgrade();
     if(state==='gameover') drawGameOver();
     if(state==='victory') drawVictory();
   }
   drawOverlays();
 }
Wait I ctx.restore() then draw overlays outside save. Let me restructure: 
 ctx.save(); if(shake) translate;
   draw scene (bg/entities/fx/popups) OR title;
 ctx.restore();
 then overlays (UI) drawn in screen space (no shake) — but waveMsg/pause etc should be fine unshaken. Actually waveMsg shaking is fine either way. Let me keep UI unshaken for readability.

Let me just do:
 function render(){
   ctx.save();
   if(shake>0) ctx.translate(rand,rand);
   if(state==='title') drawTitle();
   else { drawBackground(); if(state==='playing'||state==='gameover') drawEntities(); drawFx(); if(state==='playing'||state==='gameover') drawPopups(); }
   ctx.restore();
   // UI (no shake)
   if(state==='playing'){ drawWaveMsg(); drawHUD(); if(paused)drawPause(); }
   else if(state==='intro') drawIntro();
   else if(state==='sector') drawSectorCard();
   else if(state==='upgrade') drawUpgrade();
   else if(state==='gameover') drawGameOver();
   else if(state==='victory') drawVictory();
   drawOverlays();
 }

Good. drawBackground handles sun position based on state: playing/gameover/upgrade/sector/victory/intro use sunCY (static). title uses animation (drawTitle handles its own). Actually drawBackground for non-title states: sun at sunCY. Let me make drawBackground use sunCY always (for non-title). Fine.

But during intro I want the sun visible and grid scrolling — drawBackground covers it. Good.

Now the intro/sector/upgrade/victory/gameover all render on top of the live-ish background. For upgrade/victory I clear entities so only background+particles. Good, particles from boss explosion linger — nice.

Let me make sure when entering upgrade/victory I don't keep player drawn (state!=='playing' so drawEntities not called, but player is only drawn inside drawEntities which also draws enemies/bullets/powerups. For upgrade I skip drawEntities so no player. Good, but I might want to show player idle? Not necessary.

Now, overdrive meter in HUD.

Let me write drawHUD to include overdrive bar and sector/wave info.

Let me now also ensure the "P pause" only during playing; and while paused we still render (frame keeps rendering, dt frozen). In frame, if state==='playing'&&!paused do updates. Rendering always. Good.

Let me finalize enemy dive and safety.

Let me write the code now fully.

I'll write carefully.

For drawVictory buttons, compute:
 btnW=Math.min(W*0.32,260), btnH=54, gap=24;
 center them. Two buttons side by side if fit, else stacked. Let me stack centered for safety (mobile). 
 y positions: y1=H*0.72, y2=H*0.72+70.
 store rects.

Buttons text:
 b1: 'PLAY AGAIN'
 b2: hardMode?'EASY MODE':'HARD MODE'

On click: if in b1 -> startRun(hardMode); if in b2 -> startRun(!hardMode).
Keys: space/enter/r -> startRun(hardMode); h -> startRun(!hardMode).

For upgrade cards: 3 cards side by side (or stacked if narrow). Let me do side by side with wrap. Simpler: 3 columns centered, each card width = min((W-60)/3, 240), height=150. If W small (<720) stack. Let me just do 3 across with small min width; on mobile they'll be narrow but readable-ish. I'll compute cardW=Math.min(240,(W-40)/3). positions centered.

Cards store rects for click. Keys 1-3.

Let me define buildUpgradeCards(): pick 3 distinct from pool.
 pool:
 {label:'RAPID FIRE', desc:'-20% fire cooldown', color:'#00e5ff', apply:u=>{u.fireRate=Math.max(0.5,u.fireRate*0.8);}}
 {label:'TWIN CANNON', desc:'+1 laser bolt', color:'#ff2d95', apply:u=>{u.twin=Math.min(3,u.twin+1);}}
 {label:'+1 HULL', desc:'+1 life', color:'#76B900', apply:u=>{player.lives++;}}
 {label:'AEGIS FIELD', desc:'Shields last 60% longer', color:'#00b0ff', apply:u=>{u.shieldDur*=1.5;}}
 {label:'MAGNET CORE', desc:'Pull power-ups to you', color:'#ffe14d', apply:u=>{u.magnet=u.magnet+1;}}
 {label:'OVERDRIVE CELL', desc:'Overdrive charges faster', color:'#ff8a00', apply:u=>{u.odGain*=1.4;}}
Pick 3 random distinct.

player.upg = {twin:0, fireRate:1, shieldDur:1, magnet:0, odGain:1}.

Magnet: in updatePowerups, if upg.magnet>0, radius = 120+magnet*120; attract powerups within radius toward player.

Shield apply: when powerup shield picked: player.shield=8*upg.shieldDur.

Overdrive gain: on kill overdrive += (0.05+combo*0.004)*odGain, clamp1.

Fire: fireCd = (spread?0.18:0.22)*upg.fireRate.

Bullets: n=1+upg.twin; angles=(i-(n-1)/2)*0.12; plus if spread add -0.3,0,0.3.

Let me write updatePlayer firing:
 if(player.fireCd<=0){
   player.fireCd=(player.spread>0?0.16:0.22)*upg.fireRate;
   sfxLaser();
   const n=1+upg.twin;
   for(let i=0;i<n;i++){const a=(i-(n-1)/2)*0.13; pBullets.push({x:player.x+a*10,y:player.y-16,vx:Math.sin(a)*660,vy:-Math.cos(a)*660,r:3.5,c:'#00e5ff'}); shotsFired++;}
   if(player.spread>0){for(const a of [-0.3,0,0.3]){pBullets.push({x:player.x,y:player.y-16,vx:Math.sin(a)*660,vy:-Math.cos(a)*660,r:3.5,c:'#76B900'}); shotsFired++;}}
 }
Overdrive color accent for spread bolts acid green.

Now overdrive unleash:
 function unleashOverdrive(){
  if(state!=='playing'||player.overdrive<1||paused)return;
  player.overdrive=0;
  flash=1;whiteFlash=0.7;shake=42;hitStop=0.14;
  bigBoom(W/2,H*0.5);
  // shock ring from player
  shocks.push({x:player.x,y:player.y,r:20,v:2400,life:0.6,max:0.6,c:'#76B900'});
  sfxBoom(true);
  for(let i=enemies.length-1;i>=0;i--){const e=enemies[i];boom(e.x,e.y,'#76B900',16,0.7);const pts=(e.type==='weaver'?100:e.type==='diver'?150:200)*mult();score+=pts;enemies.splice(i,1);}
  eBullets.length=0;
  if(boss&&boss.dying===0){boss.hp-=Math.round(boss.max*0.30);boom(boss.x,boss.y,'#76B900',30,1);if(boss.hp<=0){boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;}}
 }

Good.

Now the finale boss (Static) should feel like a finale: maybe on death, big whiteout + special victory. Victory triggers after currentSector===2 boss death. Fine.

Let me also make the Static boss visually distinct: a large glitch orb with noise. I'll draw it with many small random rects (static) inside a circle, pulsing, plus the health core.

Let me write drawBoss with switch:
 id0: winged (glitch wing) magenta — a wide shape with wings.
 id1: hexagon chrome cyan — hexagon with inner core.
 id2: static orb — big circle filled with static noise + jagged.

Let me implement.

For id0 wings: draw central diamond + two side triangles that flap (rotate by sin).
 id1: hexagon + rotating inner hexagon.
 id2: circle radius Rb, fill dark, overlay ~60 random acid/orange pixels each frame (static), plus a glitchy face (two eyes).

Let me code.

Now let me also ensure boss bullets have colors.

Alright, let me also add: taunt display under boss name in drawWaveMsg or separate. I'll show taunt when tauntT>0 as a line.

Let me write drawWaveMsg to also show taunt if tauntT>0.

Now let me write the entire file.

Let me also double-check the sun stripes: I'll change buildSun stripes loop start and ensure visible. Let me set:
 let y=cx+sunR*0.03, band=Math.max(2,sunR*0.02), gap=sunR*0.035;
 while(y<cx+sunR){ fillRect(0,y,size,band); y+=band+gap; band*=1.5; gap*=1.35; }
This gives ~ a handful of stripes. Good.

Now, one more: the sun must be clearly striped "above the mountains". With our geometry the striped band is above horizon and above mountain line. Good.

Let me also make sure in drawBackground the sun is drawn BEFORE mountains and grid (so they can occlude, but they won't much). Order: sky, stars, sun, mtnBack, mtnFront, grid. Yes.

Let me write.

Also I realize during 'upgrade' and 'victory' I still call drawBackground which uses sunCY. Good.

Let me also keep gridScroll updating always (in frame top). Yes.

Let me now also handle the case where the player is not drawn during upgrade/victory (fine) but during 'sector' and 'intro' also not drawn (fine, background only).

Now, mousemove sets player.tx only when playing. Good.

Let me write pointer handler:
 function onPointer(x,y){
  if(state==='title'&&titleT>1){startRun(false);return;}
  if(state==='intro'){introT=999;return;} // skip -> but need to advance; handle in frame when introT>=total? Let me instead directly advance: enterSector(0). But we might be mid? just call go to sector. I'll set a flag skipIntro=true and in frame handle. Simpler: directly enterSector(0). But we haven't set runTime etc? startRun already did. So enterSector(0). Good.
  Actually let me handle intro skip: if(state==='intro'){enterSector(0);return;}
  if(state==='sector'){sectorCardT=sectorCardDur;return;} // will auto-advance next frame
  if(state==='upgrade'){ pickCardAt(x,y); return;}
  if(state==='gameover'&&goT>0.6){startRun(false);return;}
  if(state==='victory'){ victoryClick(x,y); return;}
  if(state==='playing'){ /* nothing extra; mousemove handles */ }
 }
Wait intro skip to enterSector(0) — but intro is only for first run. Good. Also if user clicks repeatedly during intro it's fine.

But careful: after intro we go to sector card for sector 0. Good.

Also I should allow intro to auto-advance when all lines typed + pause. Let me auto-advance after typing done + 1.2s. Compute totalChars; if introT*28>=totalChars and introT> (totalChars/28 + 1.0) -> enterSector(0). Let me implement in frame.

Let me compute totalIntroChars once.

Now let me write pickCardAt: iterate upgradeCards rects, if contains -> chooseCard(i).
chooseCard(i): upgradeCards[i].apply(player.upg); player.overdrive=Math.min(1,player.overdrive+0.15) (reward); sfxPower(); enterSector(currentSector+1).

But +1 life card uses player.lives. Fine.

Now victoryClick(x,y): iterate victoryButtons; if contains -> its action.

Let me store victoryButtons global; set each frame in drawVictory (or compute once). I'll compute in a function victoryBtns() returning rects based on current W/H, use both for draw and click.

Let me define:
 function victoryBtnRects(){
  const w=Math.min(W*0.5,300),h=52;
  const x=(W-w)/2;
  return [
   {x,y:H*0.72-h/2,w,h,label: 'PLAY AGAIN', act:()=>startRun(hardMode)},
   {x,y:H*0.80-h/2,w,h,label: hardMode?'EASY MODE':'HARD MODE', act:()=>startRun(!hardMode)}
  ];
 }
Use in draw and click.

Now let me finalize and write the whole file. This is long; let me be meticulous.

Let me write drawIntro:
 const lines=introLines;
 const cps=26;
 let shown=Math.floor(introT*cps);
 let y=H*0.4;
 ctx.font='18px monospace'; textAlign left? Let me center each line but typewriter left-to-right. I'll compute per line the substring.
 I'll draw centered using measureText for full line to get x start. Simpler: textAlign='center' but reveal by clipping? Let me do: for each line, full=lines[i]; count chars from shown; visible=full.slice(0, n) where n is remaining. Compute remaining across lines.
 Actually to center while typing, I'll draw the visible substring centered — but that shifts as it types. Slight shift is okay but looks odd. Let me left-align within a centered block: compute block width = max line width; x0=W/2-blockW/2. Draw each line from x0 left aligned, revealing chars.
 Let me do that.
 cursor blink at end of current typing position.

Let me implement:
 const lineH=28;
 const maxW = ctx.measureText(lines.reduce((a,b)=>a,lines[0]))... I'll compute width of each full line, take max.
 x0=W/2-maxW/2;
 let remaining=shown;
 for i: line=lines[i]; take=line.length; if(remaining>=take){draw full line; remaining-=take;} else {draw slice(0,remaining); cursor here; remaining=0; }
 if remaining still>0 after all lines, cursor at end of last.

I'll draw with fillStyle '#cfe8ff', shadow cyan. Add a small header "TRANSMISSION // SPARK" above.

Good.

Let me now write drawSectorCard:
 a = fade in/out based on sectorCardT/dur.
 name big, "SECTOR n / 3", sub.
 color = pal.grid? use a bright accent per sector: use sectors[i].boss.color or a fixed. Let me use sectors[i].accent. Add accent field.

Add accent to each sector: 0:'#ff2d95',1:'#00e5ff',2:'#ff8a00'.

drawSectorCard uses accent.

Now drawUpgrade: title "CHOOSE AN UPGRADE", 3 cards with label/desc/color, number badge 1/2/3.

Let me write.

Now let me also show overdrive hint text near bar.

Alright, writing final code. Let me be careful to define all variables at top.

Let me also keep 'best' load.

Let me also keep flash/whiteFlash/chromatic.

Let me now also make sure when state transitions to upgrade/victory we set musicOn appropriately: victory -> musicOn=false. upgrade -> keep music? Let me keep music playing during upgrade (nice). Actually pause action but music continues — fine, keep musicOn true. gameover -> musicOn false.

Let me ensure music starts after first click: initAudio in onPointer; startRun sets musicOn=true. But during intro/sector/upgrade we want music too. So set musicOn=true in startRun, and only false on gameover/victory. Good.

But AC must be created (first click). onPointer calls initAudio() first. startRun also calls initAudio. Good.

Now, the very first user interaction is the title click -> onPointer -> initAudio + startRun -> musicOn true -> music schedules. Good.

Let me write.

I think I have a full plan. Let me write the code.

Let me also handle window blur -> pause? Optional. I'll add: on visibilitychange if playing -> paused=true. Nice touch.

Let me write final.

Regarding the enemy bullet colors and boss bullet helper:
 function fb(x,y,vx,vy,c,r){eBullets.push({x,y,vx,vy,r:r||5,c});}

Boss patterns (in updateBoss after movement, if dying skip):
 const frac=boss.hp/boss.max;
 boss.phase = frac>0.66?0:(frac>0.33?1:2);
 switch(boss.id){
  case 0: // GLITCHWING
   boss.x=W/2+Math.sin(boss.t*0.5)*W*0.22;
   if(boss.phase===0){boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+20,5,0.22,220,'#ff2d95');boss.fireCd=1.4;}}
   else if(boss.phase===1){boss.fireCd-=dt;if(boss.fireCd<=0){for(k=0;k<12;k++){const a=-Math.PI/2 + (k-5.5)/5.5*Math.PI*0.5 + Math.sin(boss.t)*0.3; fb(boss.x,boss.y,Math.cos(a)*190,Math.sin(a)*190,'#ff2d95');}boss.fireCd=0.85;} aimedSpread every 2.0}
   else {ring 20 + aimedSpread 5}
  case 1: // CANYON WARDEN
   boss.x=W/2+Math.sin(boss.t*0.4)*W*0.26;
   phase0: side streams: every 0.55 fire two bolts from edges? Let me do: fb from boss to lower-left and lower-right:
     const a1=Math.PI*0.7, a2=Math.PI*0.3; fb(boss.x,boss.y,Math.cos(a1)*210,Math.sin(a1)*210,'#00e5ff'); fb(...a2...); fireCd 0.55
   phase1: spiral 2 arms 0.06
   phase2: spiral + aimed 3 + ring occasionally
  case 2: // STATIC
   boss.x=W/2+Math.sin(boss.t*0.6)*W*0.2 + Math.sin(boss.t*1.7)*40;
   phase0: noise burst 16 random every 0.8
   phase1: scanline: every 0.5 fire a horizontal row? plus aimed 3
   phase2: spiral + ring + aimed + noise, faster
 }

Let me define aimedSpread(x,y,n,spread,speed,c): base angle to player; for k in -(n-1)/2..(n-1)/2 fb at angle+ k*spread.
 function aimedSpread(x,y,n,spread,speed,c){const base=Math.atan2(player.y-y,player.x-x);for(let k=-(n-1)/2;k<=(n-1)/2;k++)fb(x,y,Math.cos(base+k*spread)*speed,Math.sin(base+k*spread)*speed,c,5);}
For odd n, (n-1)/2 integer. n=5 -> -2..2 good.

ring(x,y,n,speed,c,off=0): for k fb at off+k/n*2PI.

spiral handled inline.

Let me now write boss death sequence: when boss.dying: dieT+=dt; dieBoom timer spawns random booms; after 1.4s bigBoom + award points + powerups + boss=null + next step.

I'll reuse existing but add per-sector: on finale, bigger.

Let me now also ensure the boss hp bar shows name.

Alright, writing the final file now. Let me assemble.

I'll write it out. Given the constraints, I'll produce the complete HTML.

Let me make sure to not exceed reason but it's fine.

Let me write drawBackground():
 function drawBackground(){
  drawSky();drawStars();
  drawSun(sunCY,1);
  drawMtn(mtnBack, pal.mtnBack, pal.mtnBackFill, Math.sin(time*0.04)*10, 1);
  drawMtn(mtnFront, pal.mtnFront, pal.mtnFrontFill, Math.sin(time*0.06+2)*14, 1);
  drawGrid(1);
 }
But title uses its own. drawTitle calls drawSun/mtn/grid with its alphas. I'll keep drawTitle separate and it uses pal too (sector 0 palette). Fine.

Now drawSky uses pal.
 function drawSky(){const g=ctx.createLinearGradient(0,0,0,horizonY);g.addColorStop(0,pal.skyTop);g.addColorStop(0.5,pal.skyMid);g.addColorStop(1,pal.skyHor);ctx.fillStyle=g;ctx.fillRect(0,0,W,horizonY+2);}

drawSun(y,alpha): glow uses pal.sun colors. Let me build glow gradient using pal.sun[1] and pal.sun[2].
 const gl=ctx.createRadialGradient(sx,y,sunR*0.2,sx,y,sunR*2);
 gl.addColorStop(0, hexA(pal.sun[2],0.3)) ... I'll just use rgba fixed-ish per palette. Simpler: use pal.sun[2] with alpha via converting hex. Let me write hexToRgba(hex,a).
 Let me add helper.
 gl stops: 0 -> rgba(sun[2],0.35), 0.5 -> rgba(sun[1],0.12), 1 -> rgba(sun[2],0).

buildSun: use pal.sun array (4 stops) for the disc gradient.

Let me write buildSun():
 const g=s.createLinearGradient(0,cx-sunR,0,cx+sunR);
 g.addColorStop(0,pal.sun[0]);g.addColorStop(0.35,pal.sun[1]);g.addColorStop(0.7,pal.sun[2]);g.addColorStop(1,pal.sun[3]);
 ...
 stripes as before.

Good.

hexToRgba:
 function hexA(hex,a){const h=hex.replace('#','');const r=parseInt(h.substr(0,2),16),g=parseInt(h.substr(2,2),16),b=parseInt(h.substr(4,2),16);return `rgba(${r},${g},${b},${a})`;}

Now grid uses pal.grid (r,g,b string).
 vertical: pal.gridV (rgba string). horizontal: `rgba(${pal.grid},${a})`. horizon line pal.horizon.

Let me set pal.grid as "255,45,149" etc. Already defined.

Let me finalize the sector palettes with these fields.

Now writing the full code.

Let me also ensure on resize we rebuild mountains (peaks depend on H). buildMountains uses H. And sun (sunR). And scan. Good.

Let me set peaks in buildMountains: mtnBack=ridge(H*0.11,90); mtnFront=ridge(H*0.07,70);

Now let me write everything into one file.

Also, the "P pause / M mute" and show in intro/hud.

Let me write.

For the finale boss (Static) should feel like a finale: maybe on death, big whiteout + special victory. Victory triggers after currentSector===2 boss death. Fine.

Let me double check updatePlayer uses upg for fire. And shield/magnet.

Let me write updatePowerups with magnet:
 if(upg.magnet>0){const rad=120+upg.magnet*110;const dx=player.x-p.x,dy=player.y-p.y;const d=Math.hypot(dx,dy);if(d<rad&&d>1){p.x+=dx/d*300*dt;p.y+=dy/d*300*dt;}}

Good.

Now finalize.

Let me write the whole HTML now. I'll be complete.

Let me also add runTime formatting.

function fmtTime(s){const m=Math.floor(s/60);const ss=Math.floor(s%60);return m+':'+String(ss).padStart(2,'0');}

Now victory stats:
 accuracy = shotsFired? Math.round(100*shotsHit/shotsFired):0.

Let me store maxCombo updated on combo increment.

Let me write combo increment in killEnemy and overdrive? overdrive kills also count combo? Let me increment combo in a helper addKill that does combo++ etc. Actually keep in killEnemy and also in overdrive loop I'll just add score + boom but not combo (to avoid weird). Or reuse killEnemy-like. Let me make overdrive call a simplified version. Fine, just score+boom.

Let me now write.

Also need to make sure `player.upg` exists before updatePlayer (set in resetGame). resetGame sets player.upg default and overdrive 0.

Let me define resetGame to include upg and overdrive and stats reset.

resetGame():
 score=0;dispScore=0;combo=0;comboT=0;maxCombo=0;
 wave=0; // not really used now; keep for nothing. I'll drop.
 ... clear arrays ...
 boss=null;slowT=0;timeScale=1;hitStop=0;shake=0;flash=0;whiteFlash=0;paused=false;
 shotsFired=0;shotsHit=0;runTime=0;
 player.x=player.tx=W/2;player.y=H*0.86;player.lives=3;player.inv=1.5;player.fireCd=0;player.spread=0;player.shield=0;
 player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1};player.overdrive=0;
 taunt='';tauntT=0;

startRun(hard):
 hardMode=hard; resetGame(); state='intro'; introT=0; musicOn=true;
 if(AC&&AC.state==='suspended')AC.resume();

Now wave state vars: waveInSector, waveState, waveDelay, spawnQueue, waveMsg, waveMsgT. Initialize in resetGame: waveInSector=1; waveState='inter'; waveDelay=999; (we enter via enterSector anyway). Actually after intro->enterSector sets waveInSector=1, sector card, then beginPlayingSector sets waveState='inter',waveDelay. So resetGame defaults fine.

Let me include waveInSector in resetGame default 1.

Now let me write.

I'll now produce the final answer code.

Let me be careful about the intro total chars auto-advance and skip.

totalIntroChars = introLines.join('').length.

In frame intro:
 introT+=rdt;
 const typed=Math.floor(introT*26);
 if(introT>totalIntroChars/26+1.4) enterSector(0);

Now enterSector:
 function enterSector(sec){currentSector=sec;setSectorPalette(sec);waveInSector=1;
  enemies.length=0;eBullets.length=0;pBullets.length=0;powerups.length=0;
  state='sector';sectorCardT=0;}
setSectorPalette(sec){pal=sectors[sec].pal;buildSun();}

beginPlayingSector(){state='playing';waveState='inter';waveDelay=1.4;waveMsg='';waveMsgT=0;}

sector card auto: if(state==='sector'){sectorCardT+=rdt;if(sectorCardT>=sectorCardDur)beginPlayingSector();}

Good.

Now victory():
 state='victory';vicT=0;musicOn=false;
 flash=1;whiteFlash=0.8;
 if(score>best){best=score;try{localStorage.setItem('neonSparkBest',best);}catch(e){}}
 big fx: for a few booms.

gameOver():
 state='gameover';goT=0;musicOn=false;flash=1;whiteFlash=0.6;shake=40;sfxBoom(true);
 if(score>best){...}

Now let me ensure boss death calls victory/upgrade and clears.

In updateBoss dying completion block:
 bigBoom(boss.x,boss.y);
 flash=1;whiteFlash=0.8;shake=45;hitStop=0.25;sfxBoom(true);
 const pts=5000*mult();score+=pts;popup(boss.x,boss.y,'+'+pts,'#76B900',28);
 powerups.push(... two drops ...);
 boss=null;
 if(currentSector===2){victory();}
 else {state='upgrade';buildUpgradeCards();}

Good.

Now the boss "phase" variable used for patterns; also store boss.phase.

Let me write updateBoss fully.

function updateBoss(dt){
 if(!boss)return;
 boss.t+=dt;
 if(boss.dying>0){
   boss.dieT+=dt;
   if(boss.dieBoom>0){boss.dieBoom-=dt;if(boss.dieBoom<=0){const w=boss?Math.min(W*0.4,320):300;... boom}}
   if(boss.dieT>1.4){ ...completion... return;}
   return;
 }
 boss.y+=(boss.ty-boss.y)*Math.min(1,dt*1.5);
 const frac=boss.hp/boss.max; boss.phase=frac>0.66?0:(frac>0.33?1:2);
 // movement + attacks per id
 switch(boss.id){...}
 // collision with player
 const bw=Math.min(W*0.4,320)/2;
 const dx=boss.x-player.x,dy=boss.y-player.y;
 if(Math.abs(dx)<bw+player.r&&dy<60+player.r&&dy>-40+player.r)hitPlayer();
}

For dying booms use boss.x/boss.y still (boss not null until completion). Good.

Let me code the switch with sub-timers. I'll use boss.fireCd for main and boss.spiralCd for spirals, plus an extra boss.ringCd maybe. I'll reuse fireCd for pattern A and add boss.extra for secondary. Let me just use fireCd and spiralCd.

id0 GLITCHWING:
 movement: boss.x=W/2+Math.sin(boss.t*0.5)*W*0.22;
 if(boss.phase===0){
   boss.fireCd-=dt; if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+24,5,0.2,210,'#ff2d95');boss.fireCd=1.4;}
 }else if(boss.phase===1){
   boss.fireCd-=dt;
   if(boss.fireCd<=0){for(let k=0;k<13;k++){const a=-Math.PI/2+(k-6)/6*1.6+Math.sin(boss.t*0.7)*0.5;fb(boss.x,boss.y,Math.cos(a)*190,Math.sin(a)*190,'#ff2d95');}boss.fireCd=0.8;}
   boss.spiralCd-=dt; if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+24,3,0.15,240,'#ff8a00');boss.spiralCd=2.0;}
 }else{
   boss.fireCd-=dt; if(boss.fireCd<=0){ring(boss.x,boss.y,20,160,'#ff2d95',boss.t);boss.fireCd=1.2;}
   boss.spiralCd-=dt; if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+24,5,0.18,240,'#ff8a00');boss.spiralCd=0.9;}
 }

id1 CANYON WARDEN:
 boss.x=W/2+Math.sin(boss.t*0.38)*W*0.26;
 if(phase0){
   boss.fireCd-=dt; if(boss.fireCd<=0){fb(boss.x,boss.y,Math.cos(2.4)*210,Math.sin(2.4)*210,'#00e5ff');fb(boss.x,boss.y,Math.cos(0.74)*210,Math.sin(0.74)*210,'#00e5ff');boss.fireCd=0.55;}
 }else if(phase1){
   boss.spiralCd-=dt; if(boss.spiralCd<=0){boss.spiralA+=0.5;for(let k=0;k<2;k++){const a=boss.spiralA+k*Math.PI;fb(boss.x,boss.y,Math.cos(a)*200,Math.sin(a)*200,'#00e5ff');}boss.spiralCd=0.06;}
   boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+20,3,0.16,230,'#76B900');boss.fireCd=1.6;}
 }else{
   boss.spiralCd-=dt; if(boss.spiralCd<=0){boss.spiralA+=0.45;for(let k=0;k<3;k++){const a=boss.spiralA+k*Math.PI*2/3;fb(boss.x,boss.y,Math.cos(a)*210,Math.sin(a)*210,'#00e5ff');}boss.spiralCd=0.07;}
   boss.fireCd-=dt;if(boss.fireCd<=0){aimedSpread(boss.x,boss.y+20,5,0.18,240,'#ff2d95');boss.fireCd=1.0;}
 }

id2 THE STATIC (finale):
 boss.x=W/2+Math.sin(boss.t*0.55)*W*0.2+Math.sin(boss.t*1.8)*45;
 if(phase0){
   boss.fireCd-=dt; if(boss.fireCd<=0){for(let k=0;k<16;k++){const a=Math.random()*6.283;fb(boss.x,boss.y,Math.cos(a)*(150+Math.random()*120),Math.sin(a)*(150+Math.random()*120),Math.random()<0.5?'#ff8a00':'#ff2d95');}boss.fireCd=0.75;}
 }else if(phase1){
   // scanline: rows of bullets sweeping down
   boss.fireCd-=dt;
   if(boss.fireCd<=0){const yy=boss.y+20;for(let k=-6;k<=6;k++)fb(boss.x+k*26,yy,(k)*6,150,'#ff8a00');boss.fireCd=0.6;}
   boss.spiralCd-=dt;if(boss.spiralCd<=0){aimedSpread(boss.x,boss.y+20,3,0.15,240,'#ff2d95');boss.spiralCd=1.4;}
 }else{
   boss.spiralCd-=dt; if(boss.spiralCd<=0){boss.spiralA+=0.5;for(let k=0;k<4;k++){const a=boss.spiralA+k*Math.PI/2;fb(boss.x,boss.y,Math.cos(a)*200,Math.sin(a)*200,'#76B900');}boss.spiralCd=0.08;}
   boss.fireCd-=dt;if(boss.fireCd<=0){ring(boss.x,boss.y,24,150,'#ff8a00',boss.t);aimedSpread(boss.x,boss.y+20,5,0.18,250,'#ff2d95');boss.fireCd=0.9;}
 }

Good. ring(x,y,n,speed,c,off) uses off as angle offset.

ring(x,y,n,speed,c,off=0){for(let k=0;k<n;k++){const a=off+k/n*6.283;fb(x,y,Math.cos(a)*speed,Math.sin(a)*speed,c,5);}}

Now drawBoss per id.

Let me write drawBoss:
 function drawBoss(){
  if(!boss)return;
  const x=boss.x,y=boss.y;
  ctx.save();ctx.translate(x,y);
  const fl=1+0.06*Math.sin(boss.t*6);
  if(boss.id===0){
    // winged
    const w=Math.min(W*0.4,300)/2;
    const wing=Math.sin(boss.t*3)*0.4;
    ctx.shadowColor='#ff2d95';ctx.shadowBlur=28;
    // wings
    ctx.fillStyle='rgba(50,0,30,0.85)';
    ctx.strokeStyle='#ff2d95';ctx.lineWidth=2.5;
    for(const s of [-1,1]){
      ctx.save();ctx.scale(s,1);ctx.rotate(wing*0.3*s);
      ctx.beginPath();ctx.moveTo(0,-10);ctx.lineTo(w,-h?)...
    }
  }
 ...
 }
Let me simplify wing drawing: two triangles from center to sides with vertical offset by wing flap.
 function wingTri(s){ctx.beginPath();ctx.moveTo(0,-8);ctx.lineTo(s*w,-40+wing*30);ctx.lineTo(s*w*0.7,10);ctx.lineTo(0,8);ctx.closePath();ctx.fill();ctx.stroke();}
 call wingTri(-1);wingTri(1);
 then central diamond: ctx.rotate(0); draw diamond shape with acid core.

I'll just make it look decent.

For id1 hexagon:
 const r=90;
 draw hexagon path with r, fill dark, stroke cyan, plus inner rotating hexagon, plus core.
 function hex(r,rot){ctx.beginPath();for(let k=0;k<6;k++){const a=rot+k/6*6.283;const px=Math.cos(a)*r,py=Math.sin(a)*r;k?ctx.lineTo(px,py):ctx.moveTo(px,py);}ctx.closePath();}

For id2 static orb:
 const R=110;
 ctx.shadowColor='#ff8a00';ctx.shadowBlur=30;
 ctx.fillStyle='#0a0004';ctx.beginPath();ctx.arc(0,0,R,0,7);ctx.fill();
 ctx.strokeStyle='#ff2d95';ctx.lineWidth=3;ctx.stroke();
 // static noise pixels
 for(let k=0;k<90;k++){const a=Math.random()*6.283,rr=Math.sqrt(Math.random())*R;const px=Math.cos(a)*rr,py=Math.sin(a)*rr;const c=Math.random()<0.5?'#ff8a00':'#76B900';ctx.fillStyle=c;ctx.globalAlpha=0.5;ctx.fillRect(px,py,3,3);}
 ctx.globalAlpha=1;
 // eyes
 ctx.fillStyle='#fff';ctx.shadowColor='#fff';ctx.shadowBlur=12;
 ctx.fillRect(-34,-16,20,10);ctx.fillRect(14,-16,20,10);
 // glitchy mouth
 ctx.strokeStyle='#ff2d95';...
 Good enough.

Now HP bar at top with name:
 const bw=W*0.5,bx=(W-bw)/2,by=22,frac=Math.max(0,boss.hp/boss.max);
 draw bar, name centered above? put name in middle of bar.
 I'll draw name below bar: ctx.font, fillText(boss.name, W/2, by+24) centered, color boss color.

Let me write.

Alright. Also taunt under name when tauntT>0.

Let me now assemble the entire file. I'll write it out.

I need to also make sure `wave` variable not used; I'll remove references. HUD shows sector & waveInSector.

HUD top center:
 ctx.textAlign='center';
 ctx.font='bold 16px monospace';
 ctx.fillStyle=accent; shadow;
 ctx.fillText('SECTOR '+(currentSector+1)+' / 3', W/2, 24);
 ctx.font='12px monospace'; ctx.fillStyle='rgba(255,255,255,0.7)';
 ctx.fillText(waveState==='boss'?'BOSS — '+sectors[currentSector].boss.name : 'WAVE '+waveInSector+' / 4', W/2, 42);

accent = sectors[currentSector].accent.

Now overdrive bar bottom center:
 const ow=Math.min(W*0.4,340),ox=(W-ow)/2,oy=H-30;
 ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(ox,oy,ow,10);
 const frac=player.overdrive;
 ctx.fillStyle= frac>=1? '#76B900':'rgba(118,185,0,0.7)';
 ctx.shadowColor='#76B900';ctx.shadowBlur=frac>=1?18:6;
 ctx.fillRect(ox,oy,ow*frac,10);
 ctx.strokeStyle='rgba(118,185,0,0.6)';ctx.strokeRect(ox,oy,ow,10);
 ctx.font='11px monospace';ctx.textAlign='center';
 if(frac>=1){const pa=0.5+0.5*Math.abs(Math.sin(time*6));ctx.globalAlpha=pa;ctx.fillStyle='#76B900';ctx.fillText('OVERDRIVE READY — PRESS SPACE',W/2,oy-8);ctx.globalAlpha=1;}
 else {ctx.fillStyle='rgba(118,185,0,0.6)';ctx.fillText('OVERDRIVE',W/2,oy-8);}

Good.

Now let me finalize and output.

I also want the score/lives at top-left and best below, as before.

Let me write the whole thing now.

Let me also confirm the intro text is 4 lines.

Let me write final answer.

One more: onPointer for 'intro' skip should call enterSector(0) but only if we are in intro (first run). Good. Also space key during intro -> enterSector(0).

Also during 'sector', click/space -> sectorCardT=sectorCardDur (advance next frame). Good.

Let me make sure keyboard space in playing triggers overdrive, not skip.

Key handler:
 if(k===' '||k==='enter'){e.preventDefault();
   if(state==='title'&&titleT>1)startRun(false);
   else if(state==='intro')enterSector(0);
   else if(state==='sector')sectorCardT=sectorCardDur;
   else if(state==='playing')unleashOverdrive();
   else if(state==='gameover'&&goT>0.6)startRun(false);
   else if(state==='victory')startRun(hardMode);
 }
 if(k==='p'&&state==='playing')paused=!paused;
 if(k==='m')toggleMute();
 if(state==='upgrade'){ if(k==='1')chooseCard(0); if(k==='2')chooseCard(1); if(k==='3')chooseCard(2);}
 if(state==='victory'){ if(k==='1'||k==='r')startRun(hardMode); if(k==='2'||k==='h')startRun(!hardMode);}

Good.

chooseCard(i): if upgradeCards[i] -> apply, fx, enterSector(currentSector+1).

Now let me write buildUpgradeCards and card rects.

function buildUpgradeCards(){
 const pool=[...];
 // shuffle, take 3
 const arr=pool.slice();
 for(let i=arr.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]];}
 upgradeCards=arr.slice(0,3);
}
function upgradeCardRects(){
 const cw=Math.min(240,(W-40)/3),ch=170,gap=Math.min(20,(W-cw*3)/3);
 const total=cw*3+gap*2, x0=(W-total)/2, y=H*0.42;
 return upgradeCards.map((c,i)=>({x:x0+i*(cw+gap),y,w:cw,h:ch,i}));
}
Draw and click use these.

Card apply: c.apply(player.upg) but +1 life uses player.lives; fine.

Let me write apply functions referencing upg and player.

Now chooseCard uses upgradeCards[i].

Let me ensure after choose we also grant a bit of overdrive and heal? no heal. Just apply.

Alright, writing final.

Let me also handle that during 'upgrade', the frame should still update particles/fx (for lingering booms) but not player/enemies. I'll do: if(state==='upgrade'){updateFx(rdt);} similar for victory/gameover.

Let me set in frame:
 if(state==='playing'){ if(!paused){ runTime+=dt; updatePlayer; updateWaves; updateEnemies; updateBullets; updatePowerups; updateFx(dt);} }
 else if(state==='upgrade'||state==='victory'||state==='gameover'){ updateFx(rdt*0.5); }

But updateFx uses dt for combo decay etc. Fine to pass rdt*0.5.

Also gridScroll updated at top always.

Let me also keep slowT/timeScale update only in playing (since it affects dt). For other states timeScale should reset to 1. Let me set: if not playing, timeScale=1 and slowT=0? Actually keep slowT only in playing. In frame:
 let dt=rdt;
 if(state==='playing'){
   if(!paused){
     slowT=Math.max(0,slowT-dt);
     const target=slowT>0?0.32:1; timeScale+=(target-timeScale)*Math.min(1,rdt*7);
     dt=rdt*timeScale;
     if(hitStop>0){hitStop-=rdt;dt=0;}
   } else dt=0;
 } else { timeScale=1; }
Hmm hitStop: only meaningful in playing. Let me handle hitStop within playing.

Let me restructure frame cleanly:

function frame(ts){
 requestAnimationFrame(frame);
 const rdt=Math.min(0.05,(ts-last)/1000||0); last=ts;
 time+=rdt; gridScroll=(gridScroll+rdt*0.5)%1;
 scheduleMusic();
 let dt=rdt;
 if(state==='playing'){
   if(paused){ dt=0; }
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
 } else if(state==='intro'){ introT+=rdt; const typed=totalIntroChars/26; if(introT>typed+1.4)enterSector(0); }
 else if(state==='sector'){ sectorCardT+=rdt; if(sectorCardT>=sectorCardDur)beginPlayingSector(); }
 else if(state==='title'){ titleT+=rdt; }
 else { updateFx(rdt*0.6); if(state==='gameover')goT+=rdt; if(state==='victory')vicT+=rdt; }
 render();
}

Good.

Now the updateFx also decays combo, dispScore, shake, flash, waveMsgT. Fine.

Let me ensure dispScore updates in updateFx (yes).

Now, the initial state 'title' with titleT=0. On load. Good.

Let me also set introLines and totalIntroChars.

Alright, final code writing. Let me output.

I'll write it all in one go, being careful.

Let me also double check hexA for 3-digit hex — all our hex are 6-digit, fine.

Let me also make sure buildSun is called once at init (resize calls buildSun using pal default sectors[0].pal). And on sector change.

pal initialized = sectors[0].pal at top. But sectors defined before? I'll define sectors before resize. Order: define palette data, then canvas stuff. Let me define sectors near top after helpers.

Let me place: constants, palette/sectors data, audio, state vars, player, functions, init (resize + rAF) at bottom.

Let me ensure player defined before updatePlayer uses upg. Yes.

Let me write.

Also need `hardMode` variable.

Also `currentSector` default 0.

Also `pal` default.

Now, one concern: drawTitle uses pal for colors (sector 0). Since we reset palette each enterSector but title is only at start with sector0 palette. Good. But if user returns to title? We don't have a "back to title" except restart goes to intro. So title only first. Fine. Actually victory "play again" goes to intro not title. So title only once. Acceptable.

Let me write final.

I'll write the sun position constant sunCY in resize: sunCY=horizonY - sunR*0.45.

Let me also verify sun stripes visible with these: done earlier, ~119px band. Good.

Let me write.

Let me also add subtle: in drawSun, after drawing sunCanvas, add a bright horizontal line at the sun's mid to emphasize? Not needed.

Also add: to make stripes "clearly visible", increase contrast: the striped (transparent) parts show sky. Since sky near horizon is lighter (skyHor), stripes will show as lighter bands against the orange/magenta disc. Good contrast. 

Let me finalize.

Now writing the complete file. I'll include everything.

Let me count enemy bullet radius default 5 in fb.

Let me write drawEntities to also draw boss and player (player only in playing). Keep as before.

Let me write it all.

For popups during upgrade/victory I don't draw (state check). Fine.

Let me produce.

I realize I should double-check: in updateBullets, when a pBullet hits an enemy I splice enemy and break; but I also need to only splice the pBullet once. My code: compute hit, then after loops if(hit) splice pBullet. Good.

But when boss dying set, I also want to not double. Fine.

Also shotsHit++ on each hit (enemy or boss). Good.

Let me write final answer now.

I'll write it compactly but complete. Let me go.

Let me also make sure `wave` removed from resetGame; not referenced elsewhere. I'll drop it.

Also `waveMsg`/`waveMsgT` used by drawWaveMsg; set on beginWave and boss.

drawWaveMsg uses waveMsg/waveMsgT and taunt/tauntT.

Let me write drawWaveMsg:
 function drawWaveMsg(){
   if(waveMsgT>0){
     const total=waveMsgT>2?0:2.6-waveMsgT; // fade in during first 0.6
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
     ctx.fillText(taunt, W/2, H*0.32+40);
     ctx.restore();
   }
 }
Good.

Now tauntT decrement in updateFx: if(tauntT>0)tauntT-=dt.

Let me add.

OK writing now for real.

Let me also ensure `sectorCardDur=2.6`, `vicT`, `goT`, `titleT`, `introT` vars.

Let me write.

Final output below.
