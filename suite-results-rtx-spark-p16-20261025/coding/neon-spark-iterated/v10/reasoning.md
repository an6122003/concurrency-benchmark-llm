The user wants me to fix the mobile upgrade cards specifically. Let me look at the current code for the stacked (mobile) card rendering.

Current mobile card code:
```js
if(stacked){
  const pad=12;
  const iconSize=Math.min(52,r.h-16);
  const iconCX=r.x+pad+iconSize/2;
  const iconCY=yy+r.h/2;
  drawUpgradeIcon(c.kind,iconCX,iconCY,c.color,iconSize/72);
  const textX=r.x+pad+iconSize+10;
  const textW=r.x+r.w-pad-textX;
  ctx.textAlign='left';
  ctx.font='bold 14px monospace';
  ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=6;
  ctx.fillText(c.label,textX,yy+pad+14);
  ctx.shadowBlur=0;
  const pw=Math.min(14,Math.floor(textW/max)-4),gap=3;
  let px=textX;
  const pipY=yy+pad+24;
  for(let k=0;k<max;k++){
    ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
    if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=4;}else ctx.shadowBlur=0;
    ctx.fillRect(px,pipY,pw,5);
    px+=pw+gap;
  }
  ctx.shadowBlur=0;
  const descFs=11;
  const lh=14;
  ctx.font=descFs+'px monospace';
  ctx.fillStyle='rgba(255,255,255,0.6)';
  const dlines=wrapLines(c.desc,descFs,textW);
  const dStartY=pipY+18;
  for(let i=0;i<dlines.length;i++){
    const ly=dStartY+i*lh;
    if(ly<yy+r.h-4)ctx.fillText(dlines[i],textX,ly);
  }
}
```

Requirements:
1. Make each card only as tall as its content (~120px) — I need to change the card height calculation in `upgradeCardRects` for the narrow case.
2. Vertically center the icon and the text block together.
3. Draw the icon a little larger.
4. Show "LV x / y" between the title and the bars (like desktop).
5. Keep desktop cards exactly as they are.

Let me look at `upgradeCardRects`:
```js
function upgradeCardRects(){
  const isNarrow=W<640;
  if(isNarrow){
    const gap=12,side=20;
    const cw=W-side*2;
    const maxCh=Math.round(H*0.205);
    const ch=Math.max(78,Math.min(172,maxCh));
    let y=H*0.30;
    const totalH=ch*3+gap*2;
    if(y+totalH>H-56)y=H-56-totalH;
    const out=[];
    for(let i=0;i<3;i++)out.push({x:side,y:y+i*(ch+gap),w:cw,h:ch,i});
    return out;
  }
  ...
}
```

So for the narrow case, I should set ch to ~120 (content height). Let me set it to a fixed reasonable height like 120. But I should be careful about total height fitting. 3*120 + 2*12 = 384. That's fine.

Let me change `ch` to `Math.min(120, ...)` — actually just use a value around 120. The user says "about 120 pixels". Let me use a fixed 120 but clamp so total fits. Let me compute totalH and if it doesn't fit, reduce.

Actually, let me keep it simple: ch=120, but ensure totalH fits. totalH=120*3+gap*2=384. On a phone that's fine. Let me set ch to a value that keeps total on screen.

Let me rewrite the mobile branch of upgradeCardRects:
```js
if(isNarrow){
  const gap=12,side=20;
  const cw=W-side*2;
  const ch=120;
  let y=H*0.30;
  const totalH=ch*3+gap*2;
  if(y+totalH>H-56)y=H-56-totalH;
  const out=[];
  for(let i=0;i<3;i++)out.push({x:side,y:y+i*(ch+gap),w:cw,h:ch,i});
  return out;
}
```

Now the drawing. I need to vertically center icon + text block. Let me compute the text block height and icon height, then center the whole thing.

Layout in the mobile card:
- Icon on left
- Text block on right: title (top), "LV x / y" (middle), bars, description

Let me define:
- pad = 14
- iconSize = 64 (a little larger than 52)
- Text block:
  - title font bold 14
  - LV label font bold 12
  - bars
  - description font 11, lh 14, possibly 2 lines

Let me measure the text block height:
- title height ~ 14 (cap)
- gap
- LV label ~ 12
- gap
- bars ~ 5 (height)
- gap
- description: dlines.length * 14

Let me build a vertical layout. I'll compute the total content height, then find the top Y to center within the card.

Let me define:
```
const pad=14;
const iconSize=64;
// text block
const titleFs=14, lvFs=12, descFs=11, descLh=14;
// measure
const textX = r.x+pad+iconSize+10;
const textW = r.x+r.w-pad-textX;
ctx.font=descFs+'px monospace';
const dlines=wrapLines(c.desc,descFs,textW);
const descH=dlines.length*descLh;

// vertical positions within text block (relative)
const g1=6;  // between title and lv
const g2=6;  // between lv and bars
const g3=8;  // between bars and desc
const barH=6;
const titleH=titleFs;
const lvH=lvFs;
const blockH=titleH+g1+lvH+g2+barH+g3+descH;

// center vertically: total content = max(iconSize, blockH)
const contentH=Math.max(iconSize,blockH);
const topY=yy+(r.h-contentH)/2;

// icon center
const iconCX=r.x+pad+iconSize/2;
const iconCY=yy+r.h/2;  // center in card

// text block top
const blockTop=topY+(contentH-blockH)/2;
```

Then:
- title baseline at blockTop + titleH (baseline ~ blockTop + titleFs*0.8). Let me just use baselines.

Let me use baseline positions:
- titleBaseline = blockTop + titleH (approx). Actually for monospace, cap height ~ fs. Let me set titleBaseline = blockTop + titleFs.

Hmm, let me just lay out with explicit y values:
```
let ty=blockTop+titleFs;              // title baseline
// lv baseline
let lvY=ty+g1+lvFs;
// bars
const barY=lvY+g2+4;
// desc
let dY=barY+barH+g3+descFs;
```

Wait, I need consistent spacing. Let me just do:
- title baseline: yTitle
- lv baseline: yTitle + 18
- bars top: yLv + 6
- desc first baseline: barsTop + barH + 12

Let me compute blockH from these to center properly.

Actually simpler: compute the blockH as the sum, then place from blockTop.

Let me define spacing constants and compute:
```
const titleFs=14, lvFs=12, barH=6, descFs=11, descLh=14;
const sp1=4, sp2=6, sp3=6;  // small spacings
// block content:
// title occupies ~titleFs (from baseline, but let's treat as line box)
```

I'll treat each element with a "line box" height:
- title line box: titleFs
- sp1
- lv line box: lvFs
- sp2
- barH
- sp3
- desc line boxes: descH = dlines.length*descLh

blockH = titleFs + sp1 + lvFs + sp2 + barH + sp3 + descH

Baselines (approx, baseline near bottom of line box):
- titleBaseline = blockTop + titleFs - 2
- lvBaseline = titleBaseline + sp1 + lvFs - 2
- barsTop = lvBaseline + sp2 (roughly). Let me set barsTop = blockTop + titleFs + sp1 + lvFs + sp2
- descBaseline0 = blockTop + titleFs + sp1 + lvFs + sp2 + barH + sp3 + descFs - 2

Let me just compute with cumulative offsets.

Let me write it cleanly:
```
const pad=14;
const iconSize=66;
const titleFs=15, lvFs=12, descFs=11, descLh=15, barH=6;
const sp1=5, sp2=5, sp3=7;
const textX=r.x+pad+iconSize+12;
const textW=Math.max(40, r.x+r.w-pad-textX);
ctx.font=descFs+'px monospace';
const dlines=wrapLines(c.desc,descFs,textW);
const descH=dlines.length*descLh;
const blockH=titleFs+sp1+lvFs+sp2+barH+sp3+descH;
const contentH=Math.max(iconSize,blockH);
const topY=yy+(r.h-contentH)/2;
const blockTop=topY+(contentH-blockH)/2;

// icon
const iconCX=r.x+pad+iconSize/2;
const iconCY=yy+r.h/2;
drawUpgradeIcon(c.kind,iconCX,iconCY,c.color,iconSize/72);

// title
let y=blockTop+titleFs-2;
ctx.textAlign='left';
ctx.font='bold '+titleFs+'px monospace';
ctx.fillStyle=c.color;ctx.shadowColor=c.color;ctx.shadowBlur=6;
ctx.fillText(c.label,textX,y);
ctx.shadowBlur=0;

// LV label
y+=sp1+lvFs-2;
ctx.font='bold '+lvFs+'px monospace';
ctx.fillStyle='rgba(255,255,255,0.75)';
ctx.fillText('LV '+lv+' / '+max,textX,y);

// bars
const barTop=blockTop+titleFs+sp1+lvFs+sp2;
const pw=Math.min(16,Math.floor(textW/max)-4),gap=4;
let px=textX;
for(let k=0;k<max;k++){
  ctx.fillStyle=k<lv?c.color:'rgba(255,255,255,0.18)';
  if(k<lv){ctx.shadowColor=c.color;ctx.shadowBlur=4;}else ctx.shadowBlur=0;
  ctx.fillRect(px,barTop,pw,barH);
  px+=pw+gap;
}
ctx.shadowBlur=0;

// desc
ctx.font=descFs+'px monospace';
ctx.fillStyle='rgba(255,255,255,0.6)';
let dy=blockTop+titleFs+sp1+lvFs+sp2+barH+sp3+descFs-2;
for(let i=0;i<dlines.length;i++){
  ctx.fillText(dlines[i],textX,dy+i*descLh);
}
```

That should be good. The card is ~120px tall, content centered vertically, icon larger (66 vs 52), LV label added between title and bars.

Let me double check blockH fits within 120 for 2-line desc:
titleFs15 + sp1 5 + lvFs 12 + sp2 5 + barH 6 + sp3 7 + descH (2*15=30) = 80. Good, less than 120. For 1 line: 15+5+12+5+6+7+15=65. Icon is 66. contentH=66. Fine.

Wait, for 2-line, blockH=80 > iconSize 66, so contentH=80, centered. Good.

Now I need to make sure the bars fit width: pw=Math.min(16, floor(textW/max)-4). For max=3, textW maybe ~200, floor(200/3)=66, -4=62, min(16,62)=16. Fine. gap 4, total 16*3+8=56. Fits.

Now the `drawUpgradeIcon` scale uses iconSize/72, so 66/72 ~ 0.92. Icons drawn at base size ~72 units? Let me check the icon drawing — it uses coordinates around ±17 max (shipPath uses 20, hull uses scale 1.0 → ±17). Actually shipPath(s) with s=1 → ±17, ±20. So base icon is ~40 units wide. With scale 0.92, ~37. Hmm that's small relative to 66 box. But the user said "draw the icon a little larger". Previously iconSize was 52, now 66, so scale went from 52/72=0.72 to 66/72=0.92. That's larger. Good enough. The icon content max radius ~17-20, scaled by 0.92 → ~16-18, diameter ~32-36 within a 66 box. There's padding but it's centered. Acceptable. Actually to make it look bigger, I could use a smaller denominator. Let me use iconSize/80? No, that'd make it smaller. Let me use iconSize/70 to make slightly bigger. Base 20 units → 20*(66/70)=18.8, diameter ~37. Fine. I'll keep /72 for consistency but maybe /70. Let me use /72 to not overthink. Actually the original used iconSize/72 with iconSize 52 giving scale 0.72 → 20*0.72=14.4 diameter 28.8 in a 52 box. Now 66 box with scale 0.92 → diameter 36.8. So relatively it's a bit smaller within its box but absolutely bigger. The user just wants "a little larger" absolute. It's fine.

Hmm, but to make it look nicely sized in the box, maybe use /60. 20*(66/60)=22, diameter 44 in 66 box. That looks fuller. But desktop uses iconSize/72 with iconSize 92 → scale 1.28 → 20*1.28=25.6, diameter 51 in 92 box. So desktop icons are ~51 in 92 box, ratio ~0.55. For mobile to match ratio: 66*0.55=36 diameter → 18 radius → scale 0.9. So /72 (0.92) is about right, slightly bigger. Good, keep /72.

Now let me also verify I only change the mobile branch and the narrow branch of upgradeCardRects. Desktop stays.

Let me write the full file with these edits. I'll replace the two relevant sections.

Let me now produce the complete file. I need to copy the entire original and make the two edits. Let me be careful.

Edit 1: upgradeCardRects narrow branch:
Change:
```
    const maxCh=Math.round(H*0.205);
    const ch=Math.max(78,Math.min(172,maxCh));
    let y=H*0.30;
    const totalH=ch*3+gap*2;
    if(y+totalH>H-56)y=H-56-totalH;
```
to:
```
    const ch=120;
    let y=H*0.30;
    const totalH=ch*3+gap*2;
    if(y+totalH>H-56)y=H-56-totalH;
```

Edit 2: the stacked drawing block. Replace the whole `if(stacked){ ... }` block.

Let me make sure the new block references r.x, r.w, r.h, yy, c, lv, max.

Now let me write it all out.

I'll reproduce the whole file exactly as before with these two changes.
