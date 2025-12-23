"""
분말 검사 시스템 - 데이터베이스 초기화 스크립트
SQLite 데이터베이스를 생성하고 초기 테이블 및 샘플 데이터를 입력합니다.
"""

import sqlite3
import os

def init_database():
    """데이터베이스 초기화 및 테이블 생성"""

    # 스크립트 디렉토리 기반으로 데이터베이스 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'database.db')

    # 기존 DB 파일 삭제 (초기화)
    if os.path.exists(db_path):
        print("기존 데이터베이스 삭제 중...")
        os.remove(db_path)

    # 데이터베이스 연결
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()

    # WAL 모드 활성화 (동시성 향상)
    cursor.execute('PRAGMA journal_mode = WAL')
    cursor.execute('PRAGMA busy_timeout = 30000')

    print("데이터베이스 생성 중...")

    # 1. 분말 사양 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS powder_spec (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        powder_name TEXT UNIQUE NOT NULL,

        -- 유동도
        flow_rate_min REAL,
        flow_rate_max REAL,
        flow_rate_type TEXT,

        -- 겉보기밀도
        apparent_density_min REAL,
        apparent_density_max REAL,
        apparent_density_type TEXT,

        -- C함량
        c_content_min REAL,
        c_content_max REAL,
        c_content_type TEXT,

        -- Cu함량
        cu_content_min REAL,
        cu_content_max REAL,
        cu_content_type TEXT,

        -- 수분도
        moisture_min REAL,
        moisture_max REAL,
        moisture_type TEXT,

        -- 회분도
        ash_min REAL,
        ash_max REAL,
        ash_type TEXT,

        -- 소결변화율
        sinter_change_rate_min REAL,
        sinter_change_rate_max REAL,
        sinter_change_rate_type TEXT,

        -- 소결강도
        sinter_strength_min REAL,
        sinter_strength_max REAL,
        sinter_strength_type TEXT,

        -- 성형강도
        forming_strength_min REAL,
        forming_strength_max REAL,
        forming_strength_type TEXT,

        -- 성형하중
        forming_load_min REAL,
        forming_load_max REAL,
        forming_load_type TEXT,

        -- 입도분석
        particle_size_type TEXT,

        -- 검사 구분 (수입검사/배합검사)
        category VARCHAR(20) DEFAULT 'incoming'
    )
    ''')

    # 2. 검사 결과 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        powder_name TEXT NOT NULL,
        lot_number TEXT NOT NULL,
        inspector TEXT NOT NULL,
        inspection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        inspection_type TEXT NOT NULL,

        -- 유동도
        flow_rate_1 REAL,
        flow_rate_2 REAL,
        flow_rate_3 REAL,
        flow_rate_avg REAL,
        flow_rate_result TEXT,

        -- 겉보기밀도 (원본 데이터)
        apparent_density_empty_cup_1 REAL,
        apparent_density_powder_weight_1 REAL,
        apparent_density_1 REAL,
        apparent_density_empty_cup_2 REAL,
        apparent_density_powder_weight_2 REAL,
        apparent_density_2 REAL,
        apparent_density_empty_cup_3 REAL,
        apparent_density_powder_weight_3 REAL,
        apparent_density_3 REAL,
        apparent_density_avg REAL,
        apparent_density_result TEXT,

        -- C함량
        c_content_1 REAL,
        c_content_2 REAL,
        c_content_3 REAL,
        c_content_avg REAL,
        c_content_result TEXT,

        -- Cu함량
        cu_content_1 REAL,
        cu_content_2 REAL,
        cu_content_3 REAL,
        cu_content_avg REAL,
        cu_content_result TEXT,

        -- 수분도 (원본 데이터)
        moisture_initial_weight_1 REAL,
        moisture_dried_weight_1 REAL,
        moisture_1 REAL,
        moisture_initial_weight_2 REAL,
        moisture_dried_weight_2 REAL,
        moisture_2 REAL,
        moisture_initial_weight_3 REAL,
        moisture_dried_weight_3 REAL,
        moisture_3 REAL,
        moisture_avg REAL,
        moisture_result TEXT,

        -- 회분도 (원본 데이터)
        ash_initial_weight_1 REAL,
        ash_ash_weight_1 REAL,
        ash_1 REAL,
        ash_initial_weight_2 REAL,
        ash_ash_weight_2 REAL,
        ash_2 REAL,
        ash_initial_weight_3 REAL,
        ash_ash_weight_3 REAL,
        ash_3 REAL,
        ash_avg REAL,
        ash_result TEXT,

        -- 소결변화율
        sinter_change_rate_1 REAL,
        sinter_change_rate_2 REAL,
        sinter_change_rate_3 REAL,
        sinter_change_rate_avg REAL,
        sinter_change_rate_result TEXT,

        -- 소결강도
        sinter_strength_1 REAL,
        sinter_strength_2 REAL,
        sinter_strength_3 REAL,
        sinter_strength_avg REAL,
        sinter_strength_result TEXT,

        -- 성형강도
        forming_strength_1 REAL,
        forming_strength_2 REAL,
        forming_strength_3 REAL,
        forming_strength_avg REAL,
        forming_strength_result TEXT,

        -- 성형하중
        forming_load_1 REAL,
        forming_load_2 REAL,
        forming_load_3 REAL,
        forming_load_avg REAL,
        forming_load_result TEXT,

        -- 입도분석
        particle_size_180_1 REAL,
        particle_size_180_2 REAL,
        particle_size_180_avg REAL,
        particle_size_180_result TEXT,

        particle_size_150_1 REAL,
        particle_size_150_2 REAL,
        particle_size_150_avg REAL,
        particle_size_150_result TEXT,

        particle_size_106_1 REAL,
        particle_size_106_2 REAL,
        particle_size_106_avg REAL,
        particle_size_106_result TEXT,

        particle_size_75_1 REAL,
        particle_size_75_2 REAL,
        particle_size_75_avg REAL,
        particle_size_75_result TEXT,

        particle_size_45_1 REAL,
        particle_size_45_2 REAL,
        particle_size_45_avg REAL,
        particle_size_45_result TEXT,

        particle_size_45m_1 REAL,
        particle_size_45m_2 REAL,
        particle_size_45m_avg REAL,
        particle_size_45m_result TEXT,

        particle_size_result TEXT,
        final_result TEXT,

        -- 검사 구분 (수입검사/배합검사)
        category VARCHAR(20) DEFAULT 'incoming',

        UNIQUE(powder_name, lot_number)
    )
    ''')

    # 3. 진행중 검사 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        powder_name TEXT NOT NULL,
        lot_number TEXT NOT NULL,
        inspection_type TEXT NOT NULL,
        inspector TEXT NOT NULL,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_items TEXT,  -- JSON 배열
        total_items TEXT,      -- JSON 배열
        progress TEXT,

        -- 검사 구분 (수입검사/배합검사)
        category VARCHAR(20) DEFAULT 'incoming',

        UNIQUE(powder_name, lot_number)
    )
    ''')

    # 4. 입도분석 규격 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS particle_size (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        powder_name TEXT NOT NULL,
        mesh_size TEXT NOT NULL,
        min_value REAL NOT NULL,
        max_value REAL NOT NULL,

        UNIQUE(powder_name, mesh_size)
    )
    ''')

    # 5. 검사자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspector (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # 6. 작업자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operator (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # 7. Recipe (배합 규격서) 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name VARCHAR(100) NOT NULL,
        product_code VARCHAR(50),
        powder_name VARCHAR(100) NOT NULL,
        powder_category VARCHAR(20) DEFAULT 'incoming',
        ratio DECIMAL(5,2) NOT NULL,
        target_weight DECIMAL(10,2),
        tolerance_percent DECIMAL(5,2) DEFAULT 0.05,
        is_main BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(50)
    )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_recipe_product
        ON recipe(product_name)
    ''')

    # 8. Blending Order (배합작업지시서) 테이블
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

    # 9. Blending Work (배합 작업) 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blending_work (
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
        main_powder_weights TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_blending_work_order_id
        ON blending_work(work_order_id)
    ''')
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

    # 10. Material Input (원재료 투입) 테이블
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

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_material_input_work
        ON material_input(blending_work_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_material_input_lot
        ON material_input(material_lot)
    ''')

    print("테이블 생성 완료!")

    # 샘플 데이터 입력
    print("샘플 데이터 입력 중...")

    # 분말 사양 샘플 데이터
    # 유동도만 '일상', 나머지는 모두 '정기'
    # 수입검사용 분말 3개 (원료)
    powder_specs = [
        ('순철분말', 25, 35, '일상', 2.5, 3.0, '정기', 0.5, 0.8, '정기', None, None, '비활성', 0, 0.5, '정기', 0, 1.0, '정기', 5, 8, '정기', 850, 950, '정기', 120, 150, '정기', 180, 220, '정기', '정기', 'incoming'),
        ('구리분말', 20, 30, '일상', 2.0, 2.8, '정기', 0.4, 0.7, '정기', 1.0, 2.0, '정기', 0, 0.3, '정기', 0, 0.8, '정기', 4, 7, '정기', 800, 900, '정기', 100, 140, '정기', 160, 200, '정기', '정기', 'incoming'),
        ('흑연분말', 30, 40, '일상', 3.0, 3.5, '정기', 0.6, 0.9, '정기', 2.0, 3.0, '정기', 0, 0.4, '정기', 0, 1.2, '정기', 6, 9, '정기', 900, 1000, '정기', 130, 160, '정기', 200, 240, '정기', '정기', 'incoming'),
        # 배합검사용 분말 3개 (완제품)
        ('표준배합철분', 28, 36, '일상', 2.7, 3.2, '정기', 0.5, 0.85, '정기', 0.6, 1.2, '정기', 0, 0.4, '정기', 0, 0.9, '정기', 5.5, 8.5, '정기', 870, 970, '정기', 125, 155, '정기', 185, 225, '정기', '정기', 'mixing'),
        ('고강도배합분말', 26, 34, '일상', 2.8, 3.3, '정기', 0.55, 0.88, '정기', 0.4, 1.0, '정기', 0, 0.35, '정기', 0, 0.85, '정기', 6, 9, '정기', 900, 980, '정기', 130, 160, '정기', 190, 230, '정기', '정기', 'mixing'),
        ('경량배합분말', 30, 38, '일상', 2.4, 2.9, '정기', 0.6, 0.95, '정기', 0.6, 1.4, '정기', 0, 0.45, '정기', 0, 1.0, '정기', 5, 8, '정기', 850, 950, '정기', 120, 150, '정기', 180, 220, '정기', '정기', 'mixing')
    ]

    cursor.executemany('''
        INSERT INTO powder_spec (
            powder_name,
            flow_rate_min, flow_rate_max, flow_rate_type,
            apparent_density_min, apparent_density_max, apparent_density_type,
            c_content_min, c_content_max, c_content_type,
            cu_content_min, cu_content_max, cu_content_type,
            moisture_min, moisture_max, moisture_type,
            ash_min, ash_max, ash_type,
            sinter_change_rate_min, sinter_change_rate_max, sinter_change_rate_type,
            sinter_strength_min, sinter_strength_max, sinter_strength_type,
            forming_strength_min, forming_strength_max, forming_strength_type,
            forming_load_min, forming_load_max, forming_load_type,
            particle_size_type,
            category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', powder_specs)

    # 입도분석 규격 샘플 데이터 (수입검사용 분말에 대해서만)
    particle_specs = [
        ('순철분말', '+180 um', 5.0, 10.0),
        ('순철분말', '+150 um', 10.0, 15.0),
        ('순철분말', '+106 um', 15.0, 20.0),
        ('순철분말', '+75 um', 20.0, 25.0),
        ('순철분말', '+45 um', 15.0, 20.0),
        ('순철분말', '-45 um', 10.0, 15.0),
        ('구리분말', '+180 um', 3.0, 8.0),
        ('구리분말', '+150 um', 8.0, 12.0),
        ('구리분말', '+106 um', 12.0, 18.0),
        ('구리분말', '+75 um', 18.0, 23.0),
        ('구리분말', '+45 um', 12.0, 18.0),
        ('구리분말', '-45 um', 8.0, 12.0),
        ('흑연분말', '+180 um', 4.0, 9.0),
        ('흑연분말', '+150 um', 9.0, 14.0),
        ('흑연분말', '+106 um', 14.0, 19.0),
        ('흑연분말', '+75 um', 19.0, 24.0),
        ('흑연분말', '+45 um', 14.0, 19.0),
        ('흑연분말', '-45 um', 9.0, 14.0)
    ]

    cursor.executemany('''
        INSERT INTO particle_size (powder_name, mesh_size, min_value, max_value)
        VALUES (?, ?, ?, ?)
    ''', particle_specs)

    # 검사자 샘플 데이터
    inspectors = [('김철수',), ('이영희',), ('박민수',), ('정수진',)]
    cursor.executemany('INSERT INTO inspector (name) VALUES (?)', inspectors)

    # 작업자 샘플 데이터
    operators = [('최준호',), ('한지민',), ('강태우',)]
    cursor.executemany('INSERT INTO operator (name) VALUES (?)', operators)

    # Recipe 샘플 데이터 (3개 제품, 각각 수입검사용 분말 조합)
    sample_recipes = [
        # 표준배합철분 = 순철 60% + 구리 30% + 흑연 10%
        ('표준배합철분', 'STD-001', '순철분말', 'incoming', 60.0, None, 0.5, 1, '시스템'),  # Main
        ('표준배합철분', 'STD-001', '구리분말', 'incoming', 30.0, None, 0.5, 0, '시스템'),
        ('표준배합철분', 'STD-001', '흑연분말', 'incoming', 10.0, None, 0.5, 0, '시스템'),
        # 고강도배합분말 = 순철 70% + 구리 20% + 흑연 10%
        ('고강도배합분말', 'HIGH-002', '순철분말', 'incoming', 70.0, None, 0.3, 1, '시스템'),  # Main
        ('고강도배합분말', 'HIGH-002', '구리분말', 'incoming', 20.0, None, 0.3, 0, '시스템'),
        ('고강도배합분말', 'HIGH-002', '흑연분말', 'incoming', 10.0, None, 0.3, 0, '시스템'),
        # 경량배합분말 = 순철 50% + 구리 30% + 흑연 20%
        ('경량배합분말', 'LIGHT-003', '순철분말', 'incoming', 50.0, None, 0.8, 1, '시스템'),  # Main
        ('경량배합분말', 'LIGHT-003', '구리분말', 'incoming', 30.0, None, 0.8, 0, '시스템'),
        ('경량배합분말', 'LIGHT-003', '흑연분말', 'incoming', 20.0, None, 0.8, 0, '시스템'),
    ]

    cursor.executemany('''
        INSERT INTO recipe (
            product_name, product_code, powder_name, powder_category,
            ratio, target_weight, tolerance_percent, is_main, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_recipes)

    # 수입검사 샘플 데이터 (각 분말별 2개 LOT, 합격 상태)
    print("\n수입검사 샘플 데이터 생성 중...")
    
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    
    base_date = datetime(2024, 12, 1, 10, 0, 0, tzinfo=ZoneInfo('Asia/Seoul'))
    
    # 검사자, 검사 구분 
    inspectors = ['김철수', '이영희', '박민수']
    inspection_types = ['full_test', 'sampling_test']
    
    # 각 분말별 2개 LOT 검사 데이터 생성
    lot_counter = 1
    inspection_count = 0
    
    for powder_info in [('순철분말', 'incoming'), ('구리분말', 'incoming'), ('흑연분말', 'incoming')]:
        powder_name, category = powder_info
        
        # 각 분말마다 2개 LOT 생성
        for lot_idx in range(2):
            lot_number = f"LOT-{powder_name[:2]}-2024-{lot_counter:03d}"
            lot_counter += 1
            
            inspection_time = base_date + timedelta(days=lot_idx, hours=lot_idx*2)
            
            # 기본적으로 합격(OK)으로 설정된 데이터만 입력
            cursor.execute('''
                INSERT INTO inspection_result (
                    powder_name, lot_number, inspector, inspection_time, inspection_type,
                    flow_rate_1, flow_rate_2, flow_rate_3, flow_rate_avg, flow_rate_result,
                    apparent_density_empty_cup_1, apparent_density_powder_weight_1, apparent_density_1,
                    apparent_density_empty_cup_2, apparent_density_powder_weight_2, apparent_density_2,
                    apparent_density_empty_cup_3, apparent_density_powder_weight_3, apparent_density_3,
                    apparent_density_avg, apparent_density_result,
                    c_content_1, c_content_2, c_content_3, c_content_avg, c_content_result,
                    cu_content_1, cu_content_2, cu_content_3, cu_content_avg, cu_content_result,
                    moisture_initial_weight_1, moisture_dried_weight_1, moisture_1,
                    moisture_initial_weight_2, moisture_dried_weight_2, moisture_2,
                    moisture_initial_weight_3, moisture_dried_weight_3, moisture_3,
                    moisture_avg, moisture_result,
                    ash_initial_weight_1, ash_ash_weight_1, ash_1,
                    ash_initial_weight_2, ash_ash_weight_2, ash_2,
                    ash_initial_weight_3, ash_ash_weight_3, ash_3,
                    ash_avg, ash_result,
                    sinter_change_rate_1, sinter_change_rate_2, sinter_change_rate_3, 
                    sinter_change_rate_avg, sinter_change_rate_result,
                    sinter_strength_1, sinter_strength_2, sinter_strength_3, 
                    sinter_strength_avg, sinter_strength_result,
                    forming_strength_1, forming_strength_2, forming_strength_3, 
                    forming_strength_avg, forming_strength_result,
                    forming_load_1, forming_load_2, forming_load_3, 
                    forming_load_avg, forming_load_result,
                    particle_size_180_1, particle_size_180_2, particle_size_180_avg, particle_size_180_result,
                    particle_size_150_1, particle_size_150_2, particle_size_150_avg, particle_size_150_result,
                    particle_size_106_1, particle_size_106_2, particle_size_106_avg, particle_size_106_result,
                    particle_size_75_1, particle_size_75_2, particle_size_75_avg, particle_size_75_result,
                    particle_size_45_1, particle_size_45_2, particle_size_45_avg, particle_size_45_result,
                    particle_size_45m_1, particle_size_45m_2, particle_size_45m_avg, particle_size_45m_result,
                    particle_size_result, final_result, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                powder_name, lot_number, inspectors[lot_idx % len(inspectors)], inspection_time,
                inspection_types[lot_idx % len(inspection_types)],
                # 유동도
                30.0, 31.0, 30.5, 30.5, 'OK',
                # 겉보기밀도
                2.6, 1.0, 2.6, 2.7, 1.0, 2.7, 2.8, 1.0, 2.8, 2.7, 'OK',
                # C함량
                0.6, 0.65, 0.7, 0.65, 'OK',
                # Cu함량
                0.5, 0.55, 0.6, 0.55, 'OK',
                # 수분도
                0.2, 0.18, 0.2, 0.3, 0.18, 0.3, 0.25, 0.18, 0.25, 0.21, 'OK',
                # 회분도
                0.1, 0.09, 0.1, 0.15, 0.09, 0.15, 0.12, 0.09, 0.12, 0.11, 'OK',
                # 소결변화율
                6.5, 6.8, 7.0, 6.8, 'OK',
                # 소결강도
                900, 920, 910, 910, 'OK',
                # 성형강도
                130, 135, 132, 132, 'OK',
                # 성형하중
                200, 210, 205, 205, 'OK',
                # 입도분석
                5.5, 5.8, 5.65, 'OK',
                10.0, 10.5, 10.25, 'OK',
                15.0, 15.5, 15.25, 'OK',
                18.0, 18.5, 18.25, 'OK',
                17.0, 17.5, 17.25, 'OK',
                15.0, 15.5, 15.25, 'OK',
                'OK', 'OK', category
            ))
            inspection_count += 1

    print(f"수입검사 샘플 데이터 {inspection_count}개 생성 완료")

    conn.commit()
    print("샘플 데이터 입력 완료!")

    # 데이터 확인
    print("\n=== 데이터베이스 초기화 완료 ===")
    cursor.execute("SELECT COUNT(*) FROM powder_spec")
    print(f"분말 사양: {cursor.fetchone()[0]}개")

    cursor.execute("SELECT COUNT(*) FROM particle_size")
    print(f"입도분석 규격: {cursor.fetchone()[0]}개")

    cursor.execute("SELECT COUNT(*) FROM inspector")
    print(f"검사자: {cursor.fetchone()[0]}명")

    cursor.execute("SELECT COUNT(*) FROM operator")
    print(f"작업자: {cursor.fetchone()[0]}명")

    cursor.execute("SELECT COUNT(*) FROM recipe")
    print(f"배합 규격서: {cursor.fetchone()[0]}개")
    
    cursor.execute("SELECT COUNT(*) FROM inspection_result WHERE category = 'incoming'")
    print(f"수입검사 기록: {cursor.fetchone()[0]}개")

    conn.close()
    print("\n데이터베이스 파일: " + db_path)

if __name__ == '__main__':
    init_database()
