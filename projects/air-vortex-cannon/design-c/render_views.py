"""Geometry-derived Revision C views; no independent design shapes."""
from pathlib import Path
import sys,importlib.util
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT/'presentation')]
from assembly import load_selected
from scene_data import load_configuration
spec=importlib.util.spec_from_file_location('original_mesh_renderer',ROOT/'presentation/render_views.py')
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
raster,text,line_label=renderer.raster,renderer.text,renderer.line_label

def main():
    out=HERE/'presentation';out.mkdir(exist_ok=True)
    selected,_=load_selected();core,_=load_configuration('core')
    f=Image.new('RGB',(2200,1350),'white');d=ImageDraw.Draw(f)
    text(d,(60,35),'Revision C: repair the lower connections; retain the original grip position',33)
    text(d,(60,90),'Upper rail/pins, bag clamps, elastic arrangement and outlet remain original.',24,'#5d7281')
    for i,(parts,title) in enumerate([(core,'ORIGINAL'),(selected,'SELECTED CANDIDATE')]):
        im,_=raster(parts,1020,970,direction=(-1,.04,-1.1))
        f.paste(im,(45+i*1090,205));text(d,(65+i*1090,155),title,28)
    text(d,(60,1210),'Three lower pins are replaced with conforming keyed adapters and captured metal shoulder fasteners.',24)
    text(d,(60,1255),'Local reinforcement is fused into the shell copies; existing shell slots are preserved.',24)
    text(d,(60,1300),'Conditional prototype: physical print strength, locking, comfort and vortex performance remain untested.',21,'#725335')
    f.save(out/'core-vs-selected.png')

    cut,proj=raster(selected,1450,1090,cutaway=True,direction=(-1,.25,-1.2))
    f=Image.new('RGB',(1620,1370),'white');f.paste(cut,(80,160));d=ImageDraw.Draw(f)
    text(d,(55,35),'Revision C cutaway: what changes and what stays',34)
    text(d,(55,92),'Near shell half hidden. Film and elastic lines are assumed study proxies.',23,'#5d7281')
    def pp(points):return proj(points)+np.array([80,160])
    line_label(d,pp,[0,118,192],'Original upper rail and pins',(930,210))
    line_label(d,pp,[0,-110,144],'Three revised lower joints',(900,1120))
    line_label(d,pp,[0,-155,110.4],'Original grip position retained',(85,1185))
    line_label(d,pp,[0,0,262],'Original bag clamps',(1155,910))
    text(d,(55,1305),'Orange: conforming printed adapters | Grey: metal references | Blue: shell and integrated reinforcement',21)
    f.save(out/'selected-cutaway.png')

    f=Image.new('RGB',(2000,1200),'white');d=ImageDraw.Draw(f)
    text(d,(50,30),'Lower handle connection: original versus Revision C',35)
    text(d,(50,90),'Actual meshes, same joint and camera; the shell is partly hidden.',23,'#5d7281')
    for i,(parts,title) in enumerate([(core,'ORIGINAL: printed split pin'),(selected,'C: curved load-spreading contact + metal capture')]):
        im,_=raster(parts,920,780,cutaway=True,direction=(-1,-.25,-.55),crop=([-20,-118,40],[20,-78,82]))
        f.paste(im,(40+990*i,190));text(d,(55+990*i,145),title,25)
    text(d,(55,1000),'C adds material around the existing lower slot. The curved adapter follows the reinforced cone.',23)
    text(d,(55,1045),'The outer metal washer retains the original handle seat; no extra exterior printed pad or new groove.',23)
    text(d,(55,1110),'Curved contacts are intended to spread normal load; shell reinforcement addresses slot-edge bearing.',22)
    text(d,(55,1155),'Contact fit and strength still need physical testing. No glue or tightening-friction credit.',21,'#725335')
    f.save(out/'lower-joint-comparison.png')
    print('Wrote three C actual-mesh views.')

if __name__=='__main__':main()
