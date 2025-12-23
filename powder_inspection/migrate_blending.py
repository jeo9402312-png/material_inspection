#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배합 작업 관리를 위한 데이터베이스 마이그레이션 스크립트

추가되는 테이블:
1. recipe: 제품별 배합 규격서 (BOM)
2. blending_work: 배합 작업 기록
3. material_input: 원재료 투입 이력
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def migrate_database():
    """배합 관리 테이블 추가"""

    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        print("먼저 init_db.py를 실행하세요.")
        return False

    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()

        # WAL 모드 활성화 (동시성 향상)
        cursor.execute('PRAGMA journal_mode = WAL')
        cursor.execute('PRAGMA busy_timeout = 30000')

        print("=" * 60)
        print("배합 작업 관리 테이블 마이그레이션 시작")
        print("=" * 60)

        # 1. Recipe 테이블 생성
        print("\n[1/3] Recipe 테이블 생성 중...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name VARCHAR(100) NOT NULL,
                product_code VARCHAR(50),
                powder_name VARCHAR(100) NOT NULL,
                powder_category VARCHAR(20) DEFAULT 'incoming',
                ratio DECIMAL(5,2) NOT NULL,
                target_weight DECIMAL(10,2),
                tolerance_percent DECIMAL(5,2) DEFAULT 5.0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50)
            )
        ''')

        # Recipe 인덱스
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recipe_product
            ON recipe(product_name)
        ''')

        print("   ✓ Recipe 테이블 생성 완료")

        # 2. Blending Work 테이블 생성
        print("\n[2/3] Blending Work 테이블 생성 중...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blending_work (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order VARCHAR(50) UNIQUE NOT NULL,
                product_name VARCHAR(100) NOT NULL,
                product_code VARCHAR(50),
                batch_lot VARCHAR(50) UNIQUE NOT NULL,
                target_total_weight DECIMAL(10,2),
                actual_total_weight DECIMAL(10,2),
                blending_time INTEGER,
                blending_temperature DECIMAL(5,2),
                blending_rpm INTEGER,
                operator VARCHAR(50),
                status VARCHAR(20) DEFAULT 'in_progress',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Blending Work 인덱스
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_batch_lot
            ON blending_work(batch_lot)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_work_order
            ON blending_work(work_order)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_status
            ON blending_work(status)
        ''')

        print("   ✓ Blending Work 테이블 생성 완료")

        # 3. Material Input 테이블 생성
        print("\n[3/3] Material Input 테이블 생성 중...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS material_input (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blending_work_id INTEGER NOT NULL,
                powder_name VARCHAR(100) NOT NULL,
                powder_category VARCHAR(20) DEFAULT 'incoming',
                material_lot VARCHAR(50) NOT NULL,
                target_weight DECIMAL(10,2) NOT NULL,
                actual_weight DECIMAL(10,2) NOT NULL,
                weight_deviation DECIMAL(5,2),
                is_valid BOOLEAN DEFAULT 1,
                validation_message TEXT,
                input_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                input_by VARCHAR(50),
                FOREIGN KEY (blending_work_id) REFERENCES blending_work(id) ON DELETE CASCADE
            )
        ''')

        # Material Input 인덱스
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_material_input_work
            ON material_input(blending_work_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_material_input_lot
            ON material_input(material_lot)
        ''')

        print("   ✓ Material Input 테이블 생성 완료")

        # 샘플 데이터 확인
        print("\n" + "=" * 60)
        print("샘플 Recipe 데이터 추가 여부 확인")
        print("=" * 60)

        cursor.execute('SELECT COUNT(*) FROM recipe')
        recipe_count = cursor.fetchone()[0]

        if recipe_count == 0:
            print("\n샘플 Recipe 데이터를 추가합니다...")

            # 샘플 제품 1: 표준 배합 철분
            sample_recipes = [
                ('표준배합철분', 'STD-001', '순철분말', 'incoming', 60.0, 3000.0, 2.0, '시스템'),
                ('표준배합철분', 'STD-001', '구리분말', 'incoming', 30.0, 1500.0, 2.0, '시스템'),
                ('표준배합철분', 'STD-001', '흑연분말', 'incoming', 10.0, 500.0, 2.0, '시스템'),

                # 샘플 제품 2: 고강도 배합
                ('고강도배합', 'HS-001', '순철분말', 'incoming', 70.0, 3500.0, 2.0, '시스템'),
                ('고강도배합', 'HS-001', '니켈분말', 'incoming', 20.0, 1000.0, 2.0, '시스템'),
                ('고강도배합', 'HS-001', '몰리브덴분말', 'incoming', 10.0, 500.0, 2.0, '시스템'),
            ]

            cursor.executemany('''
                INSERT INTO recipe (product_name, product_code, powder_name, powder_category,
                                    ratio, target_weight, tolerance_percent, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_recipes)

            print(f"   ✓ {len(sample_recipes)}개의 샘플 Recipe 추가 완료")
        else:
            print(f"   ℹ️  이미 {recipe_count}개의 Recipe가 존재합니다. 샘플 데이터 추가를 건너뜁니다.")

        conn.commit()

        # 최종 확인
        print("\n" + "=" * 60)
        print("마이그레이션 완료 - 테이블 현황")
        print("=" * 60)

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%recipe%' OR name LIKE '%blending%' OR name LIKE '%material%')")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f"  📋 {table_name}: {count} 레코드")

        conn.close()

        print("\n✅ 배합 작업 관리 마이그레이션 성공!")
        return True

    except sqlite3.Error as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("\n🔧 배합 작업 관리 시스템 - 데이터베이스 마이그레이션")
    print(f"📁 대상 DB: {DB_PATH}")
    print()

    success = migrate_database()

    if success:
        print("\n" + "=" * 60)
        print("다음 단계:")
        print("  1. 서버 재시작: python app.py")
        print("  2. Admin 페이지에서 Recipe 관리 확인")
        print("=" * 60)
    else:
        print("\n마이그레이션에 실패했습니다. 오류를 확인하세요.")
