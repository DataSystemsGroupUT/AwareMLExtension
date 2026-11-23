param([string]$Python = ".\.venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path -LiteralPath $Python)) { throw "Python interpreter not found. Pass -Python with your PyCharm interpreter path." }
& $Python .\APPLY_AWAREML_MORTEN_V8.py --check
if ($LASTEXITCODE -ne 0) { throw "Upgrade preflight failed; no files were applied." }
& $Python .\APPLY_AWAREML_MORTEN_V8.py
if ($LASTEXITCODE -ne 0) { throw "Upgrade failed." }
& $Python -m pytest tests/test_morten_review_v8.py -q
if ($LASTEXITCODE -ne 0) { throw "Verification failed. Review the output before collecting participants." }
& $Python scripts/verify_morten_review_v8.py
if ($LASTEXITCODE -ne 0) { throw "Design integrity validation failed." }
