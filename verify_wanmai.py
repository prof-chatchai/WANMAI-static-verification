"""Re-derive the T2 counts of the BMC MIDM manuscript from a WANMAI source tree and write a hash manifest.
Outputs file names, SHA-256 hashes, modification times and counts ONLY (no source lines, no secrets).
Usage: python verify_wanmai.py <wanmai_root> <out_dir>"""
import os, re, sys, json, hashlib, subprocess, datetime

root = os.path.abspath(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
EXCL = {"node_modules", ".git", "vendor", "v1", "v2", "v3", "wanmai-v1", "wanmai-v2", "wanmai-v3", "archive", "archives", "backup", "backups", "wanmai"}

def php_files():
    for d, dn, fn in os.walk(root):
        dn[:] = [x for x in dn if x not in EXCL]
        for f in fn:
            if f.endswith(".php"):
                yield os.path.join(d, f)

def rel(p): return os.path.relpath(p, root).replace("\\", "/")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def src(p): return open(p, encoding="utf8", errors="ignore").read()

files = list(php_files())
SYMS = {"Protocol3Service": r"\bProtocol3Service\b", "autoDeriveFromSurgeries": r"\bautoDeriveFromSurgeries\b",
        "ClinicalGuidelineEngine": r"\bClinicalGuidelineEngine\b"}
DEFINERS = {"Protocol3Service": "includes/Protocol3Service.php", "autoDeriveFromSurgeries": "includes/Protocol3Service.php",
            "ClinicalGuidelineEngine": "includes/ClinicalGuidelineEngine.php"}
matches = {k: sorted(rel(p) for p in files if re.search(v, src(p))) for k, v in SYMS.items()}
callers_p3 = sorted(set(matches["Protocol3Service"]) - {DEFINERS["Protocol3Service"]})
callers_engine = sorted(set(matches["ClinicalGuidelineEngine"]) - {DEFINERS["ClinicalGuidelineEngine"]})

# discipline links -> unique module files
mdt = os.path.join(root, "multidisciplinary_team.php")
links = sorted(set(re.findall(r"""['"]([A-Za-z0-9_\-/]+\.php)['"]""", src(mdt)))) if os.path.exists(mdt) else []
EXPECTED = ["surgery_dashboard", "patient_registration", "child_development_dashboard", "ent_dashboard", "patient_view",
            "orthodontic_dashboard", "nam_treatment_dashboard", "psychiatry_dashboard", "treatment_tracking",
            "speech_therapy_dashboard", "patient_management", "population_analytics", "appointment_scheduling"]
mods = {}
for m in EXPECTED:
    p = os.path.join(root, m + ".php")
    if not os.path.exists(p): mods[m] = {"exists": False}; continue
    lint = subprocess.run([os.environ.get("PHP", "php"), "-l", p], capture_output=True, text=True)
    s = src(p)
    mods[m] = {"exists": True, "php_l_ok": lint.returncode == 0, "requirePermission": "requirePermission" in s,
               "sha256": sha(p), "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")}

manifest = {}
inspected = set(callers_p3) | set(callers_engine) | set(DEFINERS.values()) | {"multidisciplinary_team.php", "includes/protocol3_data.php",
             "config/permissions.php", "includes/navbar.php", "includes/patient_helpers.php", "database/protocol3_schema.sql"} | {m + ".php" for m in EXPECTED}
for r in sorted(inspected):
    p = os.path.join(root, r)
    if os.path.exists(p):
        manifest[r] = {"sha256": sha(p), "bytes": os.path.getsize(p),
                       "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")}
    else:
        manifest[r] = {"missing": True}
WORKFLOW = {"api/surgery_import_csv.php","includes/surgery_post_handler.php","kpi_patient_checklist.php","protocol3_matrix.php","protocol3_patient_progress.php","protocol3_cohort_dashboard.php"}
claims = {"paper_workflow_callers_expected": sorted(WORKFLOW), "workflow_callers_found": sorted(set(callers_p3) & WORKFLOW),
          "all_six_found": WORKFLOW <= set(callers_p3), "other_P3_referrers": sorted(set(callers_p3) - WORKFLOW),
          "engine_referrers_outside_definition": callers_engine, "modules_expected_existing": 12}
res = {"claims_check": claims, "generated": datetime.datetime.now().isoformat(timespec="seconds"), "root_name": os.path.basename(root),
       "php_files_scanned": len(files), "symbol_matches": matches, "callers_Protocol3Service": callers_p3,
       "n_callers_Protocol3Service": len(callers_p3), "callers_ClinicalGuidelineEngine_outside_definition": callers_engine,
       "modules": mods, "modules_existing": sum(1 for v in mods.values() if v["exists"]), "modules_total": len(EXPECTED),
       "modules_data_integrity": {k: v for k, v in mods.items() if v["exists"] and not (v["php_l_ok"] and v["requirePermission"])}.keys().__len__(),
       "manifest": manifest}
json.dump(res, open(os.path.join(out, "wanmai_verification.json"), "w"), indent=1)
print("scanned", len(files), "| callers P3:", len(callers_p3), callers_p3, "| engine callers:", callers_engine,
      "| modules:", res["modules_existing"], "/", len(EXPECTED), "| bad modules:", res["modules_data_integrity"])
late = [r for r, v in manifest.items() if not v.get("missing") and v["mtime"] > "2026-10-11T23:59:59"]
print("files modified after T2 (2026-10-11):", late)
