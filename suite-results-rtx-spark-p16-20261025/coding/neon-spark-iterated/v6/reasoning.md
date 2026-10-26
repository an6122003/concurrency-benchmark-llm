The user wants 4 specific visual fixes to the boss/upgrade UI. Let me identify the exact code to change:

1. Boss defeat line position: currently `ctx.fillText(boss.defeat,bx,by-160)` — change to below, and clamp y inside screen.

2. Death flash disc: currently the flat pale grey disc — replace with radial gradient in boss color.

3. Boss name/taunt readability: add dark band/outline behind them.

4. Upgrade card segments: currently `for(let k=0;k<=max;k++)` gives max+1 segments, and `k<=lv` lights them — so at lv=0, k=0 lights up, giving 1 lit out of max+1. Change to `k<max` for exactly max segments, and `k<lv` for light.

Let me make those precise edits and return the full file.
