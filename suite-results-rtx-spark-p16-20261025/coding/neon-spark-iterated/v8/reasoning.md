Let me analyze the three issues carefully:

1. **Intro text on monitor**: The text uses `margin=Math.round(Math.min(24,W*0.06))` and `ctx.textAlign='left'` with `x=margin`. This puts it at the far left. I need to center it in a column of at most ~900px wide.

2. **Intro text on phone**: The story text block starts at `H*0.42-blockH/2` which could overlap the header at `H*0.28`. I need to always start below the header line.

3. **Upgrade cards on phone (narrow)**: Currently uses icon-on-top layout with `titleY=yy+pad+iconSize+12`, then title, level text, pips, and description stacked. On narrow cards, description overflows. Need to switch to icon-on-left, text-on-right layout. Also the hint at `H*0.88` overlaps the third card. Need to put hint below the last card and say "TAP A CARD" on touch.

Let me rework:

**Fix 1 & 2 (drawIntro):**

Current code:
```
const margin=Math.round(Math.min(24,W*0.06));
const maxW=W-margin*2;
const fs=Math.min(W*0.055,26);
```

Change to:
```
const maxW=Math.min(900, W-48);
const marginX=(W-maxW)/2;
const fs=Math.min(W*0.055,26);
```

Then for the vertical position, I need to start below the header. The header is at `H*0.28`, the decorative line at `H*0.31`. So I should start text at something like `H*0.35` (below the line) plus a bit.

Currently:
```
let yTop=H*0.42-blockH/2;
```

Change to start at a fixed top that's below the header:
```
let yTop=Math.max(H*0.36, H*0.42 - blockH/2);
```

Actually the requirement says "always start the story text below the header line" — the header line is at `H*0.31`. So the top of the text block should be at least, say, `H*0.31 + 10` or `H*0.34`.

Let me think about this: the block is `blockH` tall, and we want it to start below `H*0.31`. So:
```
const textTop = H*0.34; // always below header
let yTop = Math.min(textTop, H*0.42 - blockH/2); // hmm no
```

Actually, we want:
- On phone (small H): the block might be tall, so we can't center it at `H*0.42-blockH/2` because that puts it above `H*0.31`.
- Solution: `let yTop = Math.max(H*0.34, H*0.42 - blockH/2);`

Wait that's the opposite — if blockH is large, `H*0.42-blockH/2` will be small (like above the header). We want to ensure yTop >= H*0.34 (below the header line).

So: `let yTop = Math.max(H*0.34, H*0.42 - blockH/2);`

That should work. On phone where blockH is large, yTop = H*0.34. On desktop where blockH is small, yTop = H*0.42 - blockH/2 which is around H*0.38.

Actually wait — on phone H*0.34 might be too low? No, H*0.34 means 34% from top. The header is at 28%, line at 31%. So 34% is below that. That's fine.

For the text alignment, change to center within the column:
```
ctx.textAlign='left';
```
→ keep left-aligned but within the centered column. Or we could do center-aligned. The user says "Put it in a centered column" — so the column is centered, text can be left-aligned within it.

So: `ctx.fillText(line, marginX, yTop+lineIdx*lineH+fs*0.8);`

**Fix 3 (drawUpgrade):**

For narrow screens (W<640), switch to horizontal layout:
- Icon on left
- Text on right (title, level pips, description)

For the hint, place it below the last card instead of at a fixed H*0.88.

Let me rewrite the narrow branch:

```javascript
if(isNarrow){
  // horizontal layout
  const pad=16;
  const iconSize=52;
  const titleFs=18;
  const descFs=12;
  const iconCX=r.x+pad+iconSize/2;
  const iconCY=yy+r.h/2;
  const textX=r.x+pad+iconSize+8;
  const textW=r.w-pad*2-iconSize-8;
  
  drawUpgradeIcon(c.kind,iconCX,iconCY,c.color,iconSize/72);
  
  ctx.textAlign='left';
  ctx.font='bold '+titleFs+'px monospace';
  ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=8;
  ctx.fillText(c.label,textX,yy+pad+10);
  ctx.shadowBlur=0;
  
  // level pips
  const lv=upgLevel(c.kind),max=upgMax(c.kind);
  const pw=18,gap=4;
  let px=textX;
  for(let k=0;k<max;k++){
    ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
    if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=6;}else ctx.shadowBlur=0;
    ctx.fillRect(px,yy+pad+18,pw,6);
    px+=pw+gap;
  }
  ctx.shadowBlur=0;
  
  // description wrapped
  ctx.font=descFs+'px monospace';
  ctx.fillStyle='rgba(255,255,255,0.6)';
  const dlines=wrapLines(c.desc,descFs,textW);
  const dStartY=yy+pad+34;
  for(let i=0;i<dlines.length;i++){
    ctx.fillText(dlines[i],textX,dStartY+i*16);
  }
}
```

And for the hint:
```
const hintY = isNarrow ? (lastCardBottom + 16) : H*0.88;
const hintText = isTouch ? 'TAP A CARD' : 'CLICK A CARD  ·  OR PRESS 1 / 2 / 3';
```

Let me also think about the narrow layout more carefully. The card height is `ch=Math.max(78,Math.min(172,maxCh))` where `maxCh=Math.round(H*0.205)`. On a phone with H~800, that's ch~164. With pad=16, iconSize=52, the remaining vertical space is 164-32=132. The text content: title at pad+10=26, pips at pad+18=34, description starts at pad+34=50. With 1-2 lines of desc at 16px line height, we need ~50+32=82px, well within 132. Good.

Now let me put together the complete file with these changes. I need to be careful to only change what's needed.

Let me re-read the original code for drawIntro to identify exactly what to change:

```javascript
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
    ctx.globalCompositeOperation='source-over';
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

  // Typewriter text wrapped to screen width
  const margin=Math.round(Math.min(24,W*0.06));
  const maxW=W-margin*2;
  const fs=Math.min(W*0.055,26);
  ctx.font=fs+'px monospace';
  const lineH=fs*1.5;
  // Pre-compute wrapped lines for each source line
  const wrappedAll=[];
  for(const line of introLines){
    const words=line.split(' ');
    const lines=[];let cur='';
    for(const wd of words){
      const test=cur?cur+' '+wd:wd;
      if(ctx.measureText(test).width>maxW&&cur){lines.push(cur);cur=wd;}
      else cur=test;
    }
    if(cur)lines.push(cur);
    wrappedAll.push(lines);
  }
  const totalLines=wrappedAll.reduce((s,a)=>s+a.length,0);
  const blockH=totalLines*lineH;
  let remaining=Math.floor(t*28);
  let yTop=H*0.42-blockH/2;
  ctx.textAlign='left';
  let lineIdx=0;
  for(const lines of wrappedAll){
    for(let i=0;i<lines.length;i++){
      const line=lines[i];
      let take=line.length;
      if(remaining>=take){
        ctx.shadowColor='#00e5ff';ctx.shadowBlur=8;ctx.fillStyle='#cfe8ff';
        ctx.fillText(line,margin,yTop+lineIdx*lineH+fs*0.8);
        remaining-=take;
      }else{
        ctx.shadowColor='#00e5ff';ctx.shadowBlur=8;ctx.fillStyle='#cfe8ff';
        ctx.fillText(line.slice(0,remaining),margin,yTop+lineIdx*lineH+fs*0.8);
        if(Math.floor(time*3)%2===0){const w=ctx.measureText(line.slice(0,remaining)).width;ctx.fillRect(margin+w+4,yTop+lineIdx*lineH-2,12,fs);}
        remaining=0;
      }
      lineIdx++;
    }
  }
```

Changes needed:
- `const margin=Math.round(Math.min(24,W*0.06));` → `const maxW=Math.min(900,W-48);const marginX=(W-maxW)/2;`
- `const maxW=W-margin*2;` → remove (already defined above)
- `let yTop=H*0.42-blockH/2;` → `let yTop=Math.max(H*0.35,H*0.42-blockH/2);`
- All `ctx.fillText(line,margin,...)` → `ctx.fillText(line,marginX,...)`
- `ctx.fillRect(margin+w+4,...)` → `ctx.fillRect(marginX+w+4,...)`

Now for drawUpgrade, I need to replace the narrow branch. Let me look at the current code:

```javascript
function drawUpgrade(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.68)';ctx.fillRect(0,0,W,H);
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.06,38)+'px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=24;ctx.fillStyle='#76B900';
  ctx.fillText('CHOOSE AN UPGRADE',W/2,H*0.24);
  const rects=upgradeCardRects();
  for(const r of rects){
    const c=upgradeCards[r.i];
    const delay=r.i*0.15;
    const animT=Math.min(1,Math.max(0,(sectorT-delay)/0.4));
    const ease=easeOutBack(animT);
    const isHover=hoverCard===r.i;
    const lift=isHover?14:0;
    const yy=r.y+ (1-ease)*90 - lift;
    ctx.save();
    ctx.globalAlpha=Math.min(1,animT*1.5);
    ctx.fillStyle=isHover?'rgba(0,40,30,0.95)':'rgba(0,20,30,0.85)';
    ctx.fillRect(r.x,yy,r.w,r.h);
    const glow=isHover?28:14;
    ctx.strokeStyle=c.color;ctx.lineWidth=isHover?3:2;ctx.shadowColor=c.color;ctx.shadowBlur=glow;
    ctx.strokeRect(r.x,yy,r.w,r.h);
    ctx.shadowBlur=0;

    // Layout metrics adapt to card size
    const isWide=r.w>200;
    const pad=isWide?34:22;
    const iconSize=isWide?92:64;
    const titleFs=isWide?26:20;
    const descFs=isWide?15:13;
    const lh=descFs*1.35;

    // icon centered at top
    const iconScale=(iconSize/72);
    const iconCY=yy+pad+iconSize/2;
    drawUpgradeIcon(c.kind,r.x+r.w/2,iconCY,c.color,iconScale);

    // title
    const titleY=yy+pad+iconSize+12;
    ctx.font='bold '+titleFs+'px monospace';
    ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=8;
    ctx.textAlign='center';
    ctx.fillText(c.label,r.x+r.w/2,titleY);
    ctx.shadowBlur=0;

    // level text
    const lv=upgLevel(c.kind),max=upgMax(c.kind);
    const lvY=titleY+18;
    ctx.font='bold 13px monospace';
    ctx.fillStyle='rgba(255,255,255,0.75)';ctx.shadowBlur=0;
    ctx.fillText('LV '+lv+' / '+max,r.x+r.w/2,lvY);

    // level pips
    const pw=isWide?30:22;
    const gap=Math.max(4,Math.round(pw*0.3));
    const tot=pw*max+gap*(max-1);
    let px=r.x+r.w/2-tot/2;
    const pipY=lvY+10;
    for(let k=0;k<max;k++){
      ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
      if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=6;}else ctx.shadowBlur=0;
      ctx.fillRect(px,pipY,pw,7);
      px+=pw+gap;
    }
    ctx.shadowBlur=0;

    // description wrapped
    const descStartY=pipY+20;
    ctx.font=descFs+'px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';
    const dlines=wrapLines(c.desc,descFs,r.w-pad*2);
    for(let i=0;i<dlines.length;i++){
      ctx.fillText(dlines[i],r.x+r.w/2,descStartY+i*lh);
    }
    ctx.restore();
  }
  ctx.font='12px monospace';ctx.fillStyle='rgba(255,255,255,0.5)';ctx.textAlign='center';
  ctx.fillText('CLICK A CARD  ·  OR PRESS 1 / 2 / 3',W/2,H*0.88);
  ctx.restore();
}
```

I need to:
1. For narrow cards (r.w<=200), use horizontal layout: icon left, text right
2. Put the hint below the last card
3. Say "TAP A CARD" on touch

Let me restructure:

```javascript
function drawUpgrade(){
  ctx.save();
  ctx.fillStyle='rgba(2,0,10,0.68)';ctx.fillRect(0,0,W,H);
  ctx.textAlign='center';
  ctx.font='bold '+Math.min(W*0.06,38)+'px monospace';
  ctx.shadowColor='#76B900';ctx.shadowBlur=24;ctx.fillStyle='#76B900';
  ctx.fillText('CHOOSE AN UPGRADE',W/2,H*0.24);
  const rects=upgradeCardRects();
  const isNarrow=rects[0].w<200;
  for(const r of rects){
    const c=upgradeCards[r.i];
    const delay=r.i*0.15;
    const animT=Math.min(1,Math.max(0,(sectorT-delay)/0.4));
    const ease=easeOutBack(animT);
    const isHover=hoverCard===r.i;
    const lift=isHover?14:0;
    const yy=r.y+ (1-ease)*90 - lift;
    ctx.save();
    ctx.globalAlpha=Math.min(1,animT*1.5);
    ctx.fillStyle=isHover?'rgba(0,40,30,0.95)':'rgba(0,20,30,0.85)';
    ctx.fillRect(r.x,yy,r.w,r.h);
    const glow=isHover?28:14;
    ctx.strokeStyle=c.color;ctx.lineWidth=isHover?3:2;ctx.shadowColor=c.color;ctx.shadowBlur=glow;
    ctx.strokeRect(r.x,yy,r.w,r.h);
    ctx.shadowBlur=0;

    const lv=upgLevel(c.kind),max=upgMax(c.kind);
    if(isNarrow){
      // Horizontal: icon left, text right
      const pad=14;
      const iconSize=48;
      const iconCX=r.x+pad+iconSize/2;
      const iconCY=yy+r.h/2;
      drawUpgradeIcon(c.kind,iconCX,iconCY,c.color,iconSize/72);
      const textX=r.x+pad+iconSize+10;
      const textW=r.w-pad*2-iconSize-10;
      ctx.textAlign='left';
      // Title
      ctx.font='bold 16px monospace';
      ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=8;
      ctx.fillText(c.label,textX,yy+pad+10);
      ctx.shadowBlur=0;
      // Pips
      const pw=16,gap=3;
      let px=textX;
      for(let k=0;k<max;k++){
        ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
        if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=6;}else ctx.shadowBlur=0;
        ctx.fillRect(px,yy+pad+20,pw,6);
        px+=pw+gap;
      }
      ctx.shadowBlur=0;
      // Description
      const descFs=11;
      const lh=15;
      ctx.font=descFs+'px monospace';
      ctx.fillStyle='rgba(255,255,255,0.6)';
      const dlines=wrapLines(c.desc,descFs,textW);
      const dStartY=yy+pad+36;
      for(let i=0;i<dlines.length;i++){
        ctx.fillText(dlines[i],textX,dStartY+i*lh);
      }
    }else{
      // Vertical: icon top center, text below (original wide layout)
      const pad=34;
      const iconSize=92;
      const titleFs=26;
      const descFs=15;
      const lh=descFs*1.35;
      const iconScale=(iconSize/72);
      const iconCY=yy+pad+iconSize/2;
      drawUpgradeIcon(c.kind,r.x+r.w/2,iconCY,c.color,iconScale);
      const titleY=yy+pad+iconSize+12;
      ctx.font='bold '+titleFs+'px monospace';
      ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=8;
      ctx.textAlign='center';
      ctx.fillText(c.label,r.x+r.w/2,titleY);
      ctx.shadowBlur=0;
      const lvY=titleY+18;
      ctx.font='bold 13px monospace';
      ctx.fillStyle='rgba(255,255,255,0.75)';ctx.shadowBlur=0;
      ctx.fillText('LV '+lv+' / '+max,r.x+r.w/2,lvY);
      const pw=30,gap=Math.max(4,Math.round(pw*0.3));
      const tot=pw*max+gap*(max-1);
      let px=r.x+r.w/2-tot/2;
      const pipY=lvY+10;
      for(let k=0;k<max;k++){
        ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
        if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=6;}else ctx.shadowBlur=0;
        ctx.fillRect(px,pipY,pw,7);
        px+=pw+gap;
      }
      ctx.shadowBlur=0;
      const descStartY=pipY+20;
      ctx.font=descFs+'px monospace';ctx.fillStyle='rgba(255,255,255,0.6)';
      const dlines=wrapLines(c.desc,descFs,r.w-pad*2);
      for(let i=0;i<dlines.length;i++){
        ctx.fillText(dlines[i],r.x+r.w/2,descStartY+i*lh);
      }
    }
    ctx.restore();
  }
  // Hint below last card
  const lastRect=rects[rects.length-1];
  const hintY=lastRect.y+lastRect.h+24;
  ctx.font='12px monospace';ctx.fillStyle='rgba(255,255,255,0.5)';ctx.textAlign='center';
  ctx.fillText(isTouch?'TAP A CARD':'CLICK A CARD  ·  OR PRESS 1 / 2 / 3',W/2,hintY);
  ctx.restore();
}
```

Wait, I need to check the narrow layout fits. With r.h being the card height (let's say 164 on phone):
- pad=14, so content area starts at yy+14
- Title at yy+14+10 = yy+24
- Pips at yy+14+20 = yy+34
- Description starts at yy+14+36 = yy+50
- With 2 lines of desc at lh=15: yy+50+15 = yy+65
- Total used: 65px from top, card is 164px tall. Plenty of room.

Actually wait, the description might wrap to 2 lines with textW. Let's check: textW = r.w - pad*2 - iconSize - 10 = (W-20) - 28 - 48 - 10. On a 375px phone: 355-28-48-10 = 269px. With 11px monospace, that's about 269/7 ≈ 38 chars per line. The descriptions are like "-20% fire cooldown" (18 chars), "+1 laser bolt" (13), "Gain a spare life" (17), "Shields last 60% longer" (23), "Pull power-ups to you" (21), "Overdrive charges faster" (24). All fit on one line. Good.

Now let me also double-check the intro fix. The `maxW` was previously `W-margin*2`. I'm changing it to `Math.min(900, W-48)`. The `marginX` becomes `(W-maxW)/2`.

For the yTop fix: `let yTop=Math.max(H*0.35,H*0.42-blockH/2);`

On a phone with H=700: H*0.35=245, H*0.42=294. If blockH=200 (4 lines × 26px), then H*0.42-blockH/2=294-100=194. So yTop=max(245,194)=245. Good, it starts below the header.

On a wide monitor H=1000: H*0.35=350, H*0.42=420. blockH might be 200. yTop=max(350,320)=350. Fine.

Actually wait, on desktop with the 900px max width, the lines might wrap less, so blockH might be smaller. Let's say 3 lines × 39px = 117. Then H*0.42-blockH/2=420-58=362. yTop=max(350,362)=362. Good.

I think this all works. Let me write the complete file now.
