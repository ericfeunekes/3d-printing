"""Self-contained WebGL inspection viewer using actual world-coordinate meshes.

No CDN, network requests, analytical geometry substitutes or physics claims.
"""
from pathlib import Path
import sys,json,base64,argparse
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scene_data import load_configuration,COLORS

def encoded(a,dtype):
    return base64.b64encode(np.asarray(a,dtype=dtype).tobytes()).decode()

def build(final_shells=False):
    geometries={};configs={};meta={}
    for conf in ['core','recommended']:
        parts,m=load_configuration(conf,final_shells=final_shells);meta[conf]=m['geometry_status'];configs[conf]=[]
        graph=m['source_metadata']['elastic_graph']
        for p in parts:
            key=p['key'];configs[conf].append(key)
            if key in geometries:continue
            mesh=p['mesh'];v=mesh.vertices
            if p['motion']=='film':
                r=np.linalg.norm(v[:,:2],axis=1);w=np.clip((116.8533-r)/(116.8533-20),0,1)
            elif p['motion']=='band':
                k=int(key.rsplit('-',1)[1]);a,b=graph['edges'][k]
                p0,p1=np.asarray(graph['nodes'][a]),np.asarray(graph['nodes'][b]);delta=p1-p0
                progress=np.clip((v-p0)@delta/(delta@delta),0,1)
                mapping={'front_left':0,'front_right':0,'carabiner':.5,'membrane_centre':1}
                w=mapping[a]+progress*(mapping[b]-mapping[a])
            else:w=np.full(len(v),p['motion'])
            geometries[key]={'name':p['name'],'role':p['role'],'color':[x/255 for x in COLORS[p['role']]],
                'vertices':encoded(v,'<f4'),'normals':encoded(mesh.vertex_normals,'<f4'),
                'weights':encoded(w,'<f4'),'indices':encoded(mesh.faces.reshape(-1),'<u4'),
                'vertex_count':len(v),'index_count':mesh.faces.size}
    data={'geometries':geometries,'configs':configs,'status':meta,'final_shells':final_shells}
    html=TEMPLATE.replace('__MODEL_DATA__',json.dumps(data,separators=(',',':')))
    (HERE/'inspection-viewer.html').write_text(html)
    print('Wrote self-contained viewer:',len(html),'bytes,',len(geometries),'mesh buffers')

TEMPLATE=r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Air-vortex cannon — core, proposed design and options</title>
<style>
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,sans-serif;color:#173246;background:#f3f6f8}
header{padding:24px 30px 14px;background:white;border-bottom:1px solid #d9e3e9}h1{margin:0;font-size:27px;letter-spacing:-.5px}p{margin:7px 0}.sub{color:#5a7181}
main{display:grid;grid-template-columns:minmax(500px,1fr) 320px;gap:16px;padding:18px;max-width:1700px;margin:auto}.stage{background:white;border:1px solid #d9e3e9;border-radius:14px;overflow:hidden}.toolbar{display:flex;gap:8px;align-items:center;padding:12px;flex-wrap:wrap;border-bottom:1px solid #e2e9ed}
button{background:#edf3f6;border:1px solid #cedce4;border-radius:8px;padding:9px 13px;color:#173246;font:inherit;cursor:pointer}button.active{background:#174c68;color:white;border-color:#174c68}.spacer{flex:1}label{display:inline-flex;align-items:center;gap:7px;cursor:pointer}canvas{display:block;width:100%;height:620px;background:linear-gradient(#f7fafc,#edf3f7);touch-action:none}
.motion{padding:15px 18px;border-top:1px solid #e2e9ed}.motion label{display:block;font-weight:600}.motion input{width:min(560px,85%);vertical-align:middle;accent-color:#236f92}.motion output{font-variant-numeric:tabular-nums;margin-left:12px}.note{font-size:13px;color:#647c8d;padding-top:4px}
aside{display:flex;flex-direction:column;gap:12px}.card{background:white;border:1px solid #d9e3e9;border-radius:12px;padding:17px}.card h2{margin:0 0 7px;font-size:18px}.tag{font-size:11px;letter-spacing:.8px;font-weight:750;color:#236f92}.card ol{margin:7px 0;padding-left:20px}.card li{margin:5px 0}.small{font-size:13px;color:#5a7181}.proof{border-left:4px solid #d99a47}.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;padding:11px 17px;color:#4d6575}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}#status{font-size:12px;padding:0 17px 11px;color:#5f788a;word-break:break-word}@media(max-width:1000px){main{grid-template-columns:1fr}aside{display:grid;grid-template-columns:repeat(3,1fr)}canvas{height:560px}}@media(max-width:700px){main{display:block;padding:8px}aside{display:block}.card{margin-top:10px}canvas{height:480px}header{padding:15px}h1{font-size:22px}}
</style>
<header><h1>A handheld air-vortex cannon, made reviewable</h1><p class="sub">Original core → proposed mechanical revision → optional experiments. Drag to orbit; scroll to zoom.</p></header>
<main><section class="stage"><div class="toolbar"><button id="core" class="active">Core design</button><button id="recommended">Our proposed design</button><span class="spacer"></span><label><input id="cutaway" type="checkbox">Shell cutaway</label><button id="reset">Reset view</button></div>
<canvas id="canvas" aria-label="Interactive full air-vortex cannon CAD assembly"></canvas>
<div class="motion"><label for="travel">Assumed pull travel</label><input id="travel" aria-label="Assumed pull travel" type="range" min="0" max="60" step="1" value="0"><output id="amount">0 mm</output><div class="note">An illustrative movement envelope, not a recommended limit. Film shape and elastic junction are schematic; no fluid simulation is implied.</div></div>
<div class="legend"><span><i class="dot" style="background:#4182aa"></i>Chamber</span><span><i class="dot" style="background:#2c8e96"></i>Rails / grip</span><span><i class="dot" style="background:#e7973d"></i>Printed keyed adapters</span><span><i class="dot" style="background:#9ba4af"></i>Hardware references</span></div><div id="status">Loading local model buffers…</div></section>
<aside><div class="card"><div class="tag">1 · CORE</div><h2>Keep the useful mechanism</h2><p>Original chamber, outlet, manual diaphragm, grip and sights provide the baseline.</p><p class="small">Seventeen source meshes are placed from recovered mating datums and designer assembly evidence. Source snap behavior remains unverified.</p></div>
<div class="card"><div class="tag">2 · PROPOSED</div><h2>Capture the joints deliberately</h2><ol><li>Replace split clips with keyed printed spacers and shoulder-bolt reference hardware.</li><li>Integrate local reinforcement around the shell slots.</li><li>Use the shoulder and washer as a spacing stop; credit no clamp friction.</li></ol><p class="small">Metal parts are hardware references, not files to print. Exact purchased hardware and its fit still need verification.</p></div>
<div class="card proof"><div class="tag">3 · OPTIONAL</div><h2>Measure before changing airflow</h2><p>Repeatable pull reference, sight calibration and controlled outlet comparisons are separate experiments.</p><p class="small">This model shows nominal geometry and motion. Actual printed strength, nut locking, wear, membrane dynamics, aim and ring coherence are not proven by a viewer.</p></div></aside></main>
<script>
const DATA=__MODEL_DATA__;
const canvas=document.querySelector('#canvas'),status=document.querySelector('#status');
const gl=canvas.getContext('webgl2',{antialias:true,alpha:false});
if(!gl){status.textContent='WebGL 2 is unavailable. Use the supplied static CAD views and GLB files.';throw Error('WebGL2 unavailable')}
const vs=`#version 300 es
in vec3 position;in vec3 normal;in float weight;uniform mat4 vp;uniform float stroke;out vec3 N;out vec3 P;
void main(){P=position+vec3(0.,0.,stroke*weight);N=normal;gl_Position=vp*vec4(P,1.);}`;
const fs=`#version 300 es
precision highp float;in vec3 N;in vec3 P;uniform vec4 color;uniform bool cut;uniform bool shell;out vec4 frag;
void main(){if(cut&&shell&&P.x<0.)discard;vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;float s=.48+.45*max(dot(n,normalize(vec3(-.4,.8,-.3))),0.);frag=vec4(color.rgb*s,color.a);}`;
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
let prog=gl.createProgram();gl.attachShader(prog,shader(gl.VERTEX_SHADER,vs));gl.attachShader(prog,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(prog));gl.useProgram(prog);
const loc={vp:gl.getUniformLocation(prog,'vp'),stroke:gl.getUniformLocation(prog,'stroke'),color:gl.getUniformLocation(prog,'color'),cut:gl.getUniformLocation(prog,'cut'),shell:gl.getUniformLocation(prog,'shell')};
function bytes(s){let raw=atob(s),a=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)a[i]=raw.charCodeAt(i);return a}
function attr(name,s,size){let b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,bytes(s),gl.STATIC_DRAW);let p=gl.getAttribLocation(prog,name);gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,size,gl.FLOAT,false,0,0)}
const meshes={};for(const [key,m] of Object.entries(DATA.geometries)){let vao=gl.createVertexArray();gl.bindVertexArray(vao);attr('position',m.vertices,3);attr('normal',m.normals,3);attr('weight',m.weights,1);let b=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,b);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,bytes(m.indices),gl.STATIC_DRAW);meshes[key]={vao,count:m.index_count,color:m.color,role:m.role};delete m.vertices;delete m.normals;delete m.weights;delete m.indices}
function norm(a){let n=Math.hypot(...a);return a.map(x=>x/n)}function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}function dot(a,b){return a.reduce((s,x,i)=>s+x*b[i],0)}
function mul(a,b){let o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o}
function look(eye,target){let z=norm(eye.map((x,i)=>x-target[i])),x=norm(cross([0,1,0],z)),y=cross(z,x);return[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]}
function perspective(aspect){let f=1/Math.tan(Math.PI/9),n=10,far=5000,q=1/(n-far);return[f/aspect,0,0,0,0,f,0,0,0,0,(far+n)*q,-1,0,0,2*far*n*q,0]}
let conf='core',az=-2.447,el=.34,distance=740,drag=null,dirty=true;
function reset(){az=-2.447;el=.34;distance=740;dirty=true}document.querySelector('#reset').onclick=reset;
for(const c of ['core','recommended'])document.querySelector('#'+c).onclick=()=>{conf=c;for(const q of ['core','recommended'])document.querySelector('#'+q).classList.toggle('active',q===c);dirty=true};
document.querySelector('#cutaway').onchange=()=>dirty=true;document.querySelector('#travel').oninput=e=>{document.querySelector('#amount').textContent=e.target.value+' mm';dirty=true};
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;az-=(e.clientX-drag[0])*.008;el=Math.max(-1.2,Math.min(1.2,el+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];dirty=true};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();distance=Math.max(300,Math.min(1800,distance*Math.exp(e.deltaY*.001)));dirty=true};canvas.ondblclick=reset;
gl.enable(gl.DEPTH_TEST);gl.clearColor(.962,.976,.984,1);gl.disable(gl.CULL_FACE);
function draw(){requestAnimationFrame(draw);let dpr=Math.min(2,devicePixelRatio||1),w=Math.round(canvas.clientWidth*dpr),h=Math.round(canvas.clientHeight*dpr);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;dirty=true}if(!dirty)return;dirty=false;gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);let target=[0,-12,150],eye=[target[0]+distance*Math.cos(el)*Math.sin(az),target[1]+distance*Math.sin(el),target[2]+distance*Math.cos(el)*Math.cos(az)];gl.uniformMatrix4fv(loc.vp,false,mul(perspective(w/h),look(eye,target)));gl.uniform1f(loc.stroke,+document.querySelector('#travel').value);gl.uniform1i(loc.cut,document.querySelector('#cutaway').checked);let keys=DATA.configs[conf];for(const transparent of [false,true]){if(transparent){gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false)}else{gl.disable(gl.BLEND);gl.depthMask(true)}for(const key of keys){const m=meshes[key];if((m.role==='film')!==transparent)continue;gl.bindVertexArray(m.vao);gl.uniform4fv(loc.color,m.color);gl.uniform1i(loc.shell,m.role==='shell');gl.drawElements(gl.TRIANGLES,m.count,gl.UNSIGNED_INT,0)}}gl.depthMask(true);let rigid=conf==='core'?17:41;status.textContent=(conf==='core'?'Core':'Proposed')+' · '+rigid+' rigid modeled pieces · units mm · '+DATA.status[conf]}
window.addEventListener('error',e=>{status.textContent='Viewer error: '+e.message});draw();
</script></html>'''

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final-shells',action='store_true');args=p.parse_args();build(args.final_shells)
