"""
ONE FILE TO RUN EVERYTHING.

    python run.py            -> uses your real Kaggle data in data/raw
    python run.py --demo     -> uses fake demo data (only to test that setup works)
    python run.py --powerbi  -> also exports CSV files for Power BI into exports/
    python run.py --no-app   -> build the data files but do not start the dashboard
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
args = set(sys.argv[1:])
demo = "--demo" in args


def ensure_packages():
    try:
        import duckdb, pandas, plotly, pyarrow, streamlit  # noqa: F401
    except ImportError:
        print("Installing required packages (one time only) ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r",
                               str(ROOT / "requirements-dev.txt")])


def main():
    ensure_packages()

    if demo:
        print("== DEMO MODE: fake data, for testing only. Do not use these numbers on your resume. ==\n")
        subprocess.check_call([sys.executable, str(ROOT / "pipeline" / "make_demo_data.py")])
        raw = ROOT / "data" / "demo_raw"
    else:
        raw = ROOT / "data" / "raw"

    cmd = [sys.executable, str(ROOT / "pipeline" / "build_data.py"), "--raw", str(raw)]
    if "--powerbi" in args:
        cmd.append("--powerbi")
    if subprocess.call(cmd) != 0:
        sys.exit(1)

    if "--no-app" in args:
        return
    print("\nStarting dashboard at http://localhost:8501  (press Ctrl+C to stop)\n")
    subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "app.py"),
                     "--browser.gatherUsageStats", "false"])


if __name__ == "__main__":
    main()
