from fastapi import APIRouter
from datetime import datetime
from pathlib import Path
from app.core.config import CS_ROOT, METADATA_PATH

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic liveness check — confirms the API is running."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
def detailed_health_check():
    """
    Deep check — validates critical dependencies:
    - Metadata CSV exists and is readable
    - Case study root directory exists
    - Reports file + folder counts per industry
    """
    issues = []

    # Check metadata CSV
    csv_ok = METADATA_PATH.exists() and METADATA_PATH.is_file()
    if not csv_ok:
        issues.append(f"Metadata CSV not found at: {METADATA_PATH}")

    # Check cs-files root directory
    cs_root_ok = CS_ROOT.exists() and CS_ROOT.is_dir()
    if not cs_root_ok:
        issues.append(f"Case study root not found at: {CS_ROOT}")

    # Count industries (subdirectories) and files
    industry_count = 0
    file_count = 0
    industry_breakdown = {}

    if cs_root_ok:
        for industry_dir in CS_ROOT.iterdir():
            if industry_dir.is_dir():
                files = [
                    f for f in industry_dir.iterdir()
                    if f.suffix.lower() in {".pdf", ".docx", ".pptx"}
                ]
                industry_breakdown[industry_dir.name] = len(files)
                file_count += len(files)
                industry_count += 1

    # Row count from CSV
    csv_row_count = 0
    if csv_ok:
        try:
            import pandas as pd
            df = pd.read_csv(METADATA_PATH)
            csv_row_count = len(df)
        except Exception as e:
            issues.append(f"CSV read error: {str(e)}")

    return {
        "status": "ok" if not issues else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "metadata_csv": {
                "ok": csv_ok,
                "path": str(METADATA_PATH),
                "row_count": csv_row_count
            },
            "cs_files_root": {
                "ok": cs_root_ok,
                "path": str(CS_ROOT),
                "industry_count": industry_count,
                "total_files": file_count,
                "breakdown": industry_breakdown
            }
        },
        "issues": issues
    }
