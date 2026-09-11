(function () {
  "use strict";

  const PALETTES = {
    earth:{sea:["#143c78","#1e5aa0"],land:["#3c8c50","#8ca05a","#beaa6e"],ring:"#00ffff"},
    desert:{sea:["#785a32","#a0783c"],land:["#d2aa64","#f0c882","#b48c50"],ring:"#966805"},
    lava:{sea:["#280a0a","#46140f"],land:["#b42814","#ff501e","#78140a"],ring:"#642626"},
    toxic:{sea:["#145028","#287832"],land:["#64c83c","#96ff50","#3c8c28"],ring:"#966805"},
    ice:{sea:["#285082","#4678b4"],land:["#c8e6ff","#f0faff","#96c8e6"],ring:"#00ffff"},
    ocean:{sea:["#0a1e5a","#144696"],land:["#507864","#789678","#6ea58a"],ring:"#a5c0f5"},
    alien:{sea:["#3c005a","#7800a0"],land:["#c800ff","#9632ff","#ff64c8"],ring:"#7e49d4"},
    forest:{sea:["#1e3c50","#326478"],land:["#147828","#28a03c","#50b450"],ring:"#a5c0f5"},
    gas:{sea:["#96503c","#c8785a"],land:["#f0b478","#ffdc96","#d99567"],ring:"#a5c0f5"},
    mono:{sea:["#3c3c3c","#5a5a5a"],land:["#969696","#c8c8c8","#aeaeae"],ring:"#a5c0f5"}
  };
  const FRAME_COLORS={hover:"#00ffff",pressed:"#008383",disabled:"#808080"};
  const THEMES = {
    deep_blue:{top:"#030410",bottom:"#080e26",nebula:["#2846a0","#5a8cdc","#a0beff"],stars:["#7896dc","#bed2ff","#fff5dc"]},
    red_nebula:{top:"#0c0308",bottom:"#260a12",nebula:["#781923","#c8463c","#ffa06e"],stars:["#dc9682","#ffdcbe","#fff5e1"]},
    white_bright:{top:"#08080e",bottom:"#161624",nebula:["#5a6482","#aab4d2","#f5f5ff"],stars:["#b4bedc","#ebebf5","#ffffff"]},
    purple_magenta:{top:"#080312",bottom:"#1c0a2d",nebula:["#501e82","#b446aa","#ffa0dc"],stars:["#9678dc","#e6beff","#fff0ff"]},
    cold_white:{top:"#04080e",bottom:"#0e1c2a",nebula:["#466e82","#a0d2dc","#ebffff"],stars:["#aad2e6","#e6faff","#ffffff"]}
  };

  const clamp=(v,min=0,max=255)=>Math.max(min,Math.min(max,v));
  const hash=(x,y,seed)=>{let h=(Math.imul(x|0,374761393)+Math.imul(y|0,668265263)+Math.imul(seed|0,1442695041))|0;h=Math.imul(h^(h>>>13),1274126177);return((h^(h>>>16))>>>0)/4294967295};
  const smooth=t=>t*t*(3-2*t);
  function valueNoise(x,y,seed,period=0){
    const x0=Math.floor(x),y0=Math.floor(y),tx=smooth(x-x0),ty=smooth(y-y0);
    const wrap=v=>period?((v%period)+period)%period:v;
    const a=hash(wrap(x0),wrap(y0),seed),b=hash(wrap(x0+1),wrap(y0),seed),c=hash(wrap(x0),wrap(y0+1),seed),d=hash(wrap(x0+1),wrap(y0+1),seed);
    return(a+(b-a)*tx)+((c+(d-c)*tx)-(a+(b-a)*tx))*ty;
  }
  function fractal(x,y,seed,period=0){let sum=0,weight=0,amp=1;for(let i=0;i<4;i++){const f=2**i/18;sum+=valueNoise(x*f,y*f,seed+i*7919,period?Math.max(1,Math.round(period*f)):0)*amp;weight+=amp;amp*=.52}return sum/weight}
  function rgb(hex){const n=parseInt(hex.replace("#",""),16);return[(n>>16)&255,(n>>8)&255,n&255]}
  function mix(a,b,t){const ar=rgb(a),br=rgb(b);return[ar[0]+(br[0]-ar[0])*t,ar[1]+(br[1]-ar[1])*t,ar[2]+(br[2]-ar[2])*t]}
  function makeRng(seed){let a=(seed|0)||1;return()=>{a|=0;a=a+0x6d2b79f5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
  function put(data,w,x,y,color,alpha=255){if(x<0||y<0||x>=w||y>=data.length/4/w)return;const p=(y*w+x)*4;data[p]=color[0];data[p+1]=color[1];data[p+2]=color[2];data[p+3]=alpha}
  function ringPixels(data,size,cx,cy,radius,color,front,tilt=.42,width=.28){
    const outerRx=radius*1.75,outerRy=radius*tilt,innerRx=radius*(1.75-width),innerRy=radius*Math.max(.08,tilt-width*.45),c=rgb(color);
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){const dx=x-cx,dy=y-cy,o=(dx/outerRx)**2+(dy/outerRy)**2,i=(dx/innerRx)**2+(dy/innerRy)**2;if(i>1&&o<1){if((front&&dy<0)||(!front&&dy>0))continue;const dist=Math.hypot(dx,dy);if(!front&&dist<radius)continue;put(data,size,x,y,c,clamp(170*(1-Math.abs(o-.75)),50,170))}}
  }
  function cornerFrame(data,size,color){const c=rgb(color),corner=Math.max(8,Math.round(size*.125)),thick=Math.max(1,Math.round(size/48)),pad=Math.max(2,Math.round(size/24));for(let i=0;i<corner;i++)for(let t=0;t<thick;t++)[[pad+i,pad+t],[pad+t,pad+i],[size-pad-1-i,pad+t],[size-pad-1-t,pad+i],[pad+i,size-pad-1-t],[pad+t,size-pad-1-i],[size-pad-1-i,size-pad-1-t],[size-pad-1-t,size-pad-1-i]].forEach(p=>put(data,size,p[0],p[1],c))}

  function renderPlanet(canvas,options,frameIndex=0,totalFrames=1){
    const size=options.size,scale=options.scale,palette=options.palette||PALETTES[options.style],base=document.createElement("canvas");base.width=base.height=size;const ctx=base.getContext("2d"),image=ctx.createImageData(size,size),data=image.data,cx=size/2,cy=size/2,radius=size*.263,phase=totalFrames>1?frameIndex/totalFrames:0,offset=phase*size,targetOcean=clamp(Number(options.oceanRatio)||60,30,90)/100,terrainMap=new Float32Array(size*size),terrainValues=[];
    if(options.ring)ringPixels(data,size,cx,cy,radius,palette.ring,false,.42,.28);
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){if(Math.hypot(x-cx,y-cy)>radius)continue;const terrain=fractal(x+offset,y,options.seed,size);terrainMap[y*size+x]=terrain;terrainValues.push(terrain)}
    const sortedTerrain=[...terrainValues].sort((a,b)=>a-b),landLevel=sortedTerrain[Math.max(0,Math.min(sortedTerrain.length-1,Math.ceil(sortedTerrain.length*targetOcean)-1))];let oceanPixels=0;
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const dx=x-cx,dy=y-cy,dist=Math.hypot(dx,dy);if(dist>radius)continue;
      const nx=dx/radius,ny=dy/radius,terrain=terrainMap[y*size+x],land=terrain>landLevel,colors=land?palette.land:palette.sea;if(!land)oceanPixels++;
      let color=rgb(colors[Math.min(colors.length-1,Math.floor(hash(x,y,options.seed+99)*colors.length))]);if(Math.abs(terrain-landLevel)<.035)color=color.map(v=>clamp(v*1.3));
      const edge=1-dist/radius,light=.64+.36*Math.max(0,(-nx-ny+1)/2),jitter=.88+hash(x,y,options.seed+211)*.24,shade=light*(.55+edge*.45)*jitter;
      put(data,size,x,y,color.map(v=>clamp(v*shade)));
    }
    if(options.ring)ringPixels(data,size,cx,cy,radius,palette.ring,true,.42,.28);if(options.frame)cornerFrame(data,size,options.frameColor||palette.frame||FRAME_COLORS.hover);
    ctx.putImageData(image,0,0);canvas.width=canvas.height=size*scale;canvas.dataset.oceanRatio=String(Math.round(targetOcean*100));canvas.dataset.actualOceanRatio=(oceanPixels/terrainValues.length*100).toFixed(1);const out=canvas.getContext("2d");out.imageSmoothingEnabled=false;out.clearRect(0,0,canvas.width,canvas.height);out.drawImage(base,0,0,canvas.width,canvas.height);return canvas;
  }

  function drawWrapped(ctx,x,y,w,h,seamless,draw){const xs=[x],ys=[y];if(seamless==="horizontal"||seamless==="both")xs.push(x-w,x+w);if(seamless==="vertical"||seamless==="both")ys.push(y-h,y+h);xs.forEach(px=>ys.forEach(py=>draw(px,py)))}
  function renderGalaxy(canvas,options,frameIndex=0,totalFrames=1){
    const w=options.width,h=options.height,theme=options.themeData||THEMES[options.theme],seed=options.seed,rng=makeRng(seed),phase=totalFrames>1?frameIndex/totalFrames:0,seamless=options.seamless||"none",starRatio=clamp(Number(options.starRatio)||60,30,90),densityScale=starRatio/60,spiralStarCount=options.spiral?Math.round(w*h/190*densityScale):0,fieldStarCount=Math.round(w*h/260*densityScale);canvas.width=w;canvas.height=h;const ctx=canvas.getContext("2d"),image=ctx.createImageData(w,h),top=rgb(theme.top),bottom=rgb(theme.bottom);
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=(y*w+x)*4,t=y/Math.max(1,h-1),n=(hash(x,y,seed)-.5)*7;image.data[p]=clamp(top[0]+(bottom[0]-top[0])*t+n);image.data[p+1]=clamp(top[1]+(bottom[1]-top[1])*t+n);image.data[p+2]=clamp(top[2]+(bottom[2]-top[2])*t+n);image.data[p+3]=255}ctx.putImageData(image,0,0);
    ctx.globalCompositeOperation="screen";
    for(let i=0;i<10;i++){
      const x=rng()*w,y=rng()*h,rx=(.08+rng()*.2)*w,ry=(.04+rng()*.12)*h,color=theme.nebula[i%theme.nebula.length];
      drawWrapped(ctx,x,y,w,h,seamless,(px,py)=>{
        const g=ctx.createRadialGradient(px,py,0,px,py,Math.max(rx,ry));g.addColorStop(0,color+"45");g.addColorStop(1,color+"00");ctx.fillStyle=g;ctx.save();ctx.translate(px,py);ctx.scale(1,ry/rx);ctx.beginPath();ctx.arc(0,0,rx,0,Math.PI*2);ctx.fill();ctx.restore();
      });
    }
    if(options.spiral){
      const cx=w*.5,cy=h*.5,armCount=3;
      for(let i=0;i<spiralStarCount;i++){
        const arm=i%armCount,r=(rng()**.62)*Math.min(w,h)*.48,angle=arm*Math.PI*2/armCount+r*.045+(rng()-.5)*.5+phase*Math.PI*2,x=cx+Math.cos(angle)*r*1.15,y=cy+Math.sin(angle)*r*.58,size=rng()<.08?2:1,color=theme.stars[Math.floor(rng()*theme.stars.length)];
        drawWrapped(ctx,x,y,w,h,seamless,(px,py)=>{ctx.globalAlpha=.18+rng()*.55;ctx.fillStyle=color;ctx.fillRect(Math.round(px),Math.round(py),size,size);});
      }
    }
    ctx.globalAlpha=1;ctx.globalCompositeOperation="source-over";
    for(let i=0;i<fieldStarCount;i++){
      // Seamless wrapping only affects edge copies; field stars twinkle in place.
      const x=rng()*w,y=rng()*h;
      const flash=.45+.55*Math.abs(Math.sin((phase+rng())*Math.PI*2)),size=rng()<.07?3:(rng()<.25?2:1),color=theme.stars[Math.floor(rng()*theme.stars.length)];
      drawWrapped(ctx,x,y,w,h,seamless,(px,py)=>{ctx.globalAlpha=flash;ctx.fillStyle=color;ctx.fillRect(Math.round(px),Math.round(py),size,size);if(size===3){ctx.fillRect(Math.round(px)-1,Math.round(py)+1,5,1);ctx.fillRect(Math.round(px)+1,Math.round(py)-1,1,5);}});
    }
    ctx.globalAlpha=1;canvas.dataset.starRatio=String(starRatio);canvas.dataset.starCount=String(fieldStarCount+spiralStarCount);return canvas;
  }

  window.PixelPlanetRenderer={PALETTES,THEMES,FRAME_COLORS,renderPlanet,renderGalaxy};
})();
