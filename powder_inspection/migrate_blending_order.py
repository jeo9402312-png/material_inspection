#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배합작업지시서 기능 추가를 위한 데이터베이스 마이그레이션 스크립트

Changes:
1. blending_order 테이블 생성 (배합작업지시서)
2. blending_work 테이블에 work_order_id 컬럼 추가
3. work_order 컬럼을 nullable로 변경 (작업지시서 연동 시 선택사항)
"""

import sqlite3
from contextlib import closing
from datetime import datetime

DATABASE = 'database.db'

def migrate():
    """마이그레이션 실행"""

    with closing(sqlite3.connect(DATABASE)) as conn:
        cursor = conn.cursor()

        print("=" * 60)
        print("배합작업지시서 마이그레이션 시작")
        print("=" * 60)

        # 1. blending_order 테이블 생성
        print("\n1. blending_order 테이블 생성 중...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blending_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_number VARCHAR(50) UNIQUE NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            product_code VARCHAR(50),
            total_target_weight DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'in_progress',
            created_by VARCHAR(50),
            created_date DATE DEFAULT (DATE('now')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 인덱스 생성
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_order_number
            ON blending_order(work_order_number)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_order_status
            ON blending_order(status)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_blending_order_date
            ON blending_order(created_date)
        ''')

        print("   ✓ blending_order 테이블 생성 완료")

        # 2. blending_work 테이블에 work_order_id 컬럼 추가
        print("\n2. blending_work 테이블 확인 중...")

        # 컬럼 존재 여부 확인
        cursor.execute("PRAGMA table_info(blending_work)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'work_order_id' not in columns:
            print("   work_order_id 컬럼 추가 중...")
            cursor.execute('''
                ALTER TABLE blending_work
                ADD COLUMN work_order_id INTEGER REFERENCES blending_order(id) ON DELETE SET NULL
            ''')

            # 인덱스 생성
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_blending_work_order_id
                ON blending_work(work_order_id)
            ''')

            print("   ✓ work_order_id 컬럼 추가 완료")
        else:
            print("   ⊙ work_order_id 컬럼이 이미 존재합니다")

        # 3. 기존 work_order 컬럼을 nullable로 변경하려면 테이블 재생성 필요
        # SQLite는 ALTER COLUMN을 지원하지 않으므로, 새 테이블 생성 후 데이터 복사
        print("\n3. blending_work 테이블 스키마 업데이트 중...")

        # work_order 컬럼이 NOT NULL인지 확인
        cursor.execute("PRAGMA table_info(blending_work)")
        work_order_col = [col for col in cursor.fetchall() if col[1] == 'work_order']

        if work_order_col and work_order_col[0][3] == 1:  # notnull = 1
            print("   work_order를 nullable로 변경 중...")

            # 임시 테이블 생성
            cursor.execute('''
            CREATE TABLE blending_work_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER REFERENCES blending_order(id) ON DELETE SET NULL,
                work_order VARCHAR(50),
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

            # 데이터 복사
            if 'work_order_id' in columns:
                cursor.execute('''
                INSERT INTO blending_work_new
                SELECT id, work_order_id, work_order, product_name, product_code, batch_lot,
                       target_total_weight, actual_total_weight, blending_time, blending_temperature,
                       blending_rpm, operator, status, start_time, end_time, notes,
                       created_at, updated_at
                FROM blending_work
                ''')
            else:
                cursor.execute('''
                INSERT INTO blending_work_new
                (id, work_order, product_name, product_code, batch_lot,
                 target_total_weight, actual_total_weight, blending_time, blending_temperature,
                 blending_rpm, operator, status, start_time, end_time, notes,
                 created_at, updated_at)
                SELECT id, work_order, product_name, product_code, batch_lot,
                       target_total_weight, actual_total_weight, blending_time, blending_temperature,
                       blending_rpm, operator, status, start_time, end_time, notes,
                       created_at, updated_at
                FROM blending_work
                ''')

            # 기존 테이블 삭제 및 새 테이블 rename
            cursor.execute('DROP TABLE blending_work')
            cursor.execute('ALTER TABLE blending_work_new RENAME TO blending_work')

            # 인덱스 재생성
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_blending_work_order_id
                ON blending_work(work_order_id)
            ''')

            print("   ✓ work_order를 nullable로 변경 완료")
        else:
            print("   ⊙ work_order가 이미 nullable입니다")

        # 커밋
        conn.commit()

        print("\n" + "=" * 60)
        print("✅ 마이그레이션 완료!")
        print("=" * 60)

        # 테이블 확인
        print("\n테이블 목록:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")

        print("\nblending_order 스키마:")
        cursor.execute("PRAGMA table_info(blending_order)")
        for col in cursor.fetchall():
            print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':10}")

        print("\nblending_work 스키마 (주요 컬럼):")
        cursor.execute("PRAGMA table_info(blending_work)")
        for col in cursor.fetchall():
            if col[1] in ['work_order_id', 'work_order', 'product_name', 'batch_lot']:
                print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':10}")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
