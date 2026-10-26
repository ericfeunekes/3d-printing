"""Exact polygon intersection of selected centre-plane mesh sections only.

This is not 3-D collision, snap deformation or printed-fit validation.
"""
from pathlib import Path
import sys,json
import numpy as np
from shapely.geometry import Polygon
sys.path.insert(0,str(Path(__file__).resolve().parent))
from recover_core import core
HERE=Path(__file__).resolve().parent
meshes,T,joints=core()
rows=[]
for j in joints:
    inv=np.linalg.inv(j['pin_local_to_assembly'])
    def section_polygon(mesh):
        m=mesh.copy();m.apply_transform(inv)
        section=m.section(plane_normal=[0,1,0],plane_origin=[0,0,0])
        result=Polygon()
        for q in section.discrete:
            p=Polygon(q[:,[0,2]])
            if not p.is_valid:p=p.buffer(0)
            result=result.symmetric_difference(p)
        return result
    pin=section_polygon(meshes[j['pin_object']])
    row={'joint':j['id'],'scope':'pinlocalY0section; undeformed source snap geometry'}
    for name,i in [('shell',j['shell_object']),('rail',j['rail_object'])]:
        intersection=pin.intersection(section_polygon(meshes[i]))
        row[name]={'intersection_area_mm2':intersection.area,
                   'intersection_uv_bounds':list(intersection.bounds) if not intersection.is_empty else None}
    rows.append(row)
(HERE/'source-joint-section-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Saved six source-joint section audit rows; not a 3-D collision proof.')
