# WANMAI static-verification manifest and re-derivation script

Companion material for the manuscript *Is the pathway engine actually wired in? A two-timepoint source-code verification of automatic milestone derivation in a multidisciplinary cleft care information system* (BMC Medical Informatics and Decision Making, in preparation).

The WANMAI source code is proprietary to the hospital project and is **not** included. This package contains only
file names, SHA-256 hashes, sizes, modification times and counts. It contains no source lines, no credentials and no patient data.

## Contents
* `verify_wanmai.py` : scans a WANMAI source tree (`python verify_wanmai.py <root> <out_dir>`; set `PHP` to the PHP 8 CLI path) and re-derives the manuscript's T2 counts: files that reference `Protocol3Service`, `autoDeriveFromSurgeries` and `ClinicalGuidelineEngine`, existence, `php -l` result and `requirePermission` guard of the 13 discipline module files, plus a hash manifest of the inspected files.
* `wanmai_verification.json` : output of that script on the study machine (PHP 8.2.12), including `claims_check`.

## What this does and does not establish
* **Snapshot date:** the manifest was generated on 2026-11-23, after the T2 inspection (2026-10-11). The inspected files are not tracked in the project's git history, so a T2 commit cannot be checked out. Of the inspected files, only one (`tests/registry_gating_test.php`, a new test that references the guideline engine) has a modification time later than 2026-10-11; modification times can be changed and are supporting evidence only.
* **T1 (2026-08-06) is not reproducible:** no snapshot or hash of the T1 state was kept, and the sibling directories `wanmai-v1/` and `wanmai-v3/` used at T1 are no longer on the study machine. T1 results rest on the authors' inspection log.
* **Result of the re-derivation on the 2026-11-23 snapshot:** all six workflow callers named in the manuscript are present; 12 of the 13 module files exist and pass `php -l` with a permission guard (`population_analytics.php` is absent); the engine is referenced only by the adapter and one test file. Two database seed scripts also reference `Protocol3Service` and are not workflow callers.

## Licence and citation
MIT (script). See `CITATION.cff`. DOI is assigned by Zenodo at release.
