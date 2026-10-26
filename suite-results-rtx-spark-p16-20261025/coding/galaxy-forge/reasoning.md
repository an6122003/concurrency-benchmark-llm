Build a single HTML file using raw WebGL. 60,000 particles, point sprites, additive blending, custom shaders. Galaxy generation on the CPU (positions), animation of differential rotation on the GPU (pass angle, radius, and speed as attributes, compute position in the vertex shader — this is the efficient way). Store per-star attributes: radius, initial angle, vertical offset, color, size, twinkle phase. In the vertex shader, compute angle = angle0 + time * speed(radius). Differential rotation: speed ∝ 1/sqrt(r) or similar.

Spiral arms: place stars along the logarithmic spiral of N arms, with Gaussian scatter. Color based on radius/temperature. Dust lanes: darkening along the arms — just spawn some dark-colored (dim red/brown) stars in the arm cores. Nebulae: separate particle system with a larger, softer sprite count (e.g., 3000), placed along the arms with hue tinting.

Background starfield: static points on a distant sphere.

Camera: orbit with inertia, idle drift after 4 seconds, zoom with scroll/pinch.

Dwarf galaxy collision: on click, spawn a dwarf galaxy of about 2000 stars with its own orbit, tidally pulling main stars into streams. Implementing real gravity with 60k stars is infeasible. Simple approach: give each main star a "stream" attribute? Simpler: the dwarf moves on an elliptical orbit. The main galaxy's stars get a gentle perturbation from the dwarf in the shader: displacement proportional to 1/(dist^2+soft) in the direction toward the dwarf — visual tidal streams. Plus, add some stars that get flung into a stream: pre-assign about 10% of stars to "stream candidates," and when a collision is active, they get pulled along a trail behind the dwarf. Simplest visual: apply a shader-based displacement toward/away from the dwarf position passed as a uniform, weighted by per-star random susceptibility. That produces visible stream-like effects. Good enough.

Big Bang: uniform explosion factor that animates from 1 to large scale and then settles back: use a uniform explosion(t). In the shader, multiply the radius by (1 + exp * f). Animate on the JS side: after explosion, stars expand, then re-form (spring back). Simply: explosionT decays; radius *= 1 + 3*explosionT^2 etc. Plus a burst of velocity… keep it visual.

PNG screenshot: preserveDrawingBuffer true, toDataURL, download link.

UI: glassmorphism panel, sliders for star count (regenerate), arm count (regenerate), speed, spread, preset buttons, toggles.

FPS counter, star counter, hide with H, pause with space, reset with R, screenshot with S.

WebGL setup: single program for stars (and reused for the dwarf), another for nebulae, another for the background. Actually can unify: same point-sprite shader with different uniforms. Use one program, multiple buffers, one draw call each.

Shaders:

Vertex:
attribute vec4 aData; // radius, angle0, speed, size
attribute vec3 aColor;
attribute float aMisc; // twinkle phase / susceptibility
uniforms: uTime, uProj, uView, uExplode, uDwarf(pos+active), uSpeed
compute: ang = aData.y + uTime * aData.z * uSpeed
pos = vec3(cos(ang)*r, y, sin(ang)*r) + bulge offset… vertical offset stored in aColor? Need a separate attribute. Attributes:
- aOrb: vec4 (radius, angle0, angSpeed, y)
- aCol: vec3 color
- aMisc: vec2 (size, phase)
- aStream: susceptibility float

Tidal: vec3 dp = pos - uDwarfPos; float d = length(dp); float pull = uDwarfActive * aStream * uDwarfStr / (d*d*0.05 + 1.0); pos += normalize(dp) * -pull? Pull toward the dwarf to make a stream: pos += (uDwarfPos - pos)*pull. Plus a tangential smear. OK.

Explosion: r_eff = radius * (1.0 + uExplode * 4.0) — plus jitter with phase.

Fragment: soft circular glow: d = length(gl_PointCoord - 0.5); alpha = exp(-d*d*k); color*alpha; additive. Twinkle: size * (0.8+0.4*sin(time*speed+phase)) only when uTwinkle.

Nebulae: same shader but larger points, lower alpha, position along the arms with hue tinting. Also animate rotation — use the same aOrb attribute to rotate with the same differential rotation, larger size, darker color. Reuse the same program with a uniform uAlphaScale.

Core glow: draw one huge point in the center with warm color, plus a small dense bright cluster.

Star count: default 60000. Regenerate on slider change.

Buffer generation:
Galaxy parameters: armCount, spread (scattering), color preset.
For each star:
- Bulge fraction ~25%: random Gaussian r ~ 0.15, y Gaussian ~0.12, random angle, warm gold/red color.
- Disk/arm stars: r = pow(rand,0.6)*1.0 (normalized galaxy radius ~ 1.0), arm index i = floor(rand*arms); armAngle = i*2π/arms + r*wind (wind ~ 3.5 * windFactor); angle = armAngle + gauss*spread*(0.15+r*0.25). y = gauss * thickness (thickness decreases with r: 0.02 + …). Color: arms are hot blue-white, core is warm: mix based on r and random.

angSpeed: v ∝ r^(-0.5) clamped: speed = base / (0.3 + r). base ~ 0.3.

Dust lanes: stars with radius near arm center have lower alpha / darker reddish color.

Preset color palettes:
- Milky Way: arms cool blue-white (0.7,0.8,1), core gold (1,0.85,0.6).
- Andromeda: more pink/white.
- Nebula: purple/teal.
- Neon: cyan/magenta.

Dwarf: 3000 stars, small bulge, own position updated on CPU: orbiting ellipse around center: pos = R_d * (cos(θ), y_d, sin(θ)), θ advances. Pass uDwarfPos per frame; dwarf stars are rendered with the same orbital shader but the model offset = dwarfPos. Add uniform uOffset vec3.

Stream susceptibility: random per star, higher for outer stars.

Camera: yaw, pitch, dist, with velocity for inertia. Idle timer → slow auto yaw drift + gentle pitch bob. Auto-camera toggle.

Pinch: touch events, track two fingers.

FPS: moving average.

Star counter: main + dwarf + background.

Write the code compact and complete.

Matrix: manually implement perspective + lookAt.

view = lookAt(eye, 0,0,0), eye from yaw/pitch/dist.

Point size scaling: gl_PointSize = size * uPx * (somePerspective/ -mvPosition.z). Use: gl_PointSize = aMisc.x * uPointScale * (3.0 / max(0.1, -mv.z)); cap with clamp.

preserveDrawingBuffer: true for screenshots.

DPI: canvas size * devicePixelRatio, cap at 2.

Star regeneration function builds Float32Array.

Big Bang: explode = 1, decays exponentially: explode *= exp(-dt*0.8). Radius scale = 1 + explode*explode*6. Plus color flash? Keep it simple.

Reset R: reset camera, clear dwarf, reinitialize explosion.

Pause space: stops time accumulation.

Screenshot S: after rendering, toDataURL, create a download link.

Write the final code. Keep the structure. Let's go.

Nebula count ~2500, placed along the arms: r in [0.2,0.95], angle along the arm + small offset, larger y scatter, size ~ 40-120 px scale, color = preset nebula hue (mix of pink/purple/teal), alpha low.

Background stars: 4000 points on a sphere of radius 50, static, twinkle.

Draw order: additive anyway, all blendFunc(SRC_ALPHA, ONE) or (ONE, ONE) with premultiplied color*alpha in the fragment. Use gl.blendFunc(gl.SRC_ALPHA, gl.ONE).

Disable depth test (additive, no depth buffer needed).

Now write the HTML.

Uniform locations, program setup — one program, attributes: aOrb(4), aCol(3), aMisc(2), aSus(1) — or pack sus into aMisc. aMisc = vec3(size, phase, sus). Good.

Vertex shader:

```
attribute vec4 aOrb; // r, ang0, angSpeed, y
attribute vec3 aCol;
attribute vec3 aMisc; // size, phase, susceptibility
uniform mat4 uVP;
uniform float uTime, uSpeed, uExplode, uDwarfActive, uTwinkle, uPointScale, uAlpha;
uniform vec3 uDwarfPos;
varying vec3 vColor;
void main(){
 float r = aOrb.x;
 float ang = aOrb.y + uTime * uSpeed * aOrb.z;
 float e = uExplode * (1.0 + aMisc.z*2.0);
 r *= 1.0 + e*e*5.0;
 float y = aOrb.w * (1.0 + e*2.0);
 vec3 p = vec3(cos(ang)*r, y, sin(ang)*r);
 if(uDwarfActive > 0.001){
   vec3 d = uDwarfPos - p;
   float dl = length(d);
   float pull = uDwarfActive * aMisc.z * 2.2 / (dl*dl*0.15 + 0.08);
   p += normalize(d) * min(pull, 1.5) * 0.12;
   // tangential smear for stream
   vec3 tang = normalize(cross(vec3(0.,1.,0.), d));
   p += tang * pull * 0.10;
 }
 vec4 mv = uVP * vec4(p,1.0);
 gl_Position = mv;
 float tw = mix(1.0, 0.75 + 0.45*sin(uTime*3.0 + aMisc.y*17.0), uTwinkle);
 gl_PointSize = clamp(aMisc.x * uPointScale * tw * (4.0 / max(0.2, -mv.z*0+1.0)), 1.0, 64.0);
```

Wait, perspective: mv.z is in clip space — after uVP, -mv.z is the depth in view space… actually mv = uVP * p gives clip space; clip z is in [-w,w]. -clipz/w = depth. Use: gl_PointSize = size * uPointScale * tw / max(0.3, -mv.z/mv.w)? Simpler: pass a view matrix? Let's just compute size = aMisc.x * uPointScale * tw * (1.2 / (0.4 + distToCam/10)) — need camera distance: pass uEye uniform and compute dist = length(p - uEye). size ∝ 1/dist. Good: gl_PointSize = clamp(aMisc.x * uPointScale * tw * (2.0 / max(0.5, dist)), 1.0, 96.0).

vColor = aCol * tw * uAlpha.

Fragment:
```
precision mediump float;
varying vec3 vColor;
void main(){
 vec2 c = gl_PointCoord - 0.5;
 float d = dot(c,c)*4.0;
 float a = exp(-d*3.0) - 0.03; // soft
 a = max(a,0.0);
 gl_FragColor = vec4(vColor * a, a);
}
```
With blend SRC_ALPHA, ONE: color = vColor*a, alpha a → adds vColor*a. Good.

Glow toggle: two-pass? Simpler: uGlow uniform that changes the falloff: uniform uGlowMix that picks between tight core and wide glow. exp(-d * mix(9.0, 2.5, uGlow)). Also add a white core: core = exp(-d*25.0)*0.8.

Nebulae: large size, alpha low (0.05), use a more elliptical shape? Keep it circular, that's fine.

Now the JS generation:

gauss(): Box-Muller-ish (sum of randoms).

buildGalaxy(count, arms, spread, preset):
Fill orb, col, misc arrays.
- Bulge count = count*0.22
- Core glow stars = count*0.04 bright gold-white, small r.
- The rest are disk/arm stars.

Colors: preset object {armCol:[c1,c2], coreCol, nebula:[...]}.

Milky Way: armCol: [(0.65,0.78,1.0),(1.0,0.95,0.85)] core (1.0,0.82,0.55), nebula [(0.35,0.45,1.0),(1.0,0.4,0.7),(0.2,0.8,0.9)].

For each disk star:
r = Math.pow(Math.random(), 0.62);
arm = floor(rand*arms);
base = arm*TAU/arms + r*wind (wind=2.8)
spreadAng = gauss()*spread*(0.12 + 0.28*r)
ang = base + spreadAng
y = gauss()*0.018*(1+2*r) + … thinner: 0.012+0.004r
angSpeed = 0.9/(0.25 + r) * 0.35 → v ~ 0.35*0.9/(0.25+r). At r=0.25 → 1.26… too fast? Time is in seconds; one revolution in TAU/1.26 ≈ 5s. Too fast. Scale: angSpeed = 0.22/(0.3+r). r=0.3 → 0.37 rad/s → 17s/rev. r=1 → 0.17 rad/s → 37s. OK.

Color: t = r plus rand: mix coreCol→armCol by smoothstep(0.15,0.55,r), plus jitter; hot stars in arms: pick armCol random blend, some blue (0.7,0.8,1). Dust: if |spreadAng|<0.05 → darken: multiply color by 0.25, reddish.

size: 1.0-2.2 rand^2.

sus (susceptibility): random, biased by outer radius: (r>0.5? rand:rand*0.3).

Nebulae build(arms, spread, preset): 2200 points along the arms, r = 0.15+rand*0.85, angle along arm + gauss*0.08, y gauss*0.05, size 30-110, color pick from nebula palette, alpha via uAlpha 0.05, angSpeed same as disk at that r.

Dwarf build: 3000 stars, small: r = pow(rand,0.5)*0.12, warm white/pink.

Dwarf motion: theta advances, radius varies: R = 1.6 - 0.9*cos(theta*0.7)? Keep elliptical: Rx=1.5, Rz=0.7, y = 0.25*sin(theta*2.0)*… use:
dTheta += dt*0.15*speed; pos = [cos(dTheta)*1.4, sin(dTheta*0.5)*0.5, sin(dTheta)*1.4*0.6]; active ramps up 0→1 over 3 seconds, fades out after 40 seconds? Keep active until reset or a new one? Keep it active, maybe fade over 60 seconds. Let active decay slowly: after 30 seconds active *= (1 - dt*0.05)… simpler: keep until reset or a new click. Let it fade: if t>25s, active -= dt*0.03.

Dwarf star rendering: same orbital shader with offset uniform uOffset (dwarf position), dwarf stars have aMisc sus = 0.

Also give dwarf stars a slow self-spin.

Background: 3500 stars, sphere of radius 30, static (angSpeed 0), small size, dim, twinkle.

UI panel: collapsible with header button. Sliders: stars (10k–120k, step 5k, default 60k), arms (2–5), speed (0–3), spread (0.2–2). Presets as buttons. Toggles as checkboxes: glow, nebula, auto-cam. BIG BANG button.

Title top-left: GALAXY FORGE, FPS, stars.

Hint text: "drag to orbit · scroll to zoom · click to spawn a dwarf galaxy".

Click vs drag: track mousedown position; if mouseup within a small distance and short time → spawn dwarf at projected… just spawn the dwarf (position independent of click point).

Touch: one finger drag orbit, two fingers pinch zoom.

Pause: don't advance uTime, keep rendering (camera still works).

FPS: count frames each second.

Write the code. Careful with the shader attribute setup (one program, bind the same attribute locations for each buffer).

Matrix math:

persp(fov, aspect, near, far)
lookAt: standard.

Camera: eye = [dist*cos(pitch)*sin(yaw), dist*sin(pitch), dist*cos(pitch)*cos(yaw)]. Clamp pitch to (-1.5, 1.5).

Inertia: yawVel, pitchVel decay *0.92 per frame.

Idle: lastInteract; if now-lastInteract>4000 and autoCam: yaw += dt*0.05; pitch → target sin drift: pitch += (Math.sin(t*0.1)*0.35 - pitch)*dt*0.3; slight dist drift.

Resize: canvas width = innerWidth*dpr etc.

Screenshot: render then toDataURL immediately.

Star counter element updated: stars + nebulae? Show total point count: main + 3500 background. "★ 63,500".

OK, let's write it.

Also handle WebGL point size limit — no problem.

Explosion: explode = 1 → in shader r *= 1 + e*e*5: max 6×, nice.

Also on Big Bang, add a flash: temporarily boost uAlpha? Skip.

Write the final answer.

Edge: regenerate on star slider change — debounce on 'change', live on 'input'? Just regenerate on 'input' with throttling; 60k build is fast enough (<30ms). Use 'input' with rAF throttle.

Code:

```html
<!DOCTYPE html>
<html>...
```

Let's carefully write everything.

Fragment glow:
```
float d = dot(c,c)*4.0;
float core = exp(-d*18.0);
float halo = exp(-d * mix(10.0, 2.2, uGlow));
float a = core*1.2 + halo*0.6;
```
When glow is off uGlow=0 → tight. Multiply by vColor (which already contains alpha scale). Nebulae also use same shader, size large, alpha low.

Nebula alpha: pass uAlpha per draw: main stars 1.0, nebulae 0.06, background 0.8.

One issue: gl_PointSize cap 96 dpr… uPointScale = dpr * canvasH/1000 or so. Set uPointScale = (canvas.height/900).

Dwarf: offset uniform uOffset vec3; add to p before camera calc. For main/background/nebula, uOffset=0.

Now let's write the complete file.

Panel CSS: glassmorphism: backdrop-filter blur, rgba bg, border.

Keyboard: H toggles .hidden on #ui container; Space toggles pause (preventDefault); R reset; S screenshot.

Reset: camera to defaults, dwarfActive=0, explode=0.

Big Bang: explode=1; plus maybe a random kick too: also re-randomize? Keep it simple.

Also on click spawn dwarf: also set dwarfPos initial.

OK, writing.

Star count label in the counter: `${mainCount + BG.toLocaleString()}`.

Let's write the code.

```js
// matrices
function perspective(fov, aspect, n, f){ const t=1/Math.tan(fov/2); const nf=1/(n-f);
 return new Float32Array([t/aspect,0,0,0, 0,t,0,0, 0,0,(f+n)*nf,-1, 0,0,2*f*n*nf,0]); }
function lookAt(e, c, up){ ... }
```

Compose VP = P * V.

Write a small mat4 multiply.

Time: simTime advances by dt*1 when not paused.

Dwarf update uses simTime? Use real dt * speed when not paused.

OK, writing final.

Pinch: on touchmove, if 2 touches, compute distance delta → targetDist.

Use a targetDist for smoothing zoom: dist += (targetDist-dist)*0.15.

OK, let's write the complete code, compact but readable.

Attribute locations: set via getAttribLocation.

Per draw: bind buffers, enable arrays.

Buffers: orb (4f), col(3f), misc(3f) per system.

Star build function:

```js
function buildMain(){
 const n = state.stars;
 orb = new Float32Array(n*4); col = new Float32Array(n*3); misc = new Float32Array(n*3);
 const arms=state.arms, spread=state.spread, P=PRESETS[state.preset];
 const nBulge = n*0.22|0, nCore = n*0.04|0;
 let i=0;
 for(i=0;i<nCore;i++){ small bright stars }
 ...
}
```

Color mix helper.

Bulge star: r = |gauss|*0.16, y = gauss*0.13, ang random, color coreCol mixed with (1,0.6,0.4), size smaller.

Disk: as above.

Wind: 3.0.

Dust: |gaussSpread|<0.045 and r>0.12 → dust flag.

sus = (Math.random()* (r*0.9) ).

Nebula build similar.

Dwarf: static array of 3000, offset animated.

Now, writing. Also FPS: frames++, compute every 500ms.

Final answer: single html code block, no explanation.
