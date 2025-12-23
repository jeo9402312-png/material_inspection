"""
blending_work 테이블에 main_powder_weights 필드 추가 마이그레이션
Main 분말 중량 정보를 JSON 형태로 저장
"""

import sqlite3
import os

def migrate():
    """데이터베이스 마이그레이션 실행"""

    db_path = 'database.db'

    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()

        print("=== Main 분말 중량 저장 기능 추가 마이그레이션 시작 ===\n")

        # 1. blending_work 테이블에 main_powder_weights 컬럼이 있는지 확인
        cursor.execute("PRAGMA table_info(blending_work)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'main_powder_weights' not in columns:
            print("1. blending_work 테이블에 main_powder_weights 컬럼 추가 중...")
            cursor.execute('''
                ALTER TABLE blending_work
                ADD COLUMN main_powder_weights TEXT
            ''')
            print("   ✓ main_powder_weights 컬럼 추가 완료")
        else:
            print("1. blending_work 테이블에 main_powder_weights 컬럼이 이미 존재합니다.")

        conn.commit()
        print("\n=== 마이그레이션 완료 ===")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = migrate()
    if success:
        print("\n✅ 마이그레이션이 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 마이그레이션이 실패했습니다.")
