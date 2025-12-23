"""
데이터베이스 마이그레이션 스크립트
수입검사/배합검사 분리를 위한 category 컬럼 추가
"""

import sqlite3
from contextlib import closing

DATABASE = 'database.db'

def migrate_database():
    """데이터베이스 스키마 업데이트"""
    print("=== 데이터베이스 마이그레이션 시작 ===")

    conn = sqlite3.connect(DATABASE, timeout=30.0)
    cursor = conn.cursor()

    # WAL 모드 활성화 (동시성 향상)
    cursor.execute('PRAGMA journal_mode = WAL')
    cursor.execute('PRAGMA busy_timeout = 30000')

    try:
        # 1. powder_spec 테이블에 category 컬럼 추가
        print("\n1. powder_spec 테이블 업데이트 중...")
        try:
            cursor.execute("ALTER TABLE powder_spec ADD COLUMN category VARCHAR(20) DEFAULT 'incoming'")
            print("   ✓ category 컬럼 추가됨")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   - category 컬럼이 이미 존재함 (건너뜀)")
            else:
                raise

        # 기존 데이터를 모두 'incoming'으로 설정
        cursor.execute("UPDATE powder_spec SET category = 'incoming' WHERE category IS NULL OR category = ''")
        print("   ✓ 기존 데이터를 'incoming'으로 설정")

        # 2. inspection_progress 테이블에 category 컬럼 추가
        print("\n2. inspection_progress 테이블 업데이트 중...")
        try:
            cursor.execute("ALTER TABLE inspection_progress ADD COLUMN category VARCHAR(20) DEFAULT 'incoming'")
            print("   ✓ category 컬럼 추가됨")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   - category 컬럼이 이미 존재함 (건너뜀)")
            else:
                raise

        cursor.execute("UPDATE inspection_progress SET category = 'incoming' WHERE category IS NULL OR category = ''")
        print("   ✓ 기존 데이터를 'incoming'으로 설정")

        # 3. inspection_result 테이블에 category 컬럼 추가
        print("\n3. inspection_result 테이블 업데이트 중...")
        try:
            cursor.execute("ALTER TABLE inspection_result ADD COLUMN category VARCHAR(20) DEFAULT 'incoming'")
            print("   ✓ category 컬럼 추가됨")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   - category 컬럼이 이미 존재함 (건너뜀)")
            else:
                raise

        cursor.execute("UPDATE inspection_result SET category = 'incoming' WHERE category IS NULL OR category = ''")
        print("   ✓ 기존 데이터를 'incoming'으로 설정")

        # 4. particle_size 테이블도 category 컬럼 추가 (수입/배합 구분)
        print("\n4. particle_size 테이블 업데이트 중...")
        try:
            cursor.execute("ALTER TABLE particle_size ADD COLUMN category VARCHAR(20) DEFAULT 'incoming'")
            print("   ✓ category 컬럼 추가됨")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   - category 컬럼이 이미 존재함 (건너뜀)")
            else:
                raise

        cursor.execute("UPDATE particle_size SET category = 'incoming' WHERE category IS NULL OR category = ''")
        print("   ✓ 기존 데이터를 'incoming'으로 설정")

        conn.commit()

        # 5. 결과 확인
        print("\n=== 마이그레이션 결과 확인 ===")

        cursor.execute("SELECT COUNT(*) FROM powder_spec WHERE category = 'incoming'")
        count = cursor.fetchone()[0]
        print(f"powder_spec: {count}개 레코드가 'incoming'으로 설정됨")

        cursor.execute("SELECT COUNT(*) FROM inspection_progress WHERE category = 'incoming'")
        count = cursor.fetchone()[0]
        print(f"inspection_progress: {count}개 레코드가 'incoming'으로 설정됨")

        cursor.execute("SELECT COUNT(*) FROM inspection_result WHERE category = 'incoming'")
        count = cursor.fetchone()[0]
        print(f"inspection_result: {count}개 레코드가 'incoming'으로 설정됨")

        cursor.execute("SELECT COUNT(*) FROM particle_size WHERE category = 'incoming'")
        count = cursor.fetchone()[0]
        print(f"particle_size: {count}개 레코드가 'incoming'으로 설정됨")

        print("\n=== 마이그레이션 완료! ===")
        print("이제 시스템을 재시작하세요.")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
