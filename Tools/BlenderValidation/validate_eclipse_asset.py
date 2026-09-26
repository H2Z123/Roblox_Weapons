"""ECLIPSE asset validator — command-line entry point (runs inside Blender).

    blender -b <file.blend> --python Tools/BlenderValidation/validate_eclipse_asset.py -- \
        --profile viewmodel --collection ECLIPSE1_VM --out Reports/validation/<name>

Options (after the standalone ``--``):
    --profile {source,viewmodel,worldmodel}   thresholds set (default: source)
    --stage {source,export}                   export escalates some WARN to FAIL
    --collection NAME                         validate this collection (recursive)
    --objects A,B,C                           or an explicit object list
    --check NAME[,NAME]                       category or alias (validate_uv, validate_normals, ...)
    --rules ID[,ID]                           explicit rule ids (GEO001,SHD002,...)
    --config PATH                             JSON merged over config/eclipse_default.json
    --texture-resolution N                    resolution used for texel density / padding
    --analyze-textures                        read texture pixels (slower)
    --out DIR                                 write validation_report.json/.md there
    --list-rules                              print the rule catalogue and exit

Exit code: 0 = no FAIL/ERROR, 1 = at least one FAIL or ERROR, 2 = crash.
The validator never modifies the .blend file.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def parse(argv):
    p = argparse.ArgumentParser(prog="validate_eclipse_asset")
    p.add_argument("--profile", default="source")
    p.add_argument("--stage", default="source", choices=["source", "export"])
    p.add_argument("--collection")
    p.add_argument("--objects")
    p.add_argument("--check")
    p.add_argument("--rules")
    p.add_argument("--config")
    p.add_argument("--texture-resolution", type=int)
    p.add_argument("--analyze-textures", action="store_true")
    p.add_argument("--out")
    p.add_argument("--list-rules", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    if argv is None:
        if "--" in sys.argv:
            argv = sys.argv[sys.argv.index("--") + 1:]
        elif "bpy" in sys.modules and sys.argv and "blender" in os.path.basename(sys.argv[0]).lower():
            argv = []  # launched as `blender ... --python this.py` without our own arguments
        else:
            argv = sys.argv[1:]
    args = parse(argv)
    import eclipse_validator as ev
    from eclipse_validator import core

    if args.list_rules:
        ev.load_rules()
        for rid, spec in sorted(core.registry().items()):
            print(f"{rid:8s} {spec.category:22s} {spec.title}  -> {spec.doc}")
        return 0
    rep = ev.run(profile=args.profile, stage=args.stage, collection=args.collection,
                 objects=args.objects.split(",") if args.objects else None,
                 out_dir=args.out, config_path=args.config,
                 checks=args.check.split(",") if args.check else None,
                 rules=args.rules.split(",") if args.rules else None,
                 analyze_textures=args.analyze_textures, texture_resolution=args.texture_resolution)
    s = rep["summary"]
    print(f"[ECLIPSE] overall={s['overall']} counts={s['counts']}")
    for r in rep["results"]:
        if r["status"] in ("FAIL", "WARN", "ERROR"):
            objs = ", ".join(r["objects"][:6])
            print(f"  {r['status']:5s} {r['rule_id']:8s} {r['title']}" + (f"  [{objs}]" if objs else ""))
    if rep.get("written"):
        print(f"[ECLIPSE] report: {rep['written']['markdown']}")
    return 1 if s["counts"].get("FAIL", 0) or s["counts"].get("ERROR", 0) else 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # pragma: no cover - surfaced to the caller
        import traceback
        traceback.print_exc()
        print(f"[ECLIPSE] validator crashed: {exc}")
        code = 2
    # In background mode Blender ignores the script's return value; force it.
    if "--" in sys.argv or os.environ.get("ECLIPSE_VALIDATOR_EXIT"):
        sys.exit(code)
