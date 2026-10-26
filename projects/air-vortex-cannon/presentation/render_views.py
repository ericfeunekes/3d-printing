"""CPU orthographic triangle presentation from actual model meshes.

Painter shading is for inspection/presentation only, not a collision solver.
"""
from pathlib import Path
import sys,argparse
import numpy as np,trimesh
from PIL import Image,ImageDraw,ImageFont
import matplotlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scene_data import load_configuration,COLORS
FONT=Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf'
def font(n):return ImageFont.truetype(str(FONT),n)

def camera(direction):
    eye=np.asarray(direction,float);eye/=np.linalg.norm(eye)
    right=np.cross([0,1,0],eye);right/=np.linalg.norm(right)
    up=np.cross(eye,right)
    return right,up,eye

def raster(parts,width=1100,height=1000,cutaway=False,direction=(-1,.48,-1.2),crop=None):
    right,up,eye=camera(direction)
    rows=[];coordinates=[]
    for p in parts:
        m=p['mesh']
        if cutaway and p['role']=='shell':
            m=trimesh.intersections.slice_mesh_plane(m,[1,0,0],[0,0,0],cap=False)
        if crop is not None:
            lo,hi=np.asarray(crop[0]),np.asarray(crop[1])
            for axis in range(3):
                normal=np.eye(3)[axis]
                m=trimesh.intersections.slice_mesh_plane(m,normal,lo,cap=False)
                if not len(m.faces):break
                m=trimesh.intersections.slice_mesh_plane(m,-normal,hi,cap=False)
                if not len(m.faces):break
            if not len(m.faces):continue
        normals=m.face_normals
        use=np.ones(len(normals),bool) if p['role']=='film' else normals@eye>0
        if not use.any():continue
        tri=m.triangles[use]
        n=normals[use]
        if p['role']=='film':n=np.where((n@eye>0)[:,None],n,-n)
        projected=np.stack([tri@right,tri@up],axis=-1)
        depth=(tri@eye).mean(1)
        light=np.array([-.4,.8,-.3]);light/=np.linalg.norm(light)
        shade=.48+.48*np.maximum(0,n@light)
        colors=np.asarray(COLORS[p['role']],float)
        if p['role']=='film':colors=np.array([211.,222.,230.,255.])
        rgb=np.clip(shade[:,None]*colors[:3],0,255).astype(np.uint8)
        alpha=np.full((len(rgb),1),colors[3],dtype=np.uint8)
        rows.append((projected,depth,np.column_stack([rgb,alpha])))
        coordinates.append(projected.reshape(-1,2))
    cloud=np.concatenate(coordinates)
    lo,hi=cloud.min(0),cloud.max(0)
    scale=min((width-60)/(hi[0]-lo[0]),(height-60)/(hi[1]-lo[1]))
    centre=(lo+hi)/2
    def project(points):
        pp=np.stack([np.asarray(points)@right,np.asarray(points)@up],axis=-1)
        return np.column_stack([(pp[...,0]-centre[0])*scale+width/2,
                                height/2-(pp[...,1]-centre[1])*scale])
    tris=np.concatenate([r[0] for r in rows]);depth=np.concatenate([r[1] for r in rows]);color=np.concatenate([r[2] for r in rows])
    pix=np.empty_like(tris)
    pix[:,:,0]=(tris[:,:,0]-centre[0])*scale+width/2
    pix[:,:,1]=height/2-(tris[:,:,1]-centre[1])*scale
    pix=np.rint(pix).astype(np.int32)
    im=Image.new('RGB',(width,height),(246,249,251));draw=ImageDraw.Draw(im,'RGBA')
    for k in np.argsort(depth):
        draw.polygon([tuple(q) for q in pix[k]],fill=tuple(int(c) for c in color[k]))
    return im,project

def text(draw,xy,s,n=24,fill='#1b3447',anchor=None):
    draw.text(xy,s,font=font(n),fill=fill,anchor=anchor)

def line_label(draw,project,point,label,at,color='#42576a'):
    xy=project(np.array([point]))[0]
    draw.line([tuple(xy),at],fill=color,width=2)
    draw.ellipse((xy[0]-4,xy[1]-4,xy[0]+4,xy[1]+4),fill=color)
    text(draw,(at[0]+7,at[1]-14),label,20,color)

def make_comparison(final_shells=False):
    configs=[]
    for c in ['core','recommended']:
        p,meta=load_configuration(c,final_shells=final_shells)
        configs.append((p,meta))
    canvas=Image.new('RGB',(2320,1390),'white');draw=ImageDraw.Draw(canvas)
    text(draw,(70,45),'Handheld air-vortex cannon: core and proposed revision',38)
    text(draw,(70,101),'Same chamber, diaphragm and manual elastic concept; a different way to retain the structural joints.',24,'#5d7281')
    for k,((parts,meta),title) in enumerate(zip(configs,['CORE · original source geometry','OURS · proposed mechanical capture'])):
        im,proj=raster(parts,1100,1000,cutaway=False)
        canvas.paste(im,(40+k*1140,200))
        text(draw,(75+k*1140,160),title,27)
        text(draw,(75+k*1140,1220),'17 rigid printed pieces' if k==0 else 'Local reinforced shells + keyed adapters + metal reference hardware',21)
    text(draw,(70,1280),'Geometry is inspectable; actual printed strength, nut locking, membrane behavior and ring performance remain unproved.',23,'#725335')
    if not final_shells:text(draw,(70,1320),'PREVIEW: original shells plus separate collar overlays. Final fused shell export has not yet been substituted.',20,'#ad4336')
    canvas.save(HERE/'core-vs-proposed.png')
    # Recommended half-shell cutaway retains all actual joints and flexible proxies.
    parts,meta=configs[1]
    cut,proj=raster(parts,1500,1120,cutaway=True)
    frame=Image.new('RGB',(1640,1360),'white');frame.paste(cut,(70,150));d=ImageDraw.Draw(frame)
    text(d,(70,40),'Proposed assembly · shell cutaway',36)
    text(d,(70,95),'The near half of the shell is hidden to expose the load path. Film and elastic lines are study proxies.',22,'#5d7281')
    def project_cut(points):return proj(points)+np.array([70,150])
    line_label(d,project_cut,[0,120,191],'Six mechanically captured joints',(1000,210))
    line_label(d,project_cut,[0,0,0],'Existing chamber / outlet',(90,430))
    line_label(d,project_cut,[0,0,262],'Original manual diaphragm',(1130,1090))
    line_label(d,project_cut,[0,95,61],'Local shell reinforcement',(95,1030))
    line_label(d,project_cut,[0,-95,61],'Printed keyed adapter',(95,1160))
    text(d,(70,1300),'Amber: printed keyed adapter  |  Grey: purchased hardware reference  |  Blue: shell / local reinforcement',22)
    frame.save(HERE/'proposed-cutaway.png')
    # Actual front-top geometry, cropped rather than separately recreated.
    detail,project=raster(parts,1200,1000,cutaway=True,direction=(-1,.25,-.55),crop=([-20,78,40],[20,125,82]))
    f=Image.new('RGB',(1400,1240),'white');f.paste(detail,(100,130));d=ImageDraw.Draw(f)
    text(d,(65,35),'Proposed top-front connection · actual assembly meshes',30)
    text(d,(65,88),'Capture and spacing are modeled; hardware threads are dimensional envelopes.',22,'#5d7281')
    text(d,(65,1160),'The thin source shell is locally thickened; the removable spacer is keyed through the existing slot.',22)
    f.save(HERE/'proposed-joint-detail.png')
    print('Rendered core/proposed comparison, whole cutaway and local joint detail.',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--final-shells',action='store_true');args=a.parse_args()
    make_comparison(args.final_shells)
