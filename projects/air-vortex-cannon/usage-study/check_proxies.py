"""Explicit hand proxies and conditional diaphragm geometry metrics."""
from pathlib import Path
import json,sys,math
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from check_usage import make_fixed,deterministic_points,sampled_clearance

def ellipsoid(center,radii):
    m=trimesh.creation.icosphere(subdivisions=2,radius=1.)
    m.vertices=m.vertices*np.asarray(radii)+np.asarray(center)
    return m

def main():
    structure,_,_=make_fixed()
    grip=ellipsoid([0,-155,110.4],[32.5,45,32.5])
    grip.export(HERE/'grip-hand-proxy.stl')
    checks=[{'proxy':'grip-hand','center_mm':[0,-155,110.4],'radii_mm':[32.5,45,32.5],
             'excluded_intended_contact':'stock-4 lower handle/rail, which the proxy is meant to grasp',
             'checks':sampled_clearance(deterministic_points(grip,700),{k:v for k,v in structure.items() if k!='stock-4'})}]
    film=[]
    R=116.8533;r=20.
    flat=math.pi*(R*R-r*r)
    for s in [0,10,20,30,40,50,60]:
        pz=261.8896408+s
        hand=ellipsoid([0,10,pz+60],[35,37.5,40])
        if s in [0,60]:hand.export(HERE/f'pull-hand-{s}mm-proxy.stl')
        checks.append({'proxy':'pull-hand','stroke_mm':s,'center_mm':[0,10,pz+60],'radii_mm':[35,37.5,40],
          'excluded_intended_contact':'moving central pinch cap/ring being grasped',
          'checks':sampled_clearance(deterministic_points(hand,700),structure)})
        area=math.pi*(R+r)*math.sqrt((R-r)**2+s*s)
        volume=math.pi*s*(R*R+R*r+r*r)/3
        film.append({'assumed_stroke_mm':s,'annular_surface_area_mm2':area,
                     'ratio_to_flat_annulus':area/flat,'extra_annular_slack_area_percent':100*(area/flat-1),
                     'geometric_swept_volume_litres':volume/1e6})
    result={'scope':'Assumed geometric/clearance envelope, not anthropometric or fluid-dynamic validation',
      'hand_limit':'Proxy sizes/poses are chosen examples. No actual user dimensions, finger articulation, grip force or comfort were measured.',
      'hands':checks,'diaphragm_geometry':film,
      'diaphragm_limit':'Area increase is required available slack for this cone envelope, not elastic film strain. Swept volume assumes this geometry and no leakage, and is not actual discharged air, pulse history, formation number or ring-performance evidence.'}
    (HERE/'proxy-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'hand_cases':len(checks),'film_at60mm':film[-1]},indent=2))

if __name__=='__main__':main()
