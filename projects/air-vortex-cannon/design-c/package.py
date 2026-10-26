"""Package the C handoff and its relative-path source/helper dependencies.

No old B viewer, binaries, caches or rejected numerical diagnostics included.
"""
from pathlib import Path
import hashlib,json,zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    paths={ROOT/'REVISION-C-START.md'}
    excluded={'handoff-manifest.json','package-manifest.json','usage-results-axis-ray-diagnostic.json',
        'input-lower-assembly-axis-ray-diagnostic.json','optional-handle-print.stl','inspect_handle.py','inspect_source_slots.py'}
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded and p.suffix!='.zip':paths.add(p)
    preserved=json.loads((HERE/'preserved-source-hashes.json').read_text())
    for rel,h in preserved['source_files'].items():
        p=ROOT/rel;assert sha(p)==h,rel;paths.add(p)
    paths.add(ROOT/'source/egordv/mesh-inventory.json')
    for rel,h in preserved['reviewed_B_files'].items():
        p=ROOT/rel
        if p.exists():assert sha(p)==h,rel
        if rel.startswith(('assembly-study/','ancillary-study/')):
            assert p.exists(),rel;paths.add(p)
    helpers=['presentation/scene_data.py','presentation/render_views.py','joint-study/build_options.py',
        'design-b/fuse_shells.py','design-b/recommended-assembly.json',
        'usage-study/check_usage.py','usage-study/check_recommended.py',
        'usage-study/certify_envelopes.py','usage-study/refine_service_certificate.py']
    paths.update(ROOT/p for p in helpers)
    for p in (ROOT/'load-study').iterdir():
        if p.is_file() and p.suffix in {'.py','.json','.md','.png'}:paths.add(p)
    # Include the usage's own immutable evidence manifest without confusing it
    # with this archive-wide manifest.
    paths.add(HERE/'usage/handoff-manifest.json')
    files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    record={'entrypoint':'REVISION-C-START.md','status':'Conditional CAD prototype; original grip selected',
        'units':'CAD/STL/JSON mm; GLB m','file_count':len(files),'files':files,
        'selected_print_set':'design-c/joints/print/README.md',
        'not_bundled':'Rejected optional handle print alias, rejected pure-X numeric diagnostics, old HTML viewer, runtime binaries and caches',
        'physical_proof':'Not established'}
    manifest=HERE/'package-manifest.json';manifest.write_text(json.dumps(record,indent=2)+'\n')
    out=ROOT/'air-vortex-cannon-revision-c.zip'
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel in files:z.write(ROOT/rel,'air-vortex-cannon-revision-c/'+rel)
        z.write(manifest,'air-vortex-cannon-revision-c/design-c/package-manifest.json')
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for rel,h in files.items():assert hashlib.sha256(z.read('air-vortex-cannon-revision-c/'+rel)).hexdigest()==h,rel
    print(json.dumps({'files':len(files),'archive_bytes':out.stat().st_size,'archive_sha256':sha(out)}))

if __name__=='__main__':main()
