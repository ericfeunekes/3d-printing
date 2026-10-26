from pathlib import Path
import sys,json,gc,argparse
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scene_data import export_glb
def main(final_shells=False):
    records=[]
    for configuration in ['core','recommended']:
        for travel in [0,60]:
            name=f'{configuration}-{"rest" if travel==0 else "pull-60mm-study"}.glb'
            path=HERE/name
            metadata=export_glb(path,configuration,travel,final_shells)
            records.append({'path':name,'configuration':configuration,'assumed_pull_mm':travel,
                'rigid_parts':metadata['rigid_part_count'],'status':metadata['geometry_status'],
                'glb_units':'m','native_units':'mm'})
            print(name,path.stat().st_size,flush=True);gc.collect()
    (HERE/'exports.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final-shells',action='store_true');args=p.parse_args();main(args.final_shells)
