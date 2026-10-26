"""Preserve a metadata-only assembly JSON update without rerunning geometry."""
from pathlib import Path
import json,hashlib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    report=json.loads((HERE/'recommended-usage-results.json').read_text())
    current=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
    oldhash=report['input_hashes']['design-b/recommended-assembly.json']
    newhash=sha(ROOT/'design-b/recommended-assembly.json')
    checks=[]
    by={(r['joint'],r['side']):r for r in report['six_site_tools']}
    for j in current['joints']:
        M=np.asarray(j['adapter_local_to_assembly']);p=M[:3,3];n=np.asarray(j['outward_axis'])
        for side,z,axis in [('inside',j['head_inner_face_local_z_mm']-.1,-n),
                            ('outside',j['nut_outer_face_local_z_mm']+.1,n)]:
            r=by[j['id'],side];origin=p+n*z
            checks.append({'joint':j['id'],'side':side,
              'origin_max_change_mm':float(np.max(np.abs(origin-r['tool_origin_mm']))),
              'axis_max_change':float(np.max(np.abs(axis-r['tool_axis'])))})
    geometry={name:sha(ROOT/name)==h for name,h in report['input_hashes'].items()
              if name.endswith('.stl')}
    governing={name:sha(ROOT/name)==h for name,h in report['input_hashes'].items()
               if name!='design-b/recommended-assembly.json' and not name.endswith('.stl')}
    valid=all(geometry.values()) and all(governing.values()) and all(r['origin_max_change_mm']<1e-10 and r['axis_max_change']<1e-10 for r in checks)
    record={'old_assembly_json_sha256':oldhash,'new_assembly_json_sha256':newhash,
      'reason':'Parent owner reported adding gap_basis explanatory text only; no geometry, numeric values or poses changed.',
      'owner_report_not_substituted_for_geometry_check':True,
      'independently_checked_mesh_hashes':geometry,'other_governing_input_hashes':governing,
      'all12_service_pose_comparisons':checks,'semantic_geometry_inputs_match':valid,
      'scope':'Preserves old report hashes. Qualifies metadata-only JSON mismatch for these geometry/service calculations; does not independently re-attest every nongeometric narrative/capacity field.'}
    (HERE/'semantic-rebaseline.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'semantic_geometry_inputs_match':valid,'mesh_count':len(geometry),'poses':len(checks),'json_hash_changed':oldhash!=newhash},indent=2))

if __name__=='__main__':main()
