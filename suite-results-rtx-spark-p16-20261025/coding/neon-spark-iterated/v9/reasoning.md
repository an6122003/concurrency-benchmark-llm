Let me address the three issues:

1. Audio error: `noiseBuf()` returns `nb` which is an AudioBuffer. But wait, the error says "Failed to convert value to 'AudioBuffer'". Let me look at the code:

```js
function noiseBuf(){
  if(nb)return nb;
  nb=AC.createBuffer(1,AC.sampleRate,AC.sampleRate);
  const d=nb.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;
  return d;  // BUG: returns the data array, not the buffer!
}
```

The function returns `d` (the channel data array) instead of `nb` (the AudioBuffer). So `s.buffer=noiseBuf()` assigns an `Float32Array` to `buffer`, which fails.

Fix: return `nb` instead of `d`.

2. Phone upgrade cards layout: Currently the code has an `isNarrow` check:
```js
if(isNarrow){
    // Horizontal layout: icon left, text right
```

But `isNarrow` is `rects[0].w < 200` which checks width. Let me look at the phone layout logic. The phone layout in `upgradeCardRects()` gives each card a height of `Math.max(78, Math.min(172, Math.round(H*0.205)))`. On a phone, H might be around 700-900, so 20% is 140-180px. The card width on a phone would be `W - side*2` where side is 20, so on a 375px phone that's 335px. That's >200, so `isNarrow` is false and it uses the vertical layout which spills.

Actually let me re-read: `isNarrow=W<640` in `upgradeCardRects()`. But in `drawUpgrade`, `isNarrow=rects[0].w<200`.

So on a phone with W=375, `isNarrow` in `upgradeCardRects` is true, cards are stacked vertically with `cw=W-40=335` and `ch=max(78, min(172, H*0.205))`. If H=800, ch=164.

In `drawUpgrade`, `isNarrow=rects[0].w<200`. Since cw=335 > 200, `isNarrow` is false. So it uses the vertical layout (icon on top, text below) which spills out.

Fix: The user wants the phone layout to use the horizontal layout (icon left, text right). I should change the check from `rects[0].w<200` to something that correctly identifies the phone layout. Since the phone layout is determined by `W<640` in `upgradeCardRects()`, I should use the same check.

Actually wait - looking at the phone layout: cards are stacked vertically (one per row). The width is `W-40`. So the card is wide but short. The horizontal layout (icon left, text right) makes more sense here because the card is short vertically.

I should change `isNarrow=rects[0].w<200` to `isNarrow=W<640` or check if the cards are stacked (h < w).

Actually, the simplest fix: just check `W<640` in the draw function, same as in the rect function.

3. Intro on phone: The typewriter effect shows a cursor block for every line that hasn't been fully typed yet. The fix is to only show a cursor on the current line being typed (the last line with partial text), not on all untyped lines.

Looking at the code:
```js
for(const lines of introLines){
    for(let i=0;i<lines.length;i++){
      const line=lines[i];
      let take=line.length;
      if(remaining>=take){
        // full line, no cursor
      }else{
        // partial line, cursor here
        ctx.fillText(line.slice(0,remaining),marginX,...);
        if(Math.floor(time*3)%2===0){...cursor...}
        remaining=0;
      }
      lineIdx++;
    }
}
```

Wait, when `remaining` is 0 and it's less than `take`, it draws `line.slice(0,0)` which is empty string, and still shows the cursor. That's the bug - every subsequent line shows a cursor.

Fix: Only show the cursor when `remaining > 0` OR when this is the first line that's partially typed. Actually, the cursor should only appear on the line where typing is currently happening. So I should only draw the cursor when `remaining > 0` (i.e., there are some characters typed on this line but not all).

Wait, but what about when remaining is 0? Then the line is empty and we shouldn't show a cursor. Let me fix:

```js
}else{
  if(remaining > 0){
    ctx.fillText(line.slice(0,remaining),...);
    // draw cursor after the partial text
  }
  remaining=0;
}
```

Actually, even when `remaining > 0`, we still need to handle the case where remaining becomes 0 after this line. The cursor should only show on the currently-typing line. Let me restructure:

The logic is:
- For each line, if `remaining >= take`, the whole line is shown (no cursor)
- If `remaining < take`, this is the current typing line
  - If `remaining > 0`, show partial text + cursor
  - If `remaining == 0`, show nothing (no cursor - haven't started this line yet)

So the fix is simply: only draw the cursor when `remaining > 0`.

Let me also make sure the `lineIdx` still increments so the blank lines take up space (for proper vertical positioning). Actually, looking at the code more carefully, `lineIdx` is incremented for every line regardless, which is correct for positioning. The issue is just the cursor showing on empty lines.

Now let me write the complete updated file with just these three fixes.
