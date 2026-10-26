"""Local unit-load FE screen of an outer steel washer bridging the rail slot.

Gmsh quadratic tetrahedra, CalculiX linear elasticity. This models prescribed
support strips and nut-face loading, not real nonlinear contact or washer yield.
No manufacturer strength is assumed. Outputs are demands per normal newton.
"""
from pathlib import Path
import json,math,subprocess,re
import numpy as np
from scipy.optimize import linear_sum_assignment

HERE=Path(__file__).resolve().parent
BASE=HERE/'washer-fea'
BASE.mkdir(exist_ok=True)
GMSH='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh'
CCX='/Applications/FreeCAD.app/Contents/Resources/bin/ccx'
E=200000.;NU=.3;SPAN=8.;LOAD_R=3.5

def parse_mesh(path):
    lines=path.read_text().splitlines();a=lines.index('$Nodes');n=int(lines[a+1])
    nodes={int(s[0]):np.array(list(map(float,s[1:4]))) for s in (line.split() for line in lines[a+2:a+2+n])}
    a=lines.index('$Elements');n=int(lines[a+1]);tets=[];tris=[]
    target_edges=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
    for line in lines[a+2:a+2+n]:
        vals=list(map(int,line.split()));typ=vals[1];tags=vals[2];ids=vals[3+tags:]
        if typ==11:
            verts=ids[:4]
            xyz=np.array([nodes[i] for i in verts])
            if np.linalg.det((xyz[1:]-xyz[0]).T)<0:
                verts[1],verts[2]=verts[2],verts[1];xyz=np.array([nodes[i] for i in verts])
            mids=ids[4:]
            targets=np.array([(xyz[i]+xyz[j])/2 for i,j in target_edges])
            coords=np.array([nodes[i] for i in mids])
            rr,cc=linear_sum_assignment(np.linalg.norm(targets[:,None,:]-coords[None,:,:],axis=2))
            ordered=[None]*6
            for r,c in zip(rr,cc):ordered[r]=mids[c]
            tets.append(verts+ordered)
        elif typ==9:tris.append(ids)
    assert tets and tris
    return nodes,tets,tris

def make_input(folder,od,di,thickness,h):
    geo=f'''SetFactory("OpenCASCADE");
Cylinder(1)={{0,0,0,0,0,{thickness},{od/2}}};
Cylinder(2)={{0,0,-.1,0,0,{thickness+.2},{di/2}}};
BooleanDifference{{Volume{{1}};Delete;}}{{Volume{{2}};Delete;}}
Mesh.MeshSizeMin={h};Mesh.MeshSizeMax={h};
Mesh.ElementOrder=2;Mesh.SecondOrderLinear=0;
Mesh.MshFileVersion=2.2;Mesh.Binary=0;
'''
    reusable_mesh=(folder/'washer.geo').exists() and (folder/'washer.geo').read_text()==geo and (folder/'washer.msh').exists()
    (folder/'washer.geo').write_text(geo)
    if not reusable_mesh:
        mesher=subprocess.run([GMSH,'washer.geo','-3','-format','msh2','-o','washer.msh','-v','2'],cwd=folder,text=True,capture_output=True,timeout=60)
        (folder/'gmsh.log').write_text(mesher.stdout+mesher.stderr)
        assert mesher.returncode==0,(mesher.returncode,mesher.stderr)
    nodes,tets,tris=parse_mesh(folder/'washer.msh')
    support=[i for i,p in nodes.items() if abs(p[2])<1e-6 and abs(p[0])>=SPAN/2-1e-6]
    assert support
    p1=max(support,key=lambda i:nodes[i][0]);p2=min(support,key=lambda i:nodes[i][0])
    # Selected quadratic top triangles approximate the nut's circular bearing
    # patch; total force is normalized exactly to1N for every mesh.
    top=[]
    for ids in tris:
        xyz=np.array([nodes[i] for i in ids])
        if np.max(np.abs(xyz[:,2]-thickness))<1e-6 and np.linalg.norm(xyz[:3,:2].mean(axis=0))<=LOAD_R:
            area=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2
            top.append((ids,area))
    area=sum(a for _,a in top);assert area>0
    nodal={}
    # Consistent constant-pressure forces on a quadratic triangular face:
    # corner integrals0, each of its three midside integrals A/3.
    for ids,a in top:
        for i in ids[3:6]:nodal[i]=nodal.get(i,0)-a/(3*area)
    assert abs(sum(nodal.values())+1)<1e-9
    lines=['*HEADING','Outer washer unit-load screen; N-mm-MPa','*NODE']
    lines += [f'{i},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}' for i,p in nodes.items()]
    lines+=['*ELEMENT,TYPE=C3D10,ELSET=ALL']
    lines += [f'{i},'+','.join(map(str,e)) for i,e in enumerate(tets,1)]
    lines+=['*NSET,NSET=ALLN']
    allids=list(nodes)
    lines += [','.join(map(str,allids[i:i+16])) for i in range(0,len(allids),16)]
    lines+=['*NSET,NSET=SUP']
    lines += [','.join(map(str,support[i:i+16])) for i in range(0,len(support),16)]
    lines += ['*MATERIAL,NAME=STEEL_ASSUMED','*ELASTIC',f'{E},{NU}',
              '*SOLID SECTION,ELSET=ALL,MATERIAL=STEEL_ASSUMED','*BOUNDARY','SUP,3,3',f'{p1},1,2',f'{p2},2,2',
              '*STEP','*STATIC','*CLOAD']
    lines += [f'{i},3,{f:.12g}' for i,f in nodal.items()]
    lines += ['*NODE PRINT,NSET=ALLN','U','*NODE PRINT,NSET=SUP','RF','*EL PRINT,ELSET=ALL','S','*END STEP']
    (folder/'washer.inp').write_text('\n'.join(lines)+'\n')
    return nodes,tets,{'nodes':len(nodes),'quadratic_tets':len(tets),'support_nodes':len(support),
                       'top_loaded_triangles':len(top),'approximated_load_area_mm2':area,
                       'analytic_target_area_mm2':math.pi*(LOAD_R**2-(di/2)**2),
                       'total_applied_Fz_N':sum(nodal.values())}

def read_results(folder,nodes,tets):
    lines=(folder/'washer.dat').read_text().splitlines();mode=None;displacements=[];stress=[];reaction=[]
    for line in lines:
        s=line.strip().lower()
        if s.startswith('displacements'):mode='u';continue
        if s.startswith('forces'):mode='rf';continue
        if s.startswith('stresses'):mode='s';continue
        vals=line.split()
        try:
            if mode=='u' and len(vals)==4:
                displacements.append((int(vals[0]),*map(float,vals[1:])))
            elif mode=='rf' and len(vals)==4:
                reaction.append((int(vals[0]),*map(float,vals[1:])))
            elif mode=='s' and len(vals)==8:
                stress.append((int(vals[0]),int(vals[1]),*map(float,vals[2:])))
        except ValueError:pass
    assert displacements and stress and reaction
    # C3D10's4 integrationpoints in tetrahedron barycentric coordinates.
    aa=.5854101966249685;bb=.1381966011250105
    bary=np.array([[aa,bb,bb,bb],[bb,aa,bb,bb],[bb,bb,aa,bb],[bb,bb,bb,aa]])
    edge=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
    vm=[];bulk=[]
    for eid,ip,sxx,syy,szz,sxy,sxz,syz in stress:
        value=math.sqrt(.5*((sxx-syy)**2+(syy-szz)**2+(szz-sxx)**2)+3*(sxy*sxy+sxz*sxz+syz*syz))
        ll=bary[ip-1];shape=np.r_[ll*(2*ll-1),[4*ll[i]*ll[j] for i,j in edge]]
        point=shape @ np.array([nodes[i] for i in tets[eid-1]])
        vm.append(value)
        # Isolate bulk behaviour from ideal sharp support/load boundaries.
        if abs(abs(point[0])-SPAN/2)>.30 and abs(np.linalg.norm(point[:2])-LOAD_R)>.30:
            bulk.append(value)
    rz=sum(row[3] for row in reaction)
    assert abs(rz-1)<1e-4,rz
    disp=np.array([row[1:] for row in displacements])
    return {'max_displacement_mm_per_N':float(np.linalg.norm(disp,axis=1).max()),
            'most_negative_Uz_mm_per_N':float(disp[:,2].min()),
            'max_integration_point_von_mises_MPa_per_N':float(max(vm)),
            'bulk_region_max_von_mises_MPa_per_N':float(max(bulk)),
            'bulk_region_p95_von_mises_MPa_per_N':float(np.percentile(bulk,95)),
            'support_reaction_Fz_N':float(rz),
            'bulk_exclusion':'Within0.30mm of |X|=4mm support edges or R=3.5mm pressure boundary excluded; full maximum also reported'}

cases=[('nominal_t1p6',12.,4.3,1.6,[.65,.45]),
       ('worst_tolerance_t1p3',11.3,4.48,1.3,[.60,.40]),
       ('thin_comparison_t1',12.,4.3,1.,[.45])]
allresults=[]
for name,od,di,t,hs in cases:
    for h in hs:
        folder=BASE/f'{name}_h{h:g}';folder.mkdir(exist_ok=True)
        nodes,tets,mesh=make_input(folder,od,di,t,h)
        # Always solve the newly written input. A parseable pre-existing .dat
        # is not evidence it belongs to today's mesh/material/BC settings.
        for extension in ['.dat','.frd','.sta','.cvg']:
            stale=folder/('washer'+extension)
            if stale.exists():stale.unlink()
        solve=subprocess.run([CCX,'washer'],cwd=folder,text=True,capture_output=True,timeout=60)
        (folder/'ccx.log').write_text(solve.stdout+solve.stderr)
        if solve.returncode!=0 or not (folder/'washer.dat').exists():
            raise RuntimeError(f'CalculiX failed {folder}: {solve.stdout[-3000:]} {solve.stderr[-1000:]}')
        result=read_results(folder,nodes,tets)
        row={'case':name,'OD_mm':od,'ID_mm':di,'thickness_mm':t,'target_element_size_mm':h,'mesh':mesh,**result}
        allresults.append(row)
        print(json.dumps(row),flush=True)
        (HERE/'washer-fea-results.json').write_text(json.dumps({'status':'In progress','cases':allresults},indent=2)+'\n')
out={'status':'LOCAL CONDITIONAL LINEAR-ELASTIC FE SCREEN — not a washer load rating',
     'solvers':'Gmsh4.15.0 + CalculiX2.23; quadratic C3D10 tetrahedra',
     'assumed_material':{'E_MPa':E,'poisson':NU,'yield_strength':'Not assumed or verified'},
     'assumed_boundary_conditions':{'rail_gap_mm':SPAN,'support':'Uz=0 only at bottom-face nodes with |X|>=4mm; minimal X/Y rigid-body constraints',
                                    'load':'Total1N downward on quadratic top-surface triangles approximating annulus ID/2<R<3.5mm, normalized by actual selected area'},
     'hardware_source':'https://www.accu.co.uk/metric-flat-washers/63172-HDTW-M4-A2',
     'limits':['Rail and nut are modeled as prescribed rigid bearing patches, not nonlinear compliant contact',
               'Sharp support/load boundary peaks may be mesh-sensitive; bulk and full maxima reported separately',
               'No washer yield, fatigue, corrosion, manufacturing residual stress or nut seating validation',
               'Linear results scale with force only while assumptions remain elastic/small-displacement'],
     'cases':allresults}
(HERE/'washer-fea-results.json').write_text(json.dumps(out,indent=2)+'\n')
