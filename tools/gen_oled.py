#!/usr/bin/env python3
"""Generates the OLED showcase wallpapers (v0.8): Event Horizon, Abyss, Prairie Fireflies, Fractal Dive.

Every scene is one full-screen WebGL fragment shader rendered at the screen's exact device-pixel size
(up to 8K = 7680x4320 worth of pixels), animated from real time so it's smooth at 60, 120, 144 or 240 Hz.
Empty space is written as exact 0,0,0 so OLED pixels switch fully off.

    python tools/gen_oled.py        -> rewrites wallpapers/<scene>.html
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "wallpapers"

COMMON = r"""
precision highp float;
uniform vec2 R; uniform float T;
#define TAU 6.2831853
float h21(vec2 p){ vec3 q=fract(vec3(p.xyx)*.1031); q+=dot(q,q.yzx+33.33); return fract((q.x+q.y)*q.z); }
vec2  h22(vec2 p){ float n=h21(p); return vec2(n,h21(p+n+3.7)); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),u.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),u.x),u.y); }
float fbm(vec2 p){ float s=0.,a=.5; for(int i=0;i<5;i++){ s+=a*vn(p); p=mat2(1.6,1.2,-1.2,1.6)*p; a*=.5; } return s; }
vec3 hsv(float h,float s,float v){ vec3 k=clamp(abs(mod(h*6.+vec3(0,4,2),6.)-3.)-1.,0.,1.); return v*mix(vec3(1),k,s); }
mat2 rot(float a){ float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }
// Pinpoint stars: p in scene units, g = grid cell, px = one device pixel in the same units.
// A star is ~1.5 px wide at any resolution, so higher-res screens get sharper, finer stars.
vec3 stars(vec2 p,float g,float px,float dens,float t){
  vec2 id=floor(p/g), f=p/g-id; float n=h21(id);
  if(n<dens) return vec3(0);
  vec2 o=.15+.7*h22(id+7.1); float d=length((f-o)*g)/px;
  float b=pow(h21(id+3.3),3.)*.9+.1;
  float tw=.78+.22*sin(t*(.6+2.5*h21(id+1.9))+n*40.);
  vec3 c=mix(vec3(.62,.76,1.),vec3(1.,.84,.62),h21(id+9.2));
  return c*b*tw*exp(-d*d*.9);
}
"""

SCENES = {}

# ---------------------------------------------------------------- Event Horizon
SCENES["event-horizon"] = ("Event Horizon", """A ray-traced black hole: photons bent by gravity around a blazing,
   Doppler-beamed accretion disk, with the starfield lensed into rings behind it. The shadow
   is exact black. The camera slowly orbits and the hole drifts so no pixel cooks.""", r"""
vec4 disk(vec3 q,float r,vec3 v,float t){
  float ang=t*.55*pow(r,-1.5);                       // Keplerian: inner disk spins faster
  vec2 pq=rot(ang)*q.xz;
  float n=.55*fbm(pq*1.05+3.)+.45*fbm(vec2(r*6.5,1.7)+pq*.08);
  float inner=smoothstep(2.45,3.2,r), outer=1.-smoothstep(6.5,11.5,r);
  float temp=pow(3./r,1.35);
  vec3 cc=mix(vec3(.30,.04,.55),vec3(.95,.10,.42),smoothstep(.12,.32,temp));
  cc=mix(cc,vec3(1.,.50,.10),smoothstep(.32,.62,temp));
  cc=mix(cc,vec3(1.,.95,.86),smoothstep(.72,1.05,temp));
  vec3 orb=normalize(vec3(-q.z,0.,q.x));
  float beta=sqrt(.5/r), cosT=dot(orb,-normalize(v));
  float D=sqrt(1.-beta*beta)/(1.-beta*cosT), boost=D*D*D;
  cc=mix(cc,vec3(1.,.96,.9),clamp(boost-1.,0.,.6)*.45);
  float a=clamp(inner*outer*(.3+.75*n)*1.25,0.,1.);
  return vec4(cc*temp*(.45+.9*n)*boost*2.1,a);
}
vec3 sky(vec3 d,float px,float t){
  vec2 s=vec2(atan(d.z,d.x),asin(clamp(d.y,-1.,1.)));
  vec3 c=stars(s,.010,px,.66,t)+stars(s+7.,.045,px*1.6,.86,t)*1.4;
  float neb=max(fbm(s*2.2+1.)-.56,0.);
  c+=neb*neb*vec3(.9,.25,.8)*1.4;
  return c;
}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*R)/R.y;
  float t=T;
  uv-=.05*vec2(sin(t*.013),cos(t*.017));            // slow wander: burn-in insurance
  float az=t*.011, inc=.16+.10*sin(t*.019);
  float dist=24.;
  vec3 ro=dist*vec3(cos(inc)*sin(az),sin(inc),-cos(inc)*cos(az));
  vec3 fw=normalize(-ro), rt=normalize(cross(vec3(0,1,0),fw)), up=cross(fw,rt);
  float zoom=1.05;
  vec3 rd=normalize(fw+(uv.x*rt+uv.y*up)*zoom);
  float px=zoom/R.y;
  vec3 p=ro, v=rd; vec3 h=cross(p,v); float h2=dot(h,h);
  vec3 col=vec3(0); float alpha=0.; bool cap=false;
  for(int i=0;i<110;i++){
    float r=length(p);
    float dt=clamp(.07*r,.015,2.2);
    v+=-1.5*h2*p/(r*r*r*r*r)*dt;
    vec3 np=p+v*dt;
    if(p.y*np.y<0.){
      vec3 q=mix(p,np,p.y/(p.y-np.y)); float rq=length(q.xz);
      if(rq>2.4&&rq<12.){ vec4 d=disk(q,rq,v,t); col+=(1.-alpha)*d.rgb*d.a; alpha+=(1.-alpha)*d.a; }
    }
    p=np;
    float nr=length(p);
    if(nr<1.){ cap=true; break; }
    if(nr>40.&&dot(p,v)>0.) break;
    if(alpha>.995) break;
  }
  if(!cap) col+=(1.-alpha)*sky(normalize(v),px,t);
  col=col/(1.+col*.22);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}""")

# ---------------------------------------------------------------- Abyss
SCENES["abyss"] = ("Abyss", """Deep sea at midnight: neon jellyfish that swim in pulses, wander and tilt
   where they're heading, with tentacles trailing along the path they swam and light
   pulses running down them. Near and far jellies, drifting marine snow and flashes of
   plankton. Everything else is exact black. More jellies on wider screens.""", r"""
float flashes(vec2 p,float g,float px,float t,out float hue){
  vec2 id=floor(p/g), f=p/g-id; float n=h21(id); hue=h21(id+4.4);
  if(n<.55) return 0.;
  vec2 o=.2+.6*h22(id+2.2); float d=length((f-o)*g)/px;
  float ph=fract(t*(.05+.08*h21(id+8.))+n*7.);
  float fl=smoothstep(0.,.03,ph)*(1.-smoothstep(.04,.22,ph));
  return fl*(exp(-d*d*.6)+.35*exp(-d*.35));
}
// vivid neon palette: hot pink, cyan, electric blue, violet, lime, orange, magenta
vec3 neon(float k){
  k=fract(k)*7.;
  if(k<1.) return vec3(1.,.12,.62);
  if(k<2.) return vec3(.05,.95,1.);
  if(k<3.) return vec3(.15,.38,1.);
  if(k<4.) return vec3(.62,.18,1.);
  if(k<5.) return vec3(.45,1.,.22);
  if(k<6.) return vec3(1.,.48,.08);
  return vec3(1.,.15,1.);
}
// where jelly i is sideways at time t (two slow swirls = it wanders around)
float jx(float x0,float A,float t,float fi){
  return x0+A*(sin(t*(.045+.03*h21(vec2(fi,11.)))+fi*2.1)*.65+sin(t*(.11+.05*h21(vec2(fi,12.)))+fi*4.3)*.35);
}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*R)/R.y;
  float asp=R.x/R.y, px=1./R.y, t=T;
  vec3 col=vec3(0);
  // faint god-rays from far above
  float top=smoothstep(-.1,.55,uv.y);
  float rays=pow(max(0.,sin(uv.x*7.+sin(uv.x*2.3+t*.07)*2.+t*.05)),6.)*pow(max(0.,sin(uv.x*3.1-t*.04)),2.);
  col+=vec3(.0,.10,.16)*rays*top*top*.35;
  // marine snow, three depths drifting down
  for(int k=0;k<3;k++){
    float fk=float(k), sc=1.+fk*.7;
    vec2 q=uv*sc+vec2(.04*sin(t*.07+fk*2.),t*(.006+.004*fk)+fk*13.);
    col+=stars(q,.022,px*sc,.72,t)*vec3(.55,.75,.85)*(.55-fk*.13);
  }
  // plankton flashes
  float hue; float fl=flashes(uv+vec2(t*.004,0.),.045,px,t,hue);
  col+=fl*mix(vec3(.1,.9,1.),vec3(.3,.4,1.),hue);
  fl=flashes(uv*1.6+vec2(9.,t*.003),.04,px*1.6,t*1.1,hue);
  col+=fl*mix(vec3(.1,1.,.75),vec3(.6,.2,1.),hue)*.6;

  int N=int(clamp(floor(asp*2.6+.5),3.,10.));
  float fN=float(N);
  for(int i=0;i<10;i++){
    if(i>=N) break;
    float fi=float(i);
    float z=h21(vec2(fi,9.));                       // depth: 0 = far, 1 = near
    float dep=.55+.75*z;
    float bright=.45+.75*z;
    float sz=(.034+.03*h21(vec2(fi,2.)))*dep;
    float sp=(.016+.014*h21(vec2(fi,1.)))*dep;      // near ones swim faster (parallax)
    float w=1.1+.6*h21(vec2(fi,3.));                // stroke rate
    float A=(.10+.10*h21(vec2(fi,5.)))*min(asp,2.4);
    float lane=((fi+.5)/fN-.5)*asp*.92;
    float L=sz*(5.+3.*h21(vec2(fi,6.)));
    float span=1.+L+3.*sz;
    // swim in pulses: surges forward each time the bell squeezes
    float Y=sp*(t+.75*sin(w*t)/w);
    float y0=-.5-1.5*sz+mod(fi*.613*span+Y,span);
    float x0=jx(lane,A,t,fi);
    // heading -> tilt the bell toward where it's going
    float vx=(jx(lane,A,t+.5,fi)-jx(lane,A,t-.5,fi));
    float vy=sp*(1.+.75*cos(w*t));
    float ang=clamp(atan(vx,vy),-.55,.55);
    float squeeze=.5+.5*cos(w*t);                   // 1 = squeezed (thrust)
    float bw=sz*(1.08-.2*squeeze), bh=sz*(.72+.16*squeeze);
    vec3 c1=neon(h21(vec2(fi,4.))+t*.004);
    vec3 c2=neon(h21(vec2(fi,4.))+.18+t*.004);
    vec2 q=uv-vec2(x0,y0);
    float reach=bw*2.6+2.2*A+.06;
    if(abs(q.x)>reach||q.y>bh*1.8+.04||q.y<-L-bh-.04) continue;
    // ---- bell (in the jelly's tilted frame)
    vec2 r=rot(ang)*q;
    vec2 e=r/vec2(bw,bh);
    float db=e.y>0.?length(e)-1.:max(abs(e.x)-1.+(-e.y)*.35,-e.y-.24);
    float dpx=abs(db)*sz/px;
    float glowPulse=.8+.45*squeeze;
    col+=c1*bright*glowPulse*(exp(-dpx*.5)*1.25+exp(-dpx*.07)*.18);
    if(db<0.){
      float ribs=pow(abs(sin(atan(e.x,e.y+.3)*7.)),10.)*.35;
      float core=exp(-length(e-vec2(0.,.25))*2.4)*.75;
      float spots=smoothstep(.75,1.,sin(e.x*9.+t*.7)*sin(e.y*7.-t*.5))*.25;
      col+=mix(c1,c2,.5+.5*e.y)*bright*(.12+ribs*smoothstep(-.2,.6,e.y)+core*glowPulse+spots);
    }
    // ---- tentacles: each one is pinned to its own spot on the (tilted) rim of the bell, then hangs
    //      down along the path the bell swam, so they trail behind but never come loose.
    mat2 toWorld=rot(-ang);
    float tilt=sin(ang);
    for(int k=0;k<9;k++){
      float fk=float(k);
      bool arm=k==8;                                  // last one = the frilly oral arms in the middle
      vec2 anc=vec2(x0,y0)+toWorld*vec2(arm?0.:bw*(-.82+1.64*fk/7.),-.18*bh);
      float s=anc.y-uv.y;                            // how far below this tentacle's own anchor
      float Lk=arm?L*.55:L*(.82+.18*h21(vec2(fi,fk+20.)));
      if(s<-.06*sz||s>Lk) continue;
      float sc=max(s,0.);
      float fade=pow(1.-sc/Lk,1.3)*smoothstep(-.06*sz,.04*sz,s);   // tucks up under the bell
      float lag=.4*sc/max(sp,.005);
      float xPath=clamp(jx(lane,A,t-lag,fi)-x0,-sc*.45,sc*.45);
      // near the bell, hang along the tilt (straight out of the rim), then relax to straight down
      float lean=tilt*sc*.6*exp(-sc/(2.5*sz));
      float grow=smoothstep(0.,1.5*sz,sc);             // wiggle starts small at the rim
      if(arm){
        float xa=anc.x+lean+xPath*.8+sin(sc/sz*.8-t*1.1+fi)*bw*.28*grow;
        float wa=sz*.2*(1.-sc/Lk)+sz*.02;
        float d=abs(uv.x-xa)/wa;
        col+=c2*bright*.55*exp(-d*d*1.4)*(.55+.45*sin(sc/sz*9.-t*2.6))*fade;
        continue;
      }
      float amp=(.16+.12*h21(vec2(fi,fk)))*sc*grow;
      float xk=anc.x+lean+xPath+sin(sc/sz*1.3-t*(1.4+.4*h21(vec2(fk,fi)))+fk*1.7)*amp*.4;
      float d=abs(uv.x-xk)/px;
      float wave=pow(.5+.5*sin(sc/sz*2.6-t*4.5+fi),6.);  // light pulses running down
      vec3 tc=mix(c1,c2,sc/L);
      col+=tc*bright*fade*(exp(-d*d*.3)*(.85+1.1*wave)+exp(-d*.1)*.06);
    }
  }
  col=col/(1.+col*.12);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}""")

# ---------------------------------------------------------------- Abyss Pets
SCENES["abyss-pets"] = ("Abyss Pets", """Abyss, but the jellies are your pets. They stick around, blink, pull faces and
   do random stuff whenever they feel like it: backflips, triple flips, twirls, loop-de-loops,
   happy dances, heart bubbles, naps with Zzz's, boing bounces, zoomies, sparkle sneezes,
   getting spooked, and buddy spins with a friend. Every so often a random one swims up to the
   glass to wave, blow you a big heart, or smoosh its face on the glass.
   Same deep-sea background as Abyss; everything else is exact black.""", r"""
float flashes(vec2 p,float g,float px,float t,out float hue){
  vec2 id=floor(p/g), f=p/g-id; float n=h21(id); hue=h21(id+4.4);
  if(n<.55) return 0.;
  vec2 o=.2+.6*h22(id+2.2); float d=length((f-o)*g)/px;
  float ph=fract(t*(.05+.08*h21(id+8.))+n*7.);
  float fl=smoothstep(0.,.03,ph)*(1.-smoothstep(.04,.22,ph));
  return fl*(exp(-d*d*.6)+.35*exp(-d*.35));
}
vec3 neon(float k){
  k=fract(k)*7.;
  if(k<1.) return vec3(1.,.12,.62);
  if(k<2.) return vec3(.05,.95,1.);
  if(k<3.) return vec3(.15,.38,1.);
  if(k<4.) return vec3(.62,.18,1.);
  if(k<5.) return vec3(.45,1.,.22);
  if(k<6.) return vec3(1.,.48,.08);
  return vec3(1.,.15,1.);
}
float ease(float x){ x=clamp(x,0.,1.); return x*x*(3.-2.*x); }
float env(float k,float a,float b,float T){ return ease(k/a)*ease((T-k)/b); }
float sdSeg(vec2 p,vec2 a,vec2 b){ vec2 pa=p-a,ba=b-a; float h=clamp(dot(pa,ba)/dot(ba,ba),0.,1.); return length(pa-ba*h); }
float dot2(vec2 v){ return dot(v,v); }
// heart outline distance (tip at 0,0, about 1 tall)
float sdHeart(vec2 p){
  p.x=abs(p.x);
  if(p.y+p.x>1.) return sqrt(dot2(p-vec2(.25,.75)))-.35355;
  return sqrt(min(dot2(p-vec2(0.,1.)),dot2(p-.5*max(p.x+p.y,0.))))*sign(p.x-p.y);
}
// where pet i likes to hang out: its own patch of the screen, never off it
vec2 home(float fi,float t,float asp,float fN){
  float room=max(asp-.38,.2);
  float lane=((fi+.5)/fN-.5)*room, lw=room/fN;
  float x=lane+lw*.6*(sin(t*(.05+.03*h21(vec2(fi,1.)))+fi*2.)*.7+sin(t*(.13+.04*h21(vec2(fi,2.)))+fi)*.3);
  float y=.1+.15*(sin(t*(.07+.03*h21(vec2(fi,3.)))+fi*3.)*.7+sin(t*.17+fi*1.3)*.3);
  return vec2(x,y);
}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*R)/R.y;
  float asp=R.x/R.y, px=1./R.y, t=T;
  vec3 col=vec3(0);
  // same deep sea as Abyss: faint god-rays, marine snow at three depths, plankton flashes
  float top=smoothstep(-.1,.55,uv.y);
  float rays=pow(max(0.,sin(uv.x*7.+sin(uv.x*2.3+t*.07)*2.+t*.05)),6.)*pow(max(0.,sin(uv.x*3.1-t*.04)),2.);
  col+=vec3(.0,.10,.16)*rays*top*top*.35;
  for(int k=0;k<3;k++){
    float fk=float(k), sc=1.+fk*.7;
    vec2 q=uv*sc+vec2(.04*sin(t*.07+fk*2.),t*(.006+.004*fk)+fk*13.);
    col+=stars(q,.022,px*sc,.72,t)*vec3(.55,.75,.85)*(.55-fk*.13);
  }
  float hue; float fl=flashes(uv+vec2(t*.004,0.),.045,px,t,hue);
  col+=fl*mix(vec3(.1,.9,1.),vec3(.3,.4,1.),hue);
  fl=flashes(uv*1.6+vec2(9.,t*.003),.04,px*1.6,t*1.1,hue);
  col+=fl*mix(vec3(.1,1.,.75),vec3(.6,.2,1.),hue)*.6;

  int N=int(clamp(floor(asp*1.6+.5),3.,6.));
  float fN=float(N);

  // ---- glass visits: every 30 s there's a coin flip; a random pet comes up and does a random greeting
  float GS=30., gt=t+13., gn=floor(gt/GS), gk=gt-gn*GS-4., GT=11.;
  bool gOn=gk>0.&&gk<GT&&h21(vec2(gn,71.))<.5;
  float visitor=gOn?floor(h21(vec2(gn,77.))*fN):-1.;
  float gvar=floor(h21(vec2(gn,79.))*3.);            // 0 wave, 1 blow a heart, 2 smoosh face on the glass
  float occ=0.;
  if(gOn){
    float vi=visitor, g=env(gk,2.,2.,GT);
    vec2 C=home(vi,t,asp,fN);
    vec2 v=home(vi,t+.5,asp,fN)-home(vi,t-.5,asp,fN);
    float th=mix(clamp(v.x*8.,-.5,.5),.1*sin(gk*2.4),g);
    C=mix(C,vec2(clamp(C.x,-asp*.28,asp*.28),.04),g);
    float S=mix(.05+.022*h21(vec2(vi,9.)),.2,g);
    float sqz=.5+.5*cos((1.1+.5*h21(vec2(vi,3.)))*t);
    vec2 e=(rot(th)*(uv-C)/S)/vec2(1.08-.2*sqz,.72+.16*sqz);
    float db=e.y>0.?length(e)-1.:max(abs(e.x)-1.+(-e.y)*.35,-e.y-.24);
    occ=g*.92*smoothstep(.05,-.05,db);
  }

  for(int i=0;i<6;i++){
    if(i>=N) break;
    float fi=float(i);
    float base=(.05+.022*h21(vec2(fi,9.)));
    float w=1.1+.5*h21(vec2(fi,3.));
    vec2 C=home(fi,t,asp,fN);
    vec2 v=home(fi,t+.5,asp,fN)-home(fi,t-.5,asp,fN);
    vec2 xv=vec2(0);                                  // extra speed from tricks (tentacles trail it)
    float S=base, sq=1., sqy=1., thAdd=0., fling=0., flingDir=1., armE=0., happy=0., boop=-1., glass=0., glassWig=0.;
    float dim=1., splay=0., eyeMode=0., smile=0., ohMouth=0., zzz=-1., zE=0., hearts=-1., hE=0., sneeze=-1., bigHeart=-1.;
    float phase=w*t;
    if(abs(visitor-fi)<.5){
      glass=env(gk,2.,2.,GT);
      C=mix(C,vec2(clamp(C.x,-asp*.28,asp*.28),.04),glass);
      S=mix(S,.2,glass);
      glassWig=.1*sin(gk*2.4);
      boop=gk-2.;
      smile=glass;
      if(gvar<.5){ armE=env(gk-2.3,.8,.8,GT-4.7); }
      else if(gvar<1.5){                              // blow a heart: puff up, then mwah
        float pf=env(gk-2.2,.6,.3,1.3);
        S*=1.+.12*pf; eyeMode=glass>.3?2.:0.;
        bigHeart=gk-3.4;
      } else {                                        // smoosh face on the glass
        float sm=env(gk-2.,.35,.7,5.5);
        sq=1.+.45*sm; sqy=1.-.38*sm; eyeMode=sm>.2?2.:0.;
      }
    } else {
      // ---- buddy spin: now and then two neighbours grab each other and spin around
      float pr=floor(fi/2.), mate=fi-2.*pr<.5?fi+1.:fi-1.;
      float BS=9., bt=t+pr*4.1+2., bn=floor(bt/BS), bk=bt-bn*BS;
      bool orbit=mate<fN&&abs(mate-visitor)>.5&&h21(vec2(pr,bn+300.))<.08;
      if(orbit){
        float e=env(bk,1.5,1.5,BS);
        vec2 M=(home(fi,t,asp,fN)+home(mate,t,asp,fN))*.5;
        float side=fi<mate?0.:3.14159;
        float a=bk*1.6+side;
        C=mix(C,M+vec2(cos(a)*.11,sin(a)*.07),e);
        xv+=vec2(-sin(a)*.11,cos(a)*.07)*1.6*e;
        thAdd+=.35*sin(a)*e; fling=.4*e;
        if(e>.3){ eyeMode=2.; smile=e; }
      } else {
        // ---- solo tricks: every 9 s each pet rolls the dice (about 1 in 3), then picks a random trick
        float SL=9., st=t+fi*3.7, sn=floor(st/SL), k=st-sn*SL;
        if(h21(vec2(fi,sn+100.))<.34){
          float r=floor(h21(vec2(fi+.5,sn+200.))*11.);
          float dir=h21(vec2(fi,sn+9.))<.5?1.:-1.;
          if(r<.5){                                   // backflip with a hop
            float f=ease((k-2.5)/2.2);
            thAdd+=dir*f*6.2831853; flingDir=dir;
            C.y+=sin(f*3.14159)*.11; fling=sin(f*3.14159); S*=1.+.15*fling;
          } else if(r<1.5){                           // triple flip!
            float f=ease((k-2.)/3.);
            thAdd+=dir*f*18.849556; flingDir=dir;
            C.y+=sin(f*3.14159)*.15; fling=sin(f*3.14159);
            if(fling>.3) eyeMode=3.;
          } else if(r<2.5){                           // twirl
            float f=ease((k-2.5)/4.);
            sq=cos(f*12.566); C.y+=sin(f*3.14159)*.06; fling=.5*sin(f*3.14159);
          } else if(r<3.5){                           // loop-de-loop
            float f=ease((k-1.5)/5.5), a=f*6.2831853, Rl=.11;
            C+=Rl*vec2(sin(a),1.-cos(a)); thAdd+=a; fling=sin(f*3.14159); flingDir=-1.;
          } else if(r<4.5){                           // rainbow happy dance
            happy=env(k,1.5,1.5,SL);
            C.y+=abs(sin(k*4.5))*.05*happy; thAdd+=.35*sin(k*6.)*happy; phase+=happy*k*4.;
            if(happy>.3){ eyeMode=2.; smile=happy; }
          } else if(r<5.5){                           // heart bubbles
            hE=env(k,1.,1.,SL); hearts=k;
            C.y+=.03*hE; if(hE>.3){ eyeMode=2.; smile=hE; }
          } else if(r<6.5){                           // nap time: sinks, dims, closes its eyes, Zzz
            zE=env(k,1.5,1.5,SL); zzz=k;
            dim=1.-.45*zE; C.y-=.05*zE; thAdd+=zE*.22*sin(t*.6); phase-=zE*k*w*.6;
            if(zE>.3) eyeMode=1.;
          } else if(r<7.5){                           // boing boing
            float e=env(k,1.,1.,SL);
            float b=abs(sin(k*3.2));
            C.y+=(b*.09-.04)*e;
            float contact=pow(1.-b,4.)*e;
            sqy=1.-.32*contact; sq=1.+.25*contact;
            if(e>.3) eyeMode=2.;
          } else if(r<8.5){                           // zoomies: dash across and back
            float ft=ease((k-1.)/6.);
            float D=dir*.33*min(asp,2.);
            float x0=C.x;
            C.x=clamp(C.x+D*sin(ft*3.14159),-asp*.5+.09,asp*.5-.09);
            xv.x=D*cos(ft*3.14159)*.55*step(.001,ft)*step(ft,.999);
            if(ft>.05&&ft<.95){ smile=1.; }
          } else if(r<9.5){                           // ah... ah... ACHOO (sparkles everywhere)
            float inh=ease((k-1.5)/1.4)*(1.-ease((k-3.)/.15));
            S*=1.+.2*inh;
            sneeze=k-3.;
            if(k>1.5&&k<3.) eyeMode=1.;
            if(sneeze>0.&&sneeze<2.5){ eyeMode=3.; ohMouth=1.; C.y+=.05*sin(clamp(sneeze/1.2,0.,1.)*3.14159); thAdd+=-.4*sin(clamp(sneeze/.8,0.,1.)*3.14159)*dir; }
          } else {                                    // spooked! big eyes, tentacles splay
            float e=env(k-1.,.25,1.2,3.5);
            C.y+=.08*sin(ease((k-1.)/1.)*3.14159);
            splay=e; S*=1.+.1*e;
            if(e>.2){ eyeMode=3.; ohMouth=e; }
          }
        }
      }
    }
    float th=mix(clamp((v.x+xv.x)*8.,-.5,.5),glassWig,glass)+thAdd;
    float squeeze=.5+.5*cos(phase);
    vec3 c1=neon(h21(vec2(fi,4.))+t*.003);
    vec3 c2=neon(h21(vec2(fi,4.))+.18+t*.003);
    if(happy>0.){ c1=mix(c1,hsv(fract(t*.35+fi*.15),.9,1.),happy); c2=mix(c2,hsv(fract(t*.35+fi*.15+.2),.9,1.),happy); }
    float bright=(.9+.35*glass)*dim;
    float keep=abs(fi-visitor)<.5?1.:1.-occ;

    // things drawn in screen space: glass ripple and the big blown heart
    if(boop>0.&&boop<1.8){
      vec2 bc=C+vec2(0.,S*.55);
      float rr=boop*.32*(gvar>1.5?1.4:1.), d=abs(length(uv-bc)-rr)/px;
      col+=c1*exp(-d*d*.04)*.45*(1.-boop/1.8);
    }
    if(bigHeart>0.&&bigHeart<5.){
      float a=bigHeart, hs=S*(.7+a*1.1);
      vec2 hp=(uv-(C+vec2(.03*sin(a*2.),S*1.1+a*.05)))/hs+vec2(0.,.5);
      float d=abs(sdHeart(hp))*hs/px;
      col+=vec3(1.,.2,.55)*(1.-a/5.)*(exp(-d*d*.08)*1.3+exp(-d*.05)*.12);
    }

    // ---- into the pet's own frame (rotated, squashed, scaled to its size)
    vec2 q=rot(th)*(uv-C);
    q.x/=max(abs(sq),.12); q.y/=max(sqy,.3);
    vec2 p=q/S;
    float pxl=px/S;
    float L=4.6+2.2*h21(vec2(fi,6.));
    if(p.y>4.8||p.y<-L-1.2||abs(p.x)>3.9+.55*max(-p.y,0.)) continue;
    vec2 vl=(rot(th)*(v+xv))/S;
    vec3 jc=vec3(0);

    // bell
    float bw=1.08-.2*squeeze, bh=.72+.16*squeeze;
    vec2 e=p/vec2(bw,bh);
    float db=e.y>0.?length(e)-1.:max(abs(e.x)-1.+(-e.y)*.35,-e.y-.24);
    float dpx=abs(db)/pxl;
    float gp=.8+.45*squeeze;
    jc+=c1*bright*gp*(exp(-dpx*.5)*1.25+exp(-dpx*.07)*.18);
    if(db<0.){
      float ribs=pow(abs(sin(atan(e.x,e.y+.3)*7.)),10.)*.3;
      float core=exp(-length(e-vec2(0.,.25))*2.4)*.7;
      jc+=mix(c1,c2,.5+.5*e.y)*bright*(.12+ribs*smoothstep(-.2,.6,e.y)+core*gp);
      // face
      vec2 ep=vec2(abs(p.x),p.y)-vec2(.32,.26);
      float eg=0.;
      if(eyeMode<.5){                                  // normal, blinks now and then
        float bp=fract(t*.19+fi*.37), blink=(bp>.97)?.12:1.;
        float de=(length(ep/vec2(1.,blink))-.085)/pxl;
        eg=1.-smoothstep(-1.,1.5,de);
      } else if(eyeMode<1.5){                          // eyes closed (sleepy / bracing for a sneeze)
        float d=sdSeg(ep,vec2(-.09,.01),vec2(.09,.01))/pxl;
        eg=exp(-d*d*.15);
      } else if(eyeMode<2.5){                          // happy ^ ^
        float d=abs(length(ep-vec2(0.,-.07))-.1)/pxl;
        eg=exp(-d*d*.18)*step(-.05,ep.y);
      } else {                                         // shocked O O
        float r=length(ep), de=(r-.13)/pxl;
        eg=(1.-smoothstep(-1.,1.5,de))*(r<.05?.15:1.);
      }
      jc+=vec3(1.,.97,.95)*bright*eg*.9;
      if(smile>0.&&p.y<.17){
        float ds=abs(length(p-vec2(0.,.2))-.17)/pxl;
        jc+=vec3(1.,.95,.95)*smile*exp(-ds*ds*.3)*.8*step(abs(p.x),.15);
      }
      if(ohMouth>0.){
        float d=abs(length((p-vec2(0.,.06))/vec2(1.,1.3))-.065)/pxl;
        jc+=vec3(1.,.95,.95)*ohMouth*exp(-d*d*.25)*.8;
      }
    }

    // tentacles, pinned to the rim, hanging in the pet's own frame
    for(int j=0;j<9;j++){
      float fj=float(j);
      bool oral=j==8;
      vec2 anc=vec2(oral?0.:bw*(-.82+1.64*fj/7.),-.18*bh);
      float s=anc.y-p.y;
      float Lk=oral?L*.55:L*(.82+.18*h21(vec2(fi,fj+20.)));
      if(s<-.06||s>Lk) continue;
      float sc=max(s,0.);
      float fade=pow(1.-sc/Lk,1.3)*smoothstep(-.06,.04,s);
      float grow=smoothstep(0.,1.5,sc);
      float trail=clamp(-vl.x*sc*.35,-sc*.45,sc*.45);
      float swish=-flingDir*fling*sc*sc*.07;
      float spread=oral?0.:splay*(fj-3.5)/3.5*sc*.45;
      if(oral){
        float xa=anc.x+trail*.8+swish+sin(sc*.8-t*1.1+fi)*.3*grow;
        float wa=.2*(1.-sc/Lk)+.02;
        float d=abs(p.x-xa)/wa;
        jc+=c2*bright*.5*exp(-d*d*1.4)*(.55+.45*sin(sc*9.-t*2.6))*fade;
        continue;
      }
      float isArm=(j==6)?armE:0.;
      float amp=(.16+.12*h21(vec2(fi,fj)))*sc*grow*(1.-.6*splay);
      float xk=anc.x+trail+swish+spread+sin(sc*1.3-t*(1.4+.4*h21(vec2(fj,fi)))+fj*1.7)*amp*.4;
      float d=abs(p.x-xk)/pxl;
      float wave=pow(.5+.5*sin(sc*2.6-t*4.5+fi),6.);
      jc+=mix(c1,c2,sc/L)*bright*fade*(1.-isArm)*(exp(-d*d*.3)*(.85+1.1*wave)+exp(-d*.1)*.06);
    }
    // waving arm: a bendy tapered tentacle that swings out and curls up, wave running along it
    if(armE>0.){
      vec2 pt=vec2(bw*(.82-1.64/7.),-.18*bh);
      float dmin=1e9, wAt=1.;
      for(int n=0;n<10;n++){
        float fn=float(n)/10.;
        float wv=sin(t*6.5-fn*3.)*(.25+.6*fn);
        float a2=.15+armE*(1.85+1.15*fn+wv);
        vec2 nx=pt+.26*vec2(sin(a2),-cos(a2));
        float d=sdSeg(p,pt,nx);
        if(d<dmin){ dmin=d; wAt=1.-.65*fn; }
        pt=nx;
      }
      float d=dmin/pxl/max(wAt,.3), dt=length(p-pt)/pxl;
      jc+=mix(c1,c2,.4)*bright*armE*(exp(-d*d*.09)*1.1+exp(-d*.1)*.06+exp(-dt*dt*.08)*.35);
    }
    // little heart bubbles floating up
    if(hearts>0.){
      for(int j=0;j<5;j++){
        float fj=float(j), a=hearts-1.-fj*1.1;
        if(a<0.||a>4.) continue;
        float hs=.32+.08*a;
        vec2 hp=(p-vec2(.45*sin(a*1.8+fj*2.)+.25*(fj-2.),1.05+a*.8))/hs+vec2(0.,.5);
        float d=abs(sdHeart(hp))*hs/pxl;
        jc+=vec3(1.,.22,.55)*hE*(1.-a/4.)*(exp(-d*d*.15)*1.2+exp(-d*.12)*.08);
      }
    }
    // Zzz
    if(zzz>0.){
      for(int j=0;j<3;j++){
        float fj=float(j), a=fract(zzz*.28+fj/3.);
        float zs=(.18+.22*a);
        vec2 zp=(p-vec2(1.+a*.7,.9+a*1.9))/zs;
        float d=min(min(sdSeg(zp,vec2(-1.,1.),vec2(1.,1.)),sdSeg(zp,vec2(1.,1.),vec2(-1.,-1.))),sdSeg(zp,vec2(-1.,-1.),vec2(1.,-1.)))*zs/pxl;
        jc+=vec3(.75,.85,1.)*zE*sin(a*3.14159)*(exp(-d*d*.2)+exp(-d*.15)*.05);
      }
    }
    // sneeze sparkles
    if(sneeze>0.&&sneeze<3.){
      for(int j=0;j<16;j++){
        float fj=float(j), a=fj/16.*6.2831853+h21(vec2(fj,fi))*.5;
        float r=sneeze*(1.6+1.2*h21(vec2(fj,fi+3.)))*(1.-.2*sneeze);
        vec2 sp=vec2(cos(a),sin(a))*r+vec2(0.,.3);
        float d=length(p-sp)/pxl;
        jc+=hsv(h21(vec2(fj,fi+5.)),.7,1.)*exp(-sneeze*1.1)*(exp(-d*d*.08)*1.6+exp(-d*.15)*.1);
      }
    }
    col+=jc*keep;
  }
  col=col/(1.+col*.12);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}""")

# ---------------------------------------------------------------- Prairie Fireflies
SCENES["prairie-fireflies"] = ("Prairie Fireflies", """A summer night on the prairie: the Milky Way wheeling slowly overhead, grass
   bending in the wind, and thousands of fireflies blinking at three depths. The ground is
   exact black; every firefly and star is a native-resolution pinpoint.""", r"""
float grassTop(float x,float y,float t,float lay){
  float base=mix(-.24,-.11,lay)+.025*vn(vec2(x*1.3+lay*9.,lay));
  float lean=sin(t*.55+x*1.7+lay)*.6+sin(t*1.3+x*5.)*.25;
  float top=base;
  for(int i=0;i<3;i++){
    float fi=float(i);
    float f=(16.+fi*13.)*(1.+lay*1.5);
    float xs=x+lean*.012*(1.+fi*.3)*max(y-base,0.)/.1;
    float xx=xs*f+fi*17.;
    float id=floor(xx), fr=fract(xx);
    float hgt=(.05+.13*h21(vec2(id,fi+lay*3.)))*(1.-fi*.22)/(1.+lay*2.2);
    float sp=pow(1.-abs(fr-.5)*2.,1.6);
    top=max(top,base+hgt*sp);
  }
  return top;
}
float fly(vec2 uv,float g,float px,float t,float lay,out vec3 tint){
  vec2 p=uv/g+vec2(t*.01*(1.+lay),lay*31.);
  vec2 id=floor(p), f=p-id; float n=h21(id+lay);
  tint=mix(vec3(.78,1.,.22),vec3(1.,.86,.25),h21(id+5.));
  if(n<.42) return 0.;
  vec2 ph=h22(id+1.3)*TAU;
  vec2 o=.5+.27*vec2(sin(t*(.21+.2*n)+ph.x),sin(t*(.17+.15*n)+ph.y));
  float d=length((f-o)*g)/px;
  float per=3.5+5.*h21(id+8.8);
  float c=fract(t/per+n*13.);
  float on=smoothstep(0.,.05,c)*(1.-smoothstep(.12,.32,c));
  float sz=1./(1.+lay*.9);
  float rad=g/px, edge=1.-smoothstep(.12*rad,.22*rad,d);
  return on*(exp(-d*d*.35*(1.+lay))*1.15+.28*exp(-d*.16/sz)*sz*edge);
}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*R)/R.y;
  float px=1./R.y, t=T;
  vec3 col=vec3(0);
  // sky
  vec2 sp=rot(-.32+.06*sin(t*.003))*(uv-vec2(0.,.17))+vec2(t*.0025,0.);   // band drifts slowly across the sky
  float band=sp.y/.17;
  float mw=exp(-band*band);
  float neb=fbm(sp*vec2(2.2,4.)+3.);
  float dust=smoothstep(.45,.75,fbm(sp*vec2(3.,7.)+9.));
  float glow=mw*max(neb-.38,0.)*(1.-dust*.85);
  col+=glow*mix(vec3(.45,.3,.75),vec3(.95,.75,.6),neb)*1.25;
  col+=stars(sp,.0105,px,.72-.3*mw,t)+stars(sp+5.,.05,px*1.5,.9,t)*1.3;
  col+=vec3(.02,.035,.09)*exp(-max(uv.y+.12,0.)*9.);            // faint horizon glow
  // far grass hides sky
  float g2=grassTop(uv.x,uv.y,t,1.);
  if(uv.y<g2) col=vec3(0);
  // far fireflies (behind the near grass)
  vec3 tint; float f;
  f=fly(uv,.035,px,t,2.,tint); if(uv.y<-.02) col+=tint*f*.7;
  f=fly(uv,.05,px,t,1.,tint);  if(uv.y<.12) col+=tint*f*.85;
  float g1=grassTop(uv.x,uv.y,t,0.);
  if(uv.y<g1) col=vec3(0);
  // near fireflies, over the grass
  f=fly(uv,.08,px,t,0.,tint); if(uv.y<.2) col+=tint*f;
  col=col/(1.+col*.25);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}""")

# ---------------------------------------------------------------- Fractal Dive
SCENES["fractal-dive"] = ("Fractal Dive", """Endless dives into the Mandelbrot set, drawn only as razor-thin neon filaments
   on exact black. The filament width is measured in device pixels, so it gets
   finer and more detailed the higher your screen's resolution. Four dive targets, 75 s each.""", r"""
vec2 target(float k){
  if(k<.5) return vec2(-0.743643887,0.131825904);
  if(k<1.5) return vec2(-0.761574,-0.0847596);
  if(k<2.5) return vec2(-1.25066,0.02012);
  return vec2(-0.7746806106,-0.1374168856);
}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*R)/R.y;
  float t=T, Ln=75.;
  float cyc=floor(t/Ln), ph=fract(t/Ln);
  float k=mod(cyc,4.);
  float e=ph*.85+smoothstep(0.,1.,ph)*.15;
  float scale=2.6*exp(-e*log(2.6/5e-4));
  float fade=smoothstep(0.,.05,ph)*(1.-smoothstep(.93,1.,ph));
  vec2 c=target(k)+rot(t*.035+k*1.3)*uv*scale;
  float px=scale/R.y;
  // skip the main cardioid and period-2 bulb (they'd only burn iterations, they're black anyway)
  float q=(c.x-.25)*(c.x-.25)+c.y*c.y;
  if(q*(q+(c.x-.25))<.25*c.y*c.y||(c.x+1.)*(c.x+1.)+c.y*c.y<.0625){ gl_FragColor=vec4(0,0,0,1); return; }
  int maxIt=int(min(400.,110.+40.*log2(2.6/scale)));
  vec2 z=vec2(0), dz=vec2(0); float m=0.; float it=0.; bool esc=false;
  for(int i=0;i<400;i++){
    if(i>=maxIt) break;
    dz=2.*vec2(z.x*dz.x-z.y*dz.y,z.x*dz.y+z.y*dz.x)+vec2(1,0);
    z=vec2(z.x*z.x-z.y*z.y,2.*z.x*z.y)+c;
    m=dot(z,z);
    if(m>1024.){ esc=true; it=float(i); break; }
  }
  vec3 col=vec3(0);
  if(esc){
    float de=.5*sqrt(m)*log(m)/max(length(dz),1e-20);
    float d=de/px;
    float sn=it+1.-log2(log2(m)*.5);
    vec3 hc=hsv(fract(sn*.018+t*.012+k*.25),.85,1.);
    col=hc*(exp(-d*d*.45)*1.1+exp(-d*.22)*.22);
  }
  col*=fade;
  col=col/(1.+col*.2);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}""")

PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__</title>
<style>html,body{margin:0;height:100%;background:#000;overflow:hidden}canvas{display:block;width:100vw;height:100vh}</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
/* web.walls — __TITLE__  (OLED showcase, v0.8)
   __DESC__
   Renders at the screen's exact device pixels, up to 8K (7680x4320 worth), and animates
   from real time so it's equally smooth at 60, 120, 144 or 240 Hz.
   Generated by tools/gen_oled.py — edit there.
   URL options: ?scale=0.75 (render scale), ?adaptive=0 (never drop resolution), ?t=600 (jump the scene clock) */
(() => {
const qs = new URLSearchParams(location.search);
const USER_SCALE = Math.min(Math.max(parseFloat(qs.get('scale')) || 1, 0.25), 2);
const ADAPTIVE = qs.get('adaptive') !== '0';
const MAX_PIXELS = 7680 * 4320;   // 8K ceiling

const c = document.getElementById('c');
const gl = c.getContext('webgl', { antialias: false, alpha: false, depth: false, stencil: false,
  powerPreference: 'high-performance', desynchronized: true, preserveDrawingBuffer: false });
if (!gl) return;

const VS = `attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}`;
const FS = `__FS__`;

function sh(type, src) {
  const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}
const pr = gl.createProgram();
gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS));
gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS));
gl.linkProgram(pr); gl.useProgram(pr);
gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(pr, 'a');
gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
const uR = gl.getUniformLocation(pr, 'R'), uT = gl.getUniformLocation(pr, 'T');

// ---- native-resolution sizing: exact device pixels, capped at 8K ----
let cssW = innerWidth, cssH = innerHeight, devW = 0, devH = 0, scale = USER_SCALE;
function apply() {
  const dpr = window.devicePixelRatio || 1;
  const w = devW || Math.round(cssW * dpr), h = devH || Math.round(cssH * dpr);
  let s = scale;
  if (w * h * s * s > MAX_PIXELS) s = Math.sqrt(MAX_PIXELS / (w * h));
  c.width = Math.max(1, Math.round(w * s));
  c.height = Math.max(1, Math.round(h * s));
  gl.viewport(0, 0, c.width, c.height);
}
try {
  new ResizeObserver(e => {
    const en = e[0];
    cssW = en.contentRect.width; cssH = en.contentRect.height;
    const d = en.devicePixelContentBoxSize && en.devicePixelContentBoxSize[0];
    devW = d ? d.inlineSize : 0; devH = d ? d.blockSize : 0;
    apply();
  }).observe(c, { box: 'device-pixel-content-box' });
} catch (_) {
  addEventListener('resize', () => { cssW = innerWidth; cssH = innerHeight; devW = devH = 0; apply(); });
}
apply();

// ---- adaptive guard: only steps resolution down if the GPU truly can't hold the refresh rate ----
let last = 0, ivs = [], target = 0, slow = 0;
function adapt(dt) {
  if (!ADAPTIVE) return;
  if (!target) { ivs.push(dt); if (ivs.length === 120) { ivs.sort((a, b) => a - b); target = ivs[60]; } return; }
  if (dt > target * 1.45) slow++; else slow = Math.max(0, slow - 1);
  if (slow > 60 && scale > USER_SCALE * 0.6) { scale *= 0.92; slow = 0; apply(); }
}

// Scene clock loops every 30 min. Graphics cards round big numbers, so a clock that just keeps counting
// makes long-running scenes stutter and grow stripes after a few hours. At the loop point the screen
// dips to black for a moment so the jump is never seen.
const LOOP = 1800, DIP = 0.8, HOLD = qs.has('hold');   // ?hold freezes the clock at ?t (testing / screenshots)
const t0 = performance.now(), seed = qs.has('t') ? parseFloat(qs.get('t')) - 10 : (Date.now() / 1000) % LOOP;   // ?t= jumps the clock (testing)
let dipped = false;
let raf = 0;
function frame(now) {
  raf = requestAnimationFrame(frame);
  if (last) adapt(now - last);
  last = now;
  gl.uniform2f(uR, c.width, c.height);
  const tt = ((((HOLD ? 0 : now - t0) / 1000) + seed) % LOOP + LOOP) % LOOP;
  const edge = Math.min(tt, LOOP - tt);
  const op = Math.max(0, Math.min(1, edge / DIP));
  if (op < 1 || dipped) { c.style.opacity = op.toFixed(3); dipped = op < 1; }
  gl.uniform1f(uT, tt + 10);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { cancelAnimationFrame(raf); raf = 0; }
  else if (!raf) { last = 0; raf = requestAnimationFrame(frame); }
});
c.addEventListener('webglcontextlost', e => { e.preventDefault(); cancelAnimationFrame(raf); raf = 0; });
c.addEventListener('webglcontextrestored', () => location.reload());
raf = requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""

def main():
    for slug, (title, desc, fs) in SCENES.items():
        html = PAGE.replace("__TITLE__", title).replace("__DESC__", desc).replace("__FS__", COMMON + fs)
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")
        print("wrote", slug)

if __name__ == "__main__":
    main()
