"""
배합 규격서에 Main 분말 지정 기능 추가 마이그레이션
recipe 테이블에 is_main 필드 추가
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

        print("=== Main 분말 지정 기능 추가 마이그레이션 시작 ===\n")

        # 1. recipe 테이블에 is_main 컬럼이 있는지 확인
        cursor.execute("PRAGMA table_info(recipe)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_main' not in columns:
            print("1. recipe 테이블에 is_main 컬럼 추가 중...")
            cursor.execute('''
                ALTER TABLE recipe
                ADD COLUMN is_main BOOLEAN DEFAULT 0
            ''')
            print("   ✓ is_main 컬럼 추가 완료")
        else:
            print("1. recipe 테이블에 is_main 컬럼이 이미 존재합니다.")

        # 2. 기존 데이터에서 비율이 가장 높은 분말을 main으로 설정
        print("\n2. 기존 배합 규격서의 main 분말 설정 중...")

        # 각 제품별로 비율이 가장 높은 분말 찾기
        cursor.execute('''
            SELECT DISTINCT product_name FROM recipe WHERE is_active = 1
        ''')
        products = cursor.fetchall()

        for (product_name,) in products:
            # 해당 제품의 최대 비율 찾기
            cursor.execute('''
                SELECT id, powder_name, ratio
                FROM recipe
                WHERE product_name = ? AND is_active = 1
                ORDER BY ratio DESC
                LIMIT 1
            ''', (product_name,))

            main_recipe = cursor.fetchone()
            if main_recipe:
                recipe_id, powder_name, ratio = main_recipe
                cursor.execute('''
                    UPDATE recipe
                    SET is_main = 1
                    WHERE id = ?
                ''', (recipe_id,))
                print(f"   ✓ {product_name}: {powder_name} ({ratio}%) → Main 분말로 설정")

        conn.commit()
        print("\n=== 마이그레이션 완료 ===")

        # 결과 확인
        print("\n=== Main 분말 설정 결과 ===")
        cursor.execute('''
            SELECT product_name, powder_name, ratio, is_main
            FROM recipe
            WHERE is_active = 1
            ORDER BY product_name, is_main DESC, ratio DESC
        ''')

        current_product = None
        for row in cursor.fetchall():
            product_name, powder_name, ratio, is_main = row
            if current_product != product_name:
                print(f"\n[{product_name}]")
                current_product = product_name
            main_mark = " ⭐ MAIN" if is_main else ""
            print(f"  - {powder_name}: {ratio}%{main_mark}")

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
