# 01-Analysis/verify_brain.py
"""
SHawn-BIO Brain Module Verification
SHawn-BOT 연동 상태를 검증합니다.
"""
import os
import sys

def inject_brain_paths():
    """SHawn-BOT/Brain 후보 경로를 sys.path에 주입"""
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(curr_dir)
    workspace_parent = os.path.dirname(root_dir)
    env_brain_path = os.environ.get("SHAWN_BOT_PATH")
    candidates = [
        env_brain_path,
        os.path.join(root_dir, "99-System"),
        os.path.join(workspace_parent, "SHawn-LAB", "SHawn-BOT"),
        os.path.join(workspace_parent, "SHawn-Brain"),
        os.path.join(workspace_parent, "SHawn-Lab-Vault", "99-System"),
        os.path.join(workspace_parent, "SHawn-Lab-Vault", "99-System", "shawn_bot"),
    ]
    for base in candidates:
        if not base:
            continue
        for path in [base, os.path.join(base, "99-System"), os.path.join(base, "shawn_bot")]:
            if os.path.isdir(path) and path not in sys.path:
                sys.path.insert(0, path)


def verify_brain():
    """Brain 모듈 연동 상태 검증"""
    print("=" * 50)
    print("SHawn-BIO: Brain Module Verification")
    print("=" * 50)

    # 1. SHawnBrainV4 검증
    try:
        from shawn_brain_v4 import SHawnBrainV4
        print("[OK] SHawnBrainV4 imported successfully")
        try:
            brain = SHawnBrainV4(use_ensemble=False)
            print("[OK] SHawnBrainV4 initialized")
        except Exception as e:
            print(f"[WARN] SHawnBrainV4 init failed: {e}")
    except Exception as e:
        print(f"[SKIP] SHawnBrainV4 not available ({e})")

    # 2. SHawnBrain 검증
    try:
        from shawn_brain import SHawnBrain
        print("[OK] SHawnBrain imported successfully")
        try:
            brain = SHawnBrain()
            print("[OK] SHawnBrain initialized")
        except Exception as e:
            print(f"[WARN] SHawnBrain init failed: {e}")
    except Exception as e:
        print(f"[SKIP] SHawnBrain not available ({e})")

    # 2-1. SHawnBrainV2 검증
    try:
        from shawn_brain_v2 import SHawnBrainV2
        print("[OK] SHawnBrainV2 imported successfully")
        try:
            brain = SHawnBrainV2()
            print("[OK] SHawnBrainV2 initialized")
        except Exception as e:
            print(f"[WARN] SHawnBrainV2 init failed: {e}")
    except Exception as e:
        print(f"[SKIP] SHawnBrainV2 not available ({e})")

    # 3. SBI Pipeline 검증
    print("-" * 50)
    try:
        from sbi_pipeline import SBIPipeline
        print("[OK] SBIPipeline imported successfully")
        try:
            pipeline = SBIPipeline()
            print(f"[OK] SBIPipeline initialized")
            status = pipeline.get_status()
            print(f"     OneDrive: {status['onedrive_path']}")
            print(f"     DB Path (active): {status['db_path']}")
            print(f"     DB Path (legacy): {status['legacy_db_path']}")
            print(f"     Index/Data Exists: {status['index_exists']}/{status['data_exists']}")
            print(f"     Chunks/Files: {status['chunks']}/{status['indexed_files']}")
        except Exception as e:
            print(f"[WARN] SBIPipeline init failed: {e}")
    except ImportError as e:
        print(f"[ERROR] SBIPipeline import failed: {e}")

    # 4. ResearchEngine 검증
    print("-" * 50)
    try:
        from research_engine import ResearchEngine
        print("[OK] ResearchEngine imported successfully")
        try:
            engine = ResearchEngine()
            print("[OK] ResearchEngine initialized")
            print(f"     Brain: {'Available' if engine.brain else 'Not available'}")
            print(f"     Pipeline: {'Available' if engine.pipeline else 'Not available'}")
        except Exception as e:
            print(f"[WARN] ResearchEngine init failed: {e}")
    except ImportError as e:
        print(f"[ERROR] ResearchEngine import failed: {e}")

    print("=" * 50)
    print("Verification complete.")


if __name__ == "__main__":
    # 현재 디렉토리를 Python 경로에 추가
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    if curr_dir not in sys.path:
        sys.path.insert(0, curr_dir)
    inject_brain_paths()

    verify_brain()
