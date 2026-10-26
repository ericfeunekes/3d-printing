"""Package unchanged selected C meshes; export editable Bambu projects, never print.

Python 3.12 with the project's trimesh/numpy dependencies. Bambu Studio 2.8.2.61.
No printer connection, upload, purchase, or machine configuration is performed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import numpy as np
import trimesh

RELEASE = "v02.08.02.61"
SOURCE = "https://makerworld.com/en/models/442826-air-vortex-cannon#profileId-348811"
LICENSE = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
NAMES = {1:"Sight pin",2:"Sight",3:"Upper rail",4:"Original handle",
         5:"Membrane centre cap",9:"Elastic carabiner",10:"Rear diaphragm clamp",
         11:"Upper pin 1",12:"Upper pin 2",13:"Upper pin 3",17:"Membrane centre ring"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve_profiles(root):
    files = {}
    for f in root.rglob("*.json"):
        p = json.loads(f.read_text())
        if "name" in p:
            files[p["name"]] = p
    def resolve(name, chain=()):
        assert name not in chain, (name, chain)
        p = files[name]
        out = resolve(p["inherits"], (*chain, name)) if p.get("inherits") else {}
        for inc in p.get("include", []):
            out.update(resolve(inc, (*chain, name)))
        out.update({k:v for k,v in p.items() if k not in ("inherits", "include")})
        return out
    machine = resolve("Bambu Lab X2D 0.4 nozzle")
    # Explicit nozzle state, as required by the CLI for this dual-hotend profile.
    machine["extruder_nozzle_stats"] = ["Standard#1", "Standard#1"]
    process = resolve("0.16mm Standard @BBL X2D")
    overrides = dict(name="Air vortex C - draft PLA 0.16", print_settings_id="Air vortex C - draft PLA 0.16",
                     wall_loops="4", top_shell_layers="5", bottom_shell_layers="5",
                     sparse_infill_density="25%", sparse_infill_pattern="gyroid",
                     enable_support="1", support_type="normal(auto)",
                     support_on_build_plate_only="1", bridge_no_support="1",
                     support_top_z_distance="0.16", support_bottom_z_distance="0.16",
                     brim_type="outer_only", brim_width="2", brim_object_gap="0.1",
                     enable_prime_tower="0", curr_bed_type="Textured PEI Plate")
    process.update(overrides)
    filament = resolve("Generic PLA @BBL X2D 0.4 nozzle")
    return {"machine":machine, "process":process, "filament":filament}, overrides

def inventories(root):
    full = []
    for n, label in NAMES.items():
        full.append((f"original-{n:02d}-{label}", next((root/"source/egordv").glob(f"obj_{n}_*.stl"))))
    for n in (6,8,7):
        full.append((f"C-reinforced-shell-{n}", root/f"design-c/joints/print/lower-only-shell-{n}.stl"))
    for site in ("front","middle","rear"):
        full.append((f"C-{site}-curved-adapter",root/f"design-c/joints/print/bottom-{site}-conforming-keyed-adapter.stl"))
    fit = [("C-shell-fit-coupon",root/"design-c/joints/fit-coupon/c-conical-collar-shell-coupon-print.stl"),
           ("Original-receiver-fit-coupon",root/"design-c/joints/fit-coupon/original-handle-receiver-coupon-print.stl"),
           full[-3]]
    return full, fit

def prepare(root, out, profiles):
    out.mkdir(parents=True,exist_ok=True)
    (out/"settings").mkdir(exist_ok=True)
    configs, overrides = resolve_profiles(profiles)
    for name, value in configs.items():
        (out/"settings"/f"{name}.json").write_text(json.dumps(value,indent=2)+"\n")
    full,fit = inventories(root)
    # Each tuple is (plate number, minimum X, minimum Y), in mm in plate coordinates.
    # Preserve all source rotations; only XYZ translations are applied.
    layout = {
        1:(5,226,180), 2:(5,145,175), 3:(5,20,119), 4:(5,20,15),
        5:(5,20,203), 9:(5,226,205), 10:(4,None,None),
        11:(5,120,215),12:(5,153,215),13:(5,186,215),17:(5,70,205),
        6:(1,None,None),8:(2,None,None),7:(3,None,None),
        "front":(5,20,175),"middle":(5,60,175),"rear":(5,100,175),
    }
    report={"units":"millimeter","source_license":LICENSE,"source_url":SOURCE,
            "bambu_release":RELEASE,"provisional_process_overrides":overrides,
            "status":"Editable unsliced project; proposed settings, not physical qualification",
            "profile_note":"Official X2D profile height261mm; prior manufacturer bare envelope260mm. All parts below91mm.",
            "packages":{}}
    for package, items in (("air-vortex-cannon-revision-c",full),("revision-c-fit-coupon",fit)):
        records=[]
        fit_mode = package=="revision-c-fit-coupon"
        fit_xy=[(40,80),(100,80),(170,80)]
        for idx,(label,path) in enumerate(items):
            mesh=trimesh.load_mesh(path)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0, path
            if fit_mode:
                plate=1; x,y=fit_xy[idx]; origin=np.zeros(3)
            else:
                key = int(label.split("-")[1]) if label.startswith("original-") else \
                      int(label.rsplit("-",1)[1]) if "reinforced-shell" in label else label.split("-")[1]
                plate,x,y=layout[key]
                origin=np.array([((plate-1)%3)*307.2,-((plate-1)//3)*307.2,0.0])
                if x is None:
                    x,y=(256-mesh.extents[:2])/2
            offset=np.array([x,y,0.0])-mesh.bounds[0]
            local=mesh.bounds+offset
            assert np.all(local[0]>=-1e-6) and np.all(local[1]<=[256,256,260]), (label,local)
            tf=np.eye(4);tf[:3,3]=offset+origin
            records.append(dict(name=label,source=str(path.relative_to(root)),source_sha256=sha(path),
                                plate=plate,plate_origin_mm=origin.tolist(),translation_mm=tf[:3,3].tolist(),
                                plate_bounds_mm=local.tolist(),source_extents_mm=mesh.extents.tolist(),
                                source_volume_mm3=float(mesh.volume),source_triangle_count=len(mesh.faces)))
        # Separate objects, no merging, supports or hardware inserted into geometry.
        report["packages"][package]={"object_count":len(items),"plate_count":1 if fit_mode else 5,"objects":records}
    (out/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

def export_projects(binary,out,scratch,root):
    scratch.mkdir(parents=True,exist_ok=True)
    common=[str(binary),"--datadir",str(scratch/"bambu-data"),"--debug","2","--orient","0","--arrange","0"]
    settings=["--load-settings",str(out/"settings/machine.json")+";"+str(out/"settings/process.json"),
              "--load-filaments",str(out/"settings/filament.json")]
    report=json.loads((out/"preparation.json").read_text())
    names=["Front reinforced shell", "Middle reinforced shell", "Rear reinforced shell", "Rear diaphragm clamp", "Handle rails adapters and small parts"]
    for name in ("air-vortex-cannon-revision-c","revision-c-fit-coupon"):
        info=report["packages"][name]
        plates=[dict(plate_name=("C actual-interface fit coupon" if info["plate_count"]==1 else names[i]),need_arrange=False,objects=[]) for i in range(info["plate_count"])]
        for obj in info["objects"]:
            offset=np.array(obj["translation_mm"])-np.array(obj["plate_origin_mm"])
            plates[obj["plate"]-1]["objects"].append(dict(path=str(root/obj["source"]),count=1,filaments=[1],pos_x=[float(offset[0])],pos_y=[float(offset[1])],pos_z=[float(offset[2])]))
        plate_list=scratch/f"{name}-plates.json"
        plate_list.write_text(json.dumps(dict(plates=plates),indent=2)+"\n")
        meta=["--metadata-name","Designer;LicenseTerms;Description",
              "--metadata-value","egordv - Revision C prepared for Eric Feunekes with Codex;Creative Commons Attribution-NonCommercial-ShareAlike 4.0 " + LICENSE + ";Unprinted conditional prototype - " + SOURCE]
        cmd=common+settings+meta+["--load-assemble-list",str(plate_list),"--export-3mf",str(out/f"{name}.3mf")]
        with (scratch/f"{name}-export.log").open("w") as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        print(name,"export exit",result.returncode,flush=True)
        if result.returncode:raise RuntimeError(f"Export failed; see {scratch}")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root",type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument("--output",type=Path,default=Path(__file__).resolve().parent)
    p.add_argument("--profiles",type=Path,required=True,help="Official Bambu Resources/profiles/BBL directory")
    p.add_argument("--binary",type=Path)
    p.add_argument("--scratch",type=Path,default=Path("/tmp/vortex-c-3mf"))
    a=p.parse_args()
    prepare(a.project_root.resolve(),a.output.resolve(),a.profiles.resolve())
    if a.binary:export_projects(a.binary.resolve(),a.output.resolve(),a.scratch.resolve(),a.project_root.resolve())
