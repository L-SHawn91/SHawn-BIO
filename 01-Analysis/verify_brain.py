# 01-Analysis/verify_brain.py
"""
SHawn-BIO Brain Module Verification
SHawn-BOT 연동 상태를 검증합니다.
"""
import os
import sys

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
    except ImportError:
        print("[SKIP] SHawnBrainV4 not available")

    # 2. SHawnBrain 검증
    try:
        from shawn_brain import SHawnBrain
        print("[OK] SHawnBrain imported successfully")
        try:
            brain = SHawnBrain()
            print("[OK] SHawnBrain initialized")
        except Exception as e:
            print(f"[WARN] SHawnBrain init failed: {e}")
    except ImportError:
        print("[SKIP] SHawnBrain not available")

    # 3. SBI Pipeline 검증
    print("-" * 50)
    try:
        from sbi_pipeline import SBIPipeline
        print("[OK] SBIPipeline imported successfully")
        try:
            pipeline = SBIPipeline()
            print(f"[OK] SBIPipeline initialized")
            print(f"     OneDrive: {pipeline.onedrive_path}")
            print(f"     DB Path: {pipeline.db_path}")
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

    verify_brain()
