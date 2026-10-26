We need answer to user: provide complete updated HTML file only in code block, no explanation. Need analyze and fix listed issues. Need ensure all requirements. We have prior full code. Need fix:
1 ReferenceError tauntT not defined in drawWaveMsg. Need declare let tauntT=0? In code we set taunt='' but not tauntT. Need use tauntT in drawWaveMsg. Could replace with a declared variable tauntT, set in beginWave when boss. Initialize tauntT=0 in resetGame and declare. Check render path for undeclared variables:
- tauntT needs declaration.
- sectorT used for upgrade animation; declared let sectorT=0. Good.
- hoverCard declared.
- clearPts? not used? declared.
- waveMsgT etc ok.
- taunt variable. Need tauntT.
- defeatShown, bossDefeatMsg? not used perhaps.
- In drawWaveMsg uses tauntT; add declaration and update.
- In resetGame set tauntT=0; in beginWave boss: tauntT=3 maybe. In update if boss? maybe decay in updateFx? We can decay tauntT in updateFx or main playing update. Simpler: let tauntT=0; in beginWave boss set tauntT=3; in updateFx: if(tauntT>0)tauntT-=dt; (but updateFx called in all states with dt; okay).
- drawWaveMsg: if(tauntT>0&&boss).
- drawBoss? no taunt.

2 Boss defeat lines: Show defeat message near boss while explodes. Need in drawBoss when boss.dying>0 draw boss.boss.defeat large glowing text near boss (probably above). Use boss.defeat. Need ensure visible while dying. Could also use popup. Add in drawEntities? drawBoss has boss. In drawBoss, after drawing, if boss.dying>0: save translate? draw text centered at x,y-110? font bold 28, shadow color boss color/white, fill. Need maybe alpha. The boss explodes over 1.4 sec; show. Ensure not missing. Add.

3 Boss deaths: boss stays whole and still then vanishes. Need make flash, shake, break apart into pieces during die. Currently dying: dieT, dieBoom every 0.09 random boom, no movement, no pieces. Need implement break apart: while dying, boss shakes (random offsets), flashes (white overlay alpha oscillating), spawn particles/shards; maybe scale/rotate. Need not vanish whole: draw fragments? Could add boss.debris array? We can during dying in update spawn shards particles with gravity? Current particles no gravity but okay. Better: when boss.dying, in updateBoss add boss.shakeX/Y random; draw with random translate and rotation; flash white overlay by drawing semi-transparent white over boss shape maybe using globalCompositeOperation 'lighter' rect? Also break apart: create a list of debris? Simpler: use existing particles but need large polygon shards. Could add boss.shards array initialized when dying: 20 pieces with x,y,vx,vy,rot,vr,life,color. Update in updateBoss: for shards, move, rotate, life-=dt. Draw in drawBoss: if dying, draw original shape with decreasing scale and alpha plus shards. Need ensure not too much. Also random small booms continue. Add boss.shards=[]; boss.dieT=0. In updateBoss dying:
 boss.dieT += dt;
 boss.shakeX = (Math.random()-0.5)*16; boss.shakeY = (Math.random()-0.5)*12;
 flash: boss.flash = 0.5+0.5*Math.sin(boss.dieT*40);
 if boss.dieBoom ... spawn shards? We can initialize shards when entering dying, then update them. Also spawn extra particles.
 For shards: each {x,y,vx,vy,rot,vr,size,life,max,color,shape}. Update x+=vx*dt etc; vy += 80*dt maybe; life-=dt.
 Draw: if dying: draw original boss with translate(x+shake, y+shake), scale = 1 + 0.15*Math.sin(dieT*30), alpha maybe 1 until last 0.3? Also white overlay. Then draw shards as glowing triangles/rects. Need boss.dying >0. Also final bigBoom after 1.4. Could reduce duration? 1.4 okay but make lively.
 Need ensure shards not huge performance.
 In spawnBoss add shards:[], shakeX=0, shakeY=0, flash=0.
 In updateBoss when hp<=0 set dying=1,dieT=0,dieBoom=0, initShards(boss).
 initShards:
 boss.shards=[]; for i 30: angle random, dist random 40, vx = cos* (100+rand300), vy=sin*... - maybe upward; rot random, vr random; size 8+rand26; life=0.9+rand0.9; max=life; color pick; shape: random.
 But boss colors: sectors[currentSector].boss.color? boss has no color? Could add boss.color=sec.boss.color. Use boss.color and white.
 Draw shards: ctx.save translate to boss.x+shake? If shards have absolute x/y, just draw each with translate. Use globalCompositeOperation lighter.
 Original boss draw currently uses ctx.translate(boss.x,boss.y). Modify to use bx=boss.x+(boss.dying>0?boss.shakeX:0), by=...; if dying add ctx.rotate(Math.sin(boss.dieT*50)*0.08); ctx.globalAlpha=1? At end if dying maybe globalAlpha = max(0.2, 1 - max(0,(boss.dieT-0.9)/0.5)); so it breaks away. But if fade too early, final explosion. Could keep alpha=1 until 1.1 then fade to 0.05. Also draw white flash overlay: after shape, if boss.dying>0, ctx.globalCompositeOperation='lighter'; ctx.fillStyle='rgba(255,255,255,'+(0.2+0.5*abs(sin(dieT*30))).toFixed(2)+')'; draw approximate circle or shape? Use circle radius maybe 120. That will glow.
 Need make sure existing code structure.

4 Upgrade levels: RAPID FIRE shows LV 5/6 initially. upgLevel('rapid') returns Math.min(5,Math.round(5/(u.fireRate*1.25))). Initial fireRate=1 => 5/1.25=4, min5? 4 not 5? Wait user says LV 5/6. max 5, level display lv+1 / max+1 => LV 5/6 means lv=4. Yes. They want start at level 0. Need change upgLevel for rapid: maybe track count? We don't have explicit count. We can compute from fireRate? Starting fireRate=1. Each apply multiplies by 0.8 down to 0.5. Levels: 0 at fireRate>=0.95? 1 at 0.8, 2 at 0.64, 3 at 0.512, 4 at min0.5? Max 4? But they want go up by exactly one each time choose it. Need robust: add upgrade counts: player.upg.levels? Or add player.upgCounts object. Since upgPool apply modifies stats, better store counts: player.upg.counts = {rapid:0,twin:0,hull:0,shield:0,magnet:0,od:0}; upgLevel(kind) returns counts[kind]||0; max as before. apply: u.counts[kind]++. But existing player.upg initialized. Need update chooseCard to increment counts. Since upgPool apply currently only modifies stats; we can in chooseCard before apply: player.upg.counts[kind]++? But if apply function could also. Better: player.upg = {twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1,counts:{rapid:0,twin:0,hull:0,shield:0,magnet:0,od:0}}. upgLevel(kind){return player.upg.counts[kind]||0}. upgMax: rapid 4? If max=4 then display LV 0/5? User said every upgrade should start at level 0 and go up by exactly one each time I choose it. Current max for rapid maybe 5? They didn't object max, but initial LV 5/6. Need start at 0 and max maybe 5? We can set max 4 or 5. But apply for rapid currently allows min 0.5, so levels: 0 fireRate=1, 1=0.8, 2=0.64, 3=0.512, 4=0.5? Actually min 0.5, so 4 purchases possible? 1*0.8^4=0.4096 -> min 0.5, so 4th reaches min. 5th would no effect but max should 4. But current max 5. Better set max 4. Or keep max 5 and adjust fireRate values? User says every upgrade start level 0 and go up by exactly one each time choose it. Could make max 5 and fireRate=0.8^level, min 0.32. apply: u.fireRate = Math.max(0.32, u.fireRate*0.8). That yields 5 purchases. But no issue. Need upgMax rapid maybe 5. But initial counts 0 -> LV 0/6. Each choose increments. Good. Use counts.
 For hull: initial lives 3, upgLevel hull Math.min(6,lives-3). That's okay but if choose hull increments lives and level. Could use counts too for consistency. upgMax hull 3? Since lives can go up to 6? If initial 3, max 3 to reach 6. Current max 6 gives LV 0/7, but can only +3? If choose hull 4 times lives 7? upgLevel min(6,lives-3) caps but apply still increases. Better max 3. Use counts for hull max 3. apply: player.lives++ but only if counts.hull<3? chooseCard shouldn't choose maxed? Currently can choose maxed maybe. Need prevent choosing maxed? Not required but better. Could if level>=max, skip? But user wants exactly one each time; if max reached maybe no effect. We can leave but max counts. For display LV counts/max. If choose hull beyond max, counts could exceed? In chooseCard, if level>=max maybe return or not apply. But user didn't ask. To be safe, in chooseCard: const card=upgradeCards[i]; if(card && upgLevel(card.kind)<upgMax(card.kind)) { card.apply; counts++; ...}. But then clicking maxed does nothing. Good.
 Need update counts in chooseCard, not apply. Or modify each apply? Easiest:
 function chooseCard(i){
   const card=upgradeCards[i]; if(!card) return;
   if(upgLevel(card.kind)>=upgMax(card.kind)) return;
   player.upg.counts[card.kind]++;
   card.apply(player.upg);
   ...
 }
 upgLevel uses counts.
 Need reset player.upg counts in resetGame.
 For twin max 3, counts; apply u.twin = Math.min(3,u.twin+1). Good.
 shield: max 5? apply *1.5. counts.
 magnet max 5? apply +1. counts.
 od max 5? apply *1.4. counts.
 Need update upgMax: rapid 5, twin 3, hull 3, shield 5, magnet 5, od 5. Or rapid maybe 5.

5 Upgrade cards larger 50% on 1920x1080: currently cw=Math.min(240,(W-40)/3), ch=170, gap max(8,...). For 1920: cw=240, ch=170. Need about 50% bigger: cw ~360, ch~255. Still three in row. Use cw=Math.min(Math.round(W*0.22), Math.round((W-60)/3))? For 1920, W*0.22=422, (1860)/3=620, min 422. Too big? 50% bigger from 240 -> 360. W*0.1875=360. Could do cw=Math.min(Math.round(W*0.19), Math.round((W-80)/3)); For 1920: 364. ch=Math.round(cw*0.72) -> 262. Good. On small screens maybe. Need text larger. Title font currently Math.min(17,cw*0.075). For cw 364, 27. Good. Description font 11 -> 15 or 16. Level font 12 -> 15. Pips bigger. Icon maybe larger. Card y maybe H*0.36? Need fit 3 cards. If cw 364, total 3*364+gap*2. gap = Math.max(14,(W-cw*3)/3) = (1920-1092)/3=276? That's huge, total width 1092+552=1644. Fine. But gap large maybe okay. Could set gap=Math.min(40,Math.max(16,(W-cw*3)/3))? To keep cards centered not spread too much. But three in row, large gap okay. Maybe use gap=Math.min(48, Math.max(20,(W-cw*3)/3)). For 1920 gap=48, total 1200. Better. cw maybe 380. Use cw = Math.min(Math.round(W*0.20), Math.round((W - 3*48) / 3))? For 1920: min384, (1920-144)/3=592 =>384. Good. ch = Math.round(cw*0.68)=261. Total 3*384+96=1248.
 For 1366: W*0.20=273, okay. Mobile maybe 375: W*0.20=75, too small? Need three in row. Could use cw = Math.min(Math.round(W*0.20), Math.round((W - 120) / 3), 420). For 1920 384. For 768 153. Good.
 Card y: H*0.34? With height 261, y 374, ends 635. Title at 0.26, bottom text 0.86. Good.
 Need adjust drawUpgradeIcon size? It uses fixed size ~14; for larger card, maybe scale icon by card w. Could pass scale = cw/360. In drawUpgrade call drawUpgradeIcon(c.kind, cx, yy+72, c.color, scale). Modify function signature optional scale. Use ctx.scale(s,s) around icon. Then icon larger.
 Text: label font = Math.min(24, cw*0.075) maybe 28. But card width 384, 28. Good. Description font 15 or 16. line height 18. Pips: pw=32, gap=8, height 7. Level font 15.
 Need ensure wrapText with maxW and lh.

Also need check no other undefined variables in render path.
Let's review prior code for potential undeclared:
- In drawHUD, uses sectors[currentSector].accent. ok.
- drawWaveMsg uses tauntT. fix.
- drawBoss defeat message uses boss.defeat. ok.
- drawEntities uses state, player. ok.
- drawUpgrade uses hoverCard, upgradeCards, sectorT. ok.
- drawSectorClear uses sectorClearT, secFired, secHit, secNoHit, secKill. ok.
- drawVictory uses victoryBtnRects, hardMode, runTime, maxCombo, shotsHit, shotsFired, score, best. ok.
- drawTitle uses titleT, best. ok.
- drawIntro uses introT, totalIntroChars. ok.
- drawBackground uses pal etc. ok.
- updateFx uses combo, comboT, dispScore, score. ok.
- main frame uses sectorT. declared.
- onPointer uses startRun, chooseCard, etc. ok.
- victory button uses startRun. ok.
- In chooseCard, player.upg.counts needs exist. resetGame. In startRun resetGame. In initial player.upg before start? For title not used. But if user somehow upgrade before start no.
- In resetGame, player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1,counts:{...}}.
- In upgLevel uses player.upg.counts. If state gameover? okay.
- upgMax uses kind.

Need preserve everything else exactly? We can modify only needed. Need output full file. Must be one ```html code block, no explanation. Ensure no external.

Let's craft final code with changes. Need be careful syntax.

Detailed modifications:

Declare variables:
let tauntT=0;
Add near taunt: let waveMsg='',waveMsgT=0,taunt='',tauntT=0;

In resetGame:
 taunt='';tauntT=0;
 player.upg={twin:0,fireRate:1,shieldDur:1,magnet:0,odGain:1,counts:{rapid:0,twin:0,hull:0,shield:0,magnet:0,od:0}};

In beginWave boss:
 waveMsg=sec.boss.name;waveMsgT=2.6;taunt=sec.boss.taunt;tauntT=3;

In updateFx:
 if(tauntT>0)tauntT-=dt;
 (Could be called with dt=0 when paused? okay. For non-playing states updateFx(rdt*0.6) so taunt fades.)

Boss spawn:
 boss={...,color:sec.boss.color,shards:[],shakeX:0,shakeY:0,flash:0, ...};
Need existing fields: id,name,defeat,x,y,ty,hp,max,t,fireCd,spiralCd,spiralA,phase,dying,dieT,dieBoom,finale. Add.

initBossShards(boss):
 boss.shards=[];
 const cols=[boss.color,'#ff2d95','#ff8a00','#00e5ff','#76B900','#ffe14d'];
 for(let i=0;i<36;i++){
  const a=Math.random()*6.283, sp=120+Math.random()*420;
  boss.shards.push({
    x:(Math.random()-0.5)*Math.min(W*0.4,300),
    y:(Math.random()-0.5)*100,
    vx:Math.cos(a)*sp,
    vy:Math.sin(a)*sp - 60,
    rot:Math.random()*6.283,
    vr:(Math.random()-0.5)*10,
    size:8+Math.random()*26,
    life:0.8+Math.random()*1.0,
    max:1.8,
    color:cols[Math.floor(Math.random()*cols.length)],
    shape:Math.floor(Math.random()*3)
  });
 }
Need max set life: const lf=...; life:lf,max:lf.

In updateBoss dying:
 boss.dieT += dt;
 boss.shakeX=(Math.random()-0.5)*18;
 boss.shakeY=(Math.random()-0.5)*14;
 boss.flash=0.5+0.5*Math.sin(boss.dieT*40);
 for(const sh of boss.shards){sh.x+=sh.vx*dt;sh.y+=sh.vy*dt;sh.vy+=90*dt;sh.rot+=sh.vr*dt;sh.life-=dt;sh.vx*=(1-1.2*dt);} // if life<=0? Could leave, draw alpha max0.
 // Also random particle sparks
 if(Math.random()<0.7) boom(boss.x+(Math.random()-0.5)*160,boss.y+(Math.random()-0.5)*80,boss.shards[Math.floor(Math.random()*boss.shards.length)].color,6,0.5);
 boss.dieBoom logic as before.
 if(boss.dieT>1.4) final.
 Need not filter shards; draw alpha.

DrawBoss:
 Need use bx,by and dying effects. Current:
 function drawBoss(){ if(!boss)return; const x=boss.x,y=boss.y; ctx.save();ctx.translate(x,y); ... }
 Modify:
 if(!boss)return;
 const bx=boss.x+(boss.dying>0?boss.shakeX:0), by=boss.y+(boss.dying>0?boss.shakeY:0);
 ctx.save();ctx.translate(bx,by);
 const fl=1+0.06*Math.sin(boss.t*6);
 if(boss.dying>0){ctx.rotate(Math.sin(boss.dieT*40)*0.12); const fade=boss.dieT>1.0?Math.max(0,1-(boss.dieT-1.0)/0.4):1; ctx.globalAlpha=fade; }
 draw shape as before using boss.id.
 if(boss.dying>0){
   ctx.globalCompositeOperation='lighter';
   const fa=(0.15+0.55*Math.abs(Math.sin(boss.dieT*32)))*ctx.globalAlpha;
   ctx.fillStyle='rgba(255,255,255,'+fa.toFixed(3)+')';
   ctx.beginPath();ctx.arc(0,0,140,0,7);ctx.fill();
   // defeat text
   ctx.globalCompositeOperation='source-over';
   ctx.globalAlpha=Math.min(1,ctx.globalAlpha+0.2);
   ctx.font='bold 28px monospace';ctx.textAlign='center';
   ctx.shadowColor=boss.color;ctx.shadowBlur=24;ctx.fillStyle='#fff';
   ctx.fillText(boss.defeat,0,-150);
 }
 ctx.restore();
 if(boss.dying>0){
  ctx.save();ctx.globalCompositeOperation='lighter';
  for(const sh of boss.shards){
    if(sh.life<=0)continue;
    const a=Math.min(1,sh.life/(sh.max*0.5));
    ctx.globalAlpha=a;
    ctx.translate(sh.x,sh.y);ctx.rotate(sh.rot);
    ctx.shadowColor=sh.color;ctx.shadowBlur=12;ctx.fillStyle=sh.color;
    if(sh.shape===0){ctx.beginPath();ctx.moveTo(-sh.size,0);ctx.lineTo(0,-sh.size*0.7);ctx.lineTo(sh.size*0.6,sh.size*0.5);ctx.closePath();ctx.fill();}
    else if(sh.shape===1){ctx.fillRect(-sh.size/2,-sh.size/4,sh.size,sh.size/2);}
    else {ctx.beginPath();ctx.arc(0,0,sh.size*0.4,0,7);ctx.fill();}
  }
  ctx.restore();
 }
 Need note ctx.globalAlpha changed inside save/restore. For defeat text, after ctx.globalAlpha maybe set to 1. Use let baseA=ctx.globalAlpha; then set. Simpler:
 if(boss.dying>0){
   ctx.globalCompositeOperation='lighter';
   ctx.fillStyle='rgba(255,255,255,'+((0.15+0.55*Math.abs(Math.sin(boss.dieT*32))).toFixed(3)+')';
   ctx.beginPath();ctx.arc(0,0,140,0,7);ctx.fill();
   ctx.globalCompositeOperation='source-over';
   ctx.globalAlpha=1;
   ctx.font='bold 28px monospace';ctx.textAlign='center';
   ctx.shadowColor=boss.color;ctx.shadowBlur=24;ctx.fillStyle='#fff';
   ctx.fillText(boss.defeat,0,-150);
 }
 ctx.restore();
 This text will be scaled by ctx.save? Not scaled. It will rotate if we set ctx.rotate for dying. If boss rotated, text rotates slightly, okay but maybe better not rotate text. Could draw text outside rotated ctx. Better:
 - Draw shape inside save/restore with rotation/fade.
 - Then if dying, draw text and shards in separate save without rotation.
 So:
 function drawBoss(){
  if(!boss)return;
  const bx=..., by=...;
  ctx.save();ctx.translate(bx,by);
  const fl=...;
  if(boss.dying>0){ctx.rotate(...);const fade=...;ctx.globalAlpha=fade;}
  // shape
  if(boss.dying>0){white flash circle maybe inside? okay with rotate}
  ctx.restore();
  if(boss.dying>0){
    ctx.save();ctx.globalCompositeOperation='lighter'; // draw flash circle maybe non-rotated?
    ctx.fillStyle=...;ctx.beginPath();ctx.arc(bx,by,150,0,7);ctx.fill();
    ctx.globalCompositeOperation='source-over';
    ctx.font='bold 30px monospace';ctx.textAlign='center';ctx.shadowColor=boss.color;ctx.shadowBlur=26;ctx.fillStyle='#fff';
    ctx.fillText(boss.defeat,bx,by-160);
    ctx.restore();
    // shards draw
  }
 }
 But need flash circle not too big. Use radius 140.
 Need ensure original shape for boss.id 2 has random noise each frame; okay.

But drawBoss currently has ctx.restore at end. We'll rewrite.

Need also draw shards before/after text? After.

Potential issue: boss.dying fade original shape to 0 at 1.4, but final bigBoom at 1.4. Good.
Need maybe keep boss visible as shards until final. Good.

Upgrade cards larger:
Modify drawUpgradeIcon(kind,cx,cy,color,scale):
 function drawUpgradeIcon(kind,cx,cy,color,scale){ ctx.save(); ctx.translate(cx,cy); ctx.scale(scale,scale); ... }
Need existing uses no scale for HUD? Only upgrade. Could default scale=1.
In drawUpgrade: const scale=r.w/360; drawUpgradeIcon(c.kind,r.x+r.w/2,yy+80,c.color,scale);
Card rects:
function upgradeCardRects(){
  const gap=Math.min(48,Math.max(20,Math.round((W-140)/3)));
  const cw=Math.min(Math.round(W*0.20),Math.round((W-gap*2-60)/3),440);
  const ch=Math.round(cw*0.68);
  const total=cw*3+gap*2, x0=(W-total)/2, y=H*0.34;
  return upgradeCards.map((c,i)=>({x:x0+i*(cw+gap),y,w:cw,h:ch,i}));
}
For 1920: gap=min48,max20,(1780/3=593)->48. cw=min384,(1920-96-60=1764)/3=588,440 =>384. ch261. Good.
For 1366: gap48, cw min273,(1366-156)/3=403 =>273, ch185. Bigger than old 240/170? width 14% bigger, height 8. But user specifically 1920; okay. Could make 1920 50%. For smaller, relative.
For 1080 screen: H=1080, y=367, ends 628. Good.
Text:
 label font Math.min(26, r.w*0.072). For 384 ->27? min 26.
 level font 15.
 description font 15, lh 18.
 pips: pw=30, gap=8, height=7. total for max 5 = 170, fits.
 icon y = yy + r.h*0.27? For h261 -> 70. Use yy + 84.
 label yy + r.h*0.60 (157). level 0.70 (183). pips 0.78 (203). desc 0.87 (227). Need enough.
 Let's set:
 icon cy=yy + r.h*0.28;
 label y=yy + r.h*0.58;
 level y=yy + r.h*0.68;
 pips y=yy + r.h*0.75;
 desc y=yy + r.h*0.84;
 For h261: icon73, label151, level177, pips196, desc219. Good.
 wrapText desc maxW r.w-40, lh 18.
Need card animation y offset: yy=r.y + (1-ease)*90 - lift.

upgLevel/max changes:
function upgLevel(kind){const c=player.upg&&player.upg.counts;return c?c[kind]||0:0;}
function upgMax(kind){switch(kind){case 'twin':return 3;case 'hull':return 3;default:return 5;}}
chooseCard:
function chooseCard(i){
 if(state!=='upgrade'||!upgradeCards[i])return;
 const card=upgradeCards[i];
 if(upgLevel(card.kind)>=upgMax(card.kind))return;
 player.upg.counts[card.kind]=(player.upg.counts[card.kind]||0)+1;
 card.apply(player.upg);
 player.overdrive=Math.min(1,player.overdrive+0.15);
 sfxPower();
 enterSector(currentSector+1);
}
Need ensure player.upg.counts exists. resetGame. Also initial player.upg before reset? At bottom: player.upg={...,counts:{...}}.

Apply functions: rapid: u.fireRate=Math.max(0.32,u.fireRate*0.8) (5 levels from 1: 0.8,0.64,0.512,0.4096,0.32768; min 0.32). Good.
hull: player.lives++ but max 3. If counts < max.
others as before.

Need check drawUpgrade uses upgLevel and upgMax. If player.upg counts maybe not for old? reset.

Potential issue: player.lives can exceed 6? max hull 3 from 3 =>6. Good.

Now need check all variables in render path:
- In drawBoss uses boss.shards, boss.shakeX, boss.shakeY, boss.flash, boss.defeat, boss.color, boss.dieT. All initialized.
- In initBossShards uses W,H. okay.
- In updateBoss uses boom, boss.shards. okay.
- In drawWaveMsg uses tauntT. declared.
- In drawHUD? boss health bar: current code? I didn't see drawBossHealth? Wait requirement: boss arrives with health bar. In prior code? I don't recall drawing boss health bar! The user says HUD is gone, including boss health bar never appear. Need check prior code: drawHUD only score, sector, lives, powerups, overdrive, combo. It did NOT draw boss health bar. But user expects boss health bar. The requirement originally: every fifth wave a boss arrives with a health bar. In prior code maybe missing. Need add boss health bar in drawHUD or drawWaveMsg. They specifically: "During play the score, lives, combo, Overdrive meter and the boss health bar never appear." So need add boss health bar. Since HUD gone due tauntT error? drawHUD called in render after drawEntities? In code: if(state==='playing'){drawWaveMsg();drawHUD();...}. drawWaveMsg throws before drawHUD, so HUD gone. Fix tauntT restores score/lives/combo/overdrive. But boss health bar still absent. Need add.
Where? In drawHUD, if boss && boss.dying===0: draw top center bar. Since waveMsg top center, maybe bar under waveMsg? Use y=92. Or top center below sector? We have sector top right if boss, combo under? Need design:
 In drawHUD:
 if(boss){
  const bw=Math.min(W*0.6,700), bh=18, bx=(W-bw)/2, by=94;
  ctx.fillStyle='rgba(0,0,0,0.55)';ctx.fillRect(bx,by,bw,bh);
  const frac=Math.max(0,boss.hp/boss.max);
  const col=frac>0.5?'#76B900':(frac>0.25?'#ff8a00':'#ff2d95');
  ctx.fillStyle=col;ctx.shadowColor=col;ctx.shadowBlur=16;ctx.fillRect(bx,by,bw*frac,bh);
  ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,0.35)';ctx.strokeRect(bx,by,bw,bh);
  ctx.font='bold 14px monospace';ctx.textAlign='center';ctx.fillStyle='#fff';ctx.shadowColor=col;ctx.shadowBlur=8;
  ctx.fillText(boss.name,W/2,by-8);
 }
But top center may collide with waveMsg (H*0.32) no. Combo at cy=112 if boss? current drawCombo sets cy=(boss||waveState==='boss')?112:84. If boss bar at by=94, combo at 112 collision. Need adjust combo cy maybe 150 when boss. Or put boss bar at top y=70 and combo y=130. Let's adjust drawCombo: const cy = boss?140:84; Or if waveState==='boss' 140.
Sector text top right; okay.
Score left. Boss bar center top.
Need ensure boss bar not hidden by waveMsg? waveMsg at H*0.32 (~345) fine.
Taunt at H*0.32+40.
Add boss bar before overdrive maybe.
Need if boss.dying maybe still show bar? Could show until final? If dying, bar remains 0? Better if boss.dying===0 or dying but fade? Use if(boss && boss.dying===0). Good.

Also drawWaveMsg waveMsgT when boss name appears at H*0.32, boss bar top. fine.

Need check drawHUD uses waveState==='boss' but waveState variable exists. Good.

Other render path undefined:
- In drawCombo uses boss variable. ok.
- In drawHUD uses boss. ok.
- In drawBoss defeat text maybe font; ok.
- In updateFx uses tauntT now.
- In main frame, sectorT variable for upgrade; declared.
- In drawUpgrade uses sectorT for animation. ok.
- In victory button click uses startRun; ok.

Need maybe remove defeatShown, bossDefeatMsg? not necessary. But check no undefined:
bossDefeatMsg declared but unused. defeatShown unused. clearPts unused. maxCombo used. runTime used.
No other.

Need ensure no syntax errors from modifications.

Let's reconstruct final file fully. Need include all previous code with changes. Since user asks complete updated file. Need ensure no explanation. Use ```html.

Let's write final code carefully.

Potential improvements:
- In drawBoss shape, for boss.id 0 wings use ctx.scale(sgn,1), but after ctx.save/restore inside. okay.
- If boss.dying, ctx.globalAlpha fade. At final fade 0. Then white flash circle separate. Good.
- Shards: Need boss.shards length maybe 0 if not initialized? spawnBoss sets [], init when dying. In updateBoss dying loops over boss.shards; if empty fine.
- In updateBoss when hp<=0 set boss.dying=1; initBossShards(boss);
But in updateBoss hp decremented in updateBullets. In updateBoss at start if boss.dying>0 handle. When bullet kills, sets dying=1. Need init shards there too. Could in updateBullets when boss.hp<=0: boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;initBossShards(boss); Same for overdrive.
Currently updateBullets: if(boss.hp<=0){boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;} Add initBossShards(boss).
In unleashOverdrive: if(boss.hp<=0){boss.hp=0;boss.dying=1;boss.dieT=0;boss.dieBoom=0;} Add initBossShards(boss).
In spawnBoss set shards empty.
Need define initBossShards before use. Place near spawnBoss.

- In updateBoss dying, boss.shakeX random every frame; if dt=0 paused? state playing and paused dt=0, but updateBoss not called if paused? main: if paused dt=0, but still calls updateWaves(dt)? Actually in state playing if paused dt=0 but code still calls updateWaves(0), updateEnemies(0), updateBoss(0)? In main:
 if(paused){dt=0;} else {... dt=rdt*timeScale; runTime+=dt; updatePlayer(dt); ...}
It does NOT call updates when paused? Wait code:
if(state==='playing'){
 if(paused){dt=0;}
 else { ... updatePlayer(dt); updateWaves(dt); ... }
 updateFx(dt);
}
So no updateBoss when paused. Good.
But render drawBoss uses shakeX random only updated in updateBoss; when paused static. okay.

- In drawEntities, if state gameover, it draws enemies/boss? state gameover after player death, boss maybe. It draws drawEntities including boss. okay. updateFx slows.

- In gameOver, musicOn=false. boss may exist but state gameover. drawBoss no update, okay.

- In victory, boss null.

- In drawBoss, when boss.dying>0 and boss.dieT > 1.0 fade. Use const fade = boss.dieT>1.0 ? Math.max(0,1-(boss.dieT-1.0)/0.4) : 1; At 1.4 fade=0. Good.

- White flash circle radius maybe 160. Use ctx.globalAlpha? We set globalCompositeOperation lighter and fill with alpha based on sin. It will be additive. Good.

- Shards colors: boss.shards[].max set. Use sh.max for alpha: const a=Math.min(1,sh.life/(sh.max*0.4)); If sh.life > max*0.4 then a 1. Good.

- Shards absolute positions: initialized relative to boss center but boss moves? Boss during dying x stays (updateBoss doesn't change x in dying). Good. If boss.x changed? no.

- Boss defeat text: large glowing near boss. by-160 maybe above. If boss near top y ~150, text y -10 maybe on screen? boss.ty H*(0.16+sector*0.02): sector0 172 at 1080; by-160=12, okay. sector2 ty 205, text 45. Good. For small screen maybe above; okay.
Could use y-140.

- Boss health bar: drawHUD after score etc. Need set text alignment maybe. Add at beginning of drawHUD after save? Ensure not interfering with shadow. Let's insert after sector/lives maybe. Code:
 if(boss){
   const bw=Math.min(W*0.6,720),bh=18,bx=(W-bw)/2,by=86;
   ctx.fillStyle='rgba(0,0,0,0.55)';ctx.fillRect(bx,by,bw,bh);
   const frac=Math.max(0,boss.hp/boss.max);
   const col=frac>0.5?'#76B900':(frac>0.25?'#ff8a00':'#ff2d95');
   ctx.fillStyle=col;ctx.shadowColor=col;ctx.shadowBlur=16;
   ctx.fillRect(bx,by,bw*frac,bh);
   ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,0.35)';ctx.lineWidth=1;ctx.strokeRect(bx,by,bw,bh);
   ctx.font='bold 14px monospace';ctx.textAlign='center';ctx.fillStyle='#fff';ctx.shadowColor=col;ctx.shadowBlur=8;
   ctx.fillText(boss.name,W/2,by-8);
   ctx.shadowBlur=0;
 }
Then continue. But if boss bar at by=86, lives at y=80 left, okay.
Combo cy adjust to 150 if boss. drawCombo:
 const isBoss=(boss||waveState==='boss');
 const cy=isBoss?150:84;
Need boss bar name at 78, bar 86-104, combo text at 150. Good.

- drawWaveMsg waveMsgT when boss name top center at H*0.32; boss bar name top. fine.

- In drawHUD overdrive at H-30, no conflict.

- In updateFx, waveMsgT and tauntT decrement. But tauntT should maybe not decrement in title? updateFx not called title except? main title only titleT, no updateFx. okay.

- In resetGame, waveMsgT=0? set waveMsg='';waveMsgT=0; taunt='';tauntT=0.

- In startRun, resetGame, state intro. Good.

- In enterSector, waveState='inter' etc.

- In beginWave boss, set tauntT=3.

- In drawWaveMsg, if(tauntT>0&&boss){...} alpha Math.min(1,tauntT). If tauntT >1? min. Good.

- In drawBoss, if dying, draw defeat text. But if boss.dying and state gameover? boss only if player died during boss? possible. Still okay.

- In drawUpgrade cards: need hoverCard detection uses old rects? Mousemove uses upgradeCardRects. okay.
- In chooseCard, after choose, enterSector. state changes. Good.
- In upgrade card animation, sectorT starts 0 in state upgrade. Good.
- In drawUpgrade, const rects=upgradeCardRects(); for each r. If upgradeCards length 3. Good.
- wrapText uses ctx.fillStyle? It uses current fillStyle, set before. Good.
- In drawUpgradeIcon scale: for kind hull uses shipPath(1.0) inside scaled ctx. Good.
- For rapid icon, scale. Good.

Need ensure no variable name conflicts:
- In drawBoss, use const fl; in original shape boss.id 2 uses ctx.fillStyle etc. ok.
- In initBossShards, variable sp maybe conflicts? local.
- In updateBoss, for shards, use for(const sh of boss.shards). ok.

Let's produce final code. Need be very careful to not omit closing braces.

I will write full file from scratch based on prior, incorporating changes. Ensure all functions. Let's draft.

One concern: In drawBoss, original code has if(boss.id===0) ... else if. We need include ctx.globalAlpha fade. But inside boss.id 2 it sets ctx.globalAlpha=0.5 then 1; if fade <1, it will be overridden. Could multiply? For simplicity, if dying, the shape may flash full alpha due inner globalAlpha resets. But final fade not critical. Could avoid globalAlpha fade inside by not using ctx.globalAlpha for shape? We can set ctx.globalAlpha=fade before, but inner boss.id 2 sets ctx.globalAlpha=0.5 and 1, losing fade. Not a big deal; shape disappears at final bigBoom. But to make break apart, maybe okay. Could set fade via ctx.globalAlpha and in boss.id 2 use ctx.globalAlpha=0.5*fade? But not necessary. The white flash and shards suffice. To be safe, we can after drawing shape set ctx.globalAlpha=1. The original shape will not fade for sector3 due inner alpha reset, but it will be obscured by flash/shards and final explosion. Could be okay. But user complained stays whole and still; now shakes, flashes, shards. Even if alpha not fade, at 1.4 vanishes with explosion. Good.

Potential bug: In drawBoss, for boss.id===2, it sets ctx.fillStyle='#fff'; ctx.shadowColor='#fff'; etc. Then after shape, ctx.restore. ok.

Need include initBossShards before updateBoss? Function hoisting: function declarations hoisted, okay.

Check audio: mTempo global. updateMusic uses currentTrack. okay.

Check resize: player.upg initial before resize? At bottom player.upg set. resize uses player? It sets player.y if player exists. player object exists. ok.

Check localStorage best. ok.

Let's verify variable tauntT in resetGame. yes.

Potential issue: In main frame for state upgrade, we don't update gridScroll? We update before. ok.

Potential issue: In drawUpgrade, if state upgrade, background uses drawBackground with current sector palette? currentSector remains old sector until enterSector after choice. Good.

Potential issue: In sectorclear, drawBackground no entities. okay.

Potential issue: In sectorclear, updateFx called rdt*0.6, tauntT may fade. ok.

Potential issue: In drawSectorClear, uses acc variable? It defines acc, acc2. ok.

Potential issue: In drawVictory, victoryBtnRects returns buttons with act closures. ok.

Potential issue: In onPointer for victory, if click not button, nothing. ok.

Potential issue: In keydown for space during upgrade? It doesn't choose. ok.

Potential issue: In chooseCard, if maxed returns, but user might click maxed card repeatedly. ok.

Potential issue: upgLevel for hull uses counts, but if resetGame counts 0. good.

Potential issue: In drawUpgrade pips, max+1 pips. For max 5, 6 pips. total width maybe pw*6+gap*5 = 30*6+8*5=220, card width 384, okay. For small card width 150, 220 too wide. Need adaptive pips: pw=Math.max(8,Math.min(30,(r.w-60)/(max*2+1)))? Simpler: const pw=Math.max(10,Math.min(30,(r.w-60)/( (max+1)*2 ))), gap=Math.max(4,pw*0.25); total pw*(max+1)+gap*max. For max5, (r.w-60)/12; for r.w 384 ->27, gap6.75 total 214. For r.w 150 ->8.3? max 10? total 10*6+4*5=80. okay. Use:
 const pw=Math.max(8,Math.min(30,(r.w-70)/((max+1)*1.8)));
 const gap=Math.max(4,Math.round(pw*0.3));
 const tot=pw*(max+1)+gap*max; let px=...;
Good.

Potential issue: drawUpgradeIcon scale for small card maybe <1. ok.

Potential issue: In drawUpgrade, description y and wrapText may exceed card if long desc. Descriptions short. ok.

Potential issue: In drawHUD boss bar, if boss is null but waveState boss? no.

Potential issue: In updateBullets, when armored enemy hit, if e.hp<=0 killEnemy; else flash. ok.

Potential issue: In killEnemy, for splitter spawns children, but if splitter killed by overdrive? Overdrive kills all enemies and adds pts, does not spawn splitter children. That's okay, overdrive maybe should not spawn. Fine.

Potential issue: In overdrive, it removes enemies without drop powerups. okay.

Potential issue: In updateWaves, if boss exists, updateBoss returns. But enemies may remain? When boss spawns, enemies cleared? enterSector clears, beginWave boss spawn without clearing enemies? If previous wave cleared, no enemies. If somehow, okay. But boss phase may have leftover? fine.

Potential issue: In updateBoss, boss.x movement uses boss.t; if dying, boss.t not updated? In updateBoss, first if dying then no boss.t+=dt? Current code: if(!boss)return; boss.t+=dt; if(boss.dying>0){... return;} So t updates during dying, shape fl uses t. ok.

Potential issue: In updateBoss dying, if boss.dieT>1.4, bigBoom, score, powerups, boss=null. If currentSector===2 victory. Good.

Potential issue: In victory, musicOn=false. ok.

Potential issue: In resetGame, mStep=0; if AC mNext set. ok.

Need ensure no external font? uses monospace. ok.

Now final answer code only. Need no explanation. Ensure code block. Let's compose.
