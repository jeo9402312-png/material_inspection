"""
분말 검사 시스템 - Flask 서버
Google Apps Script를 대체하는 로컬 웹서버
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import closing

app = Flask(__name__)
CORS(app)

DATABASE = 'database.db'

# ============================================
# 데이터베이스 헬퍼 함수
# ============================================

def get_db():
    """데이터베이스 연결"""
    conn = sqlite3.connect(DATABASE, timeout=30.0)  # 30초 타임아웃
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 반환
    conn.execute('PRAGMA busy_timeout = 30000')  # 30초 대기
    conn.execute('PRAGMA journal_mode = WAL')  # WAL 모드로 동시성 향상
    return conn


def to_kst_str(value, fmt='%Y-%m-%d %H:%M'):
    """주어진 시간 문자열/객체를 KST 문자열로 변환해서 반환합니다.

    - DB에 저장된 시간은 보통 UTC(또는 무표시 naive)로 들어오므로
      이를 UTC로 간주하고 Asia/Seoul로 변환합니다.
    - 파싱 실패 시 원본 값을 그대로 반환합니다.
    """
    if value is None:
        return value

    # 이미 datetime 객체인 경우
    dt = None
    if isinstance(value, datetime):
        dt = value
    else:
        # 문자열 파싱 시도
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            try:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                except Exception:
                    return value

    # naive이면 UTC로 간주
    if dt.tzinfo is None:
        try:
            dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        except Exception:
            # ZoneInfo가 지원되지 않거나 실패 시 기본 처리
            dt = dt

    kst = dt.astimezone(ZoneInfo('Asia/Seoul'))
    return kst.strftime(fmt)


def convert_times_in_dict(d):
    """딕셔너리의 모든 시간 관련 키(키에 'time' 포함)를 KST 문자열로 변환합니다."""
    if not isinstance(d, dict):
        return d
    for k in list(d.keys()):
        if 'time' in k.lower():
            d[k] = to_kst_str(d.get(k))
    return d

def dict_from_row(row):
    """sqlite3.Row를 딕셔너리로 변환"""
    return dict(zip(row.keys(), row))

# ============================================
# 메인 페이지
# ============================================

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

# ============================================
# API: 분말 목록
# ============================================

@app.route('/api/powder-list', methods=['GET'])
def get_powder_list():
    """분말 목록 조회 (category 파라미터로 필터링 가능)"""
    try:
        category = request.args.get('category', None)
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute('SELECT powder_name FROM powder_spec WHERE category = ? ORDER BY powder_name', (category,))
            else:
                cursor.execute('SELECT powder_name FROM powder_spec ORDER BY powder_name')
            powders = [row[0] for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': powders})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 검사자 목록
# ============================================

@app.route('/api/inspector-list', methods=['GET'])
def get_inspector_list():
    """검사자 목록 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM inspector ORDER BY name')
            inspectors = [row[0] for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': inspectors})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 분말 사양 조회
# ============================================

@app.route('/api/powder-spec/<powder_name>', methods=['GET'])
def get_powder_spec(powder_name):
    """분말 사양 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM powder_spec WHERE powder_name = ?', (powder_name,))
            row = cursor.fetchone()
            if row:
                return jsonify({'success': True, 'data': dict_from_row(row)})
            else:
                return jsonify({'success': False, 'message': '분말 사양을 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 입도분석 규격 조회
# ============================================

@app.route('/api/particle-size-spec/<powder_name>', methods=['GET'])
def get_particle_size_spec(powder_name):
    """입도분석 규격 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mesh_size, min_value, max_value
                FROM particle_size
                WHERE powder_name = ?
                ORDER BY id
            ''', (powder_name,))
            specs = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': specs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 검사 항목 필터링
# ============================================

def get_inspection_items(powder_name, inspection_type, conn=None):
    """검사 타입에 따라 필요한 검사 항목 반환

    Args:
        powder_name: 분말명
        inspection_type: 검사 타입
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM powder_spec WHERE powder_name = ?', (powder_name,))
        spec = cursor.fetchone()

        if not spec:
            return []

        spec = dict_from_row(spec)

        # 모든 검사 항목 정의
        all_items = [
            {'name': 'FlowRate', 'displayName': '유동도', 'unit': 's/50g',
             'min': spec['flow_rate_min'], 'max': spec['flow_rate_max'], 'type': spec['flow_rate_type']},

            {'name': 'ApparentDensity', 'displayName': '겉보기밀도', 'unit': 'g/cm³',
             'min': spec['apparent_density_min'], 'max': spec['apparent_density_max'], 'type': spec['apparent_density_type'],
             'isWeightBased': True},

            {'name': 'CContent', 'displayName': 'C함량', 'unit': '%',
             'min': spec['c_content_min'], 'max': spec['c_content_max'], 'type': spec['c_content_type']},

            {'name': 'CuContent', 'displayName': 'Cu함량', 'unit': '%',
             'min': spec['cu_content_min'], 'max': spec['cu_content_max'], 'type': spec['cu_content_type']},

            {'name': 'Moisture', 'displayName': '수분도', 'unit': '%',
             'min': spec['moisture_min'], 'max': spec['moisture_max'], 'type': spec['moisture_type'],
             'isWeightBased': True},

            {'name': 'Ash', 'displayName': '회분도', 'unit': '%',
             'min': spec['ash_min'], 'max': spec['ash_max'], 'type': spec['ash_type'],
             'isWeightBased': True},

            {'name': 'SinterChangeRate', 'displayName': '소결변화율', 'unit': '%',
             'min': spec['sinter_change_rate_min'], 'max': spec['sinter_change_rate_max'], 'type': spec['sinter_change_rate_type']},

            {'name': 'SinterStrength', 'displayName': '소결강도', 'unit': 'MPa',
             'min': spec['sinter_strength_min'], 'max': spec['sinter_strength_max'], 'type': spec['sinter_strength_type']},

            {'name': 'FormingStrength', 'displayName': '성형강도', 'unit': 'N',
             'min': spec['forming_strength_min'], 'max': spec['forming_strength_max'], 'type': spec['forming_strength_type']},

            {'name': 'FormingLoad', 'displayName': '성형하중', 'unit': 'MPa',
             'min': spec['forming_load_min'], 'max': spec['forming_load_max'], 'type': spec['forming_load_type']},
        ]

        # 검사 타입에 따라 필터링
        filtered_items = []
        for item in all_items:
            item_type = item['type']

            # 검사 타입 필터링
            if inspection_type == '일상점검' and item_type == '일상':
                if item['min'] is not None or item['max'] is not None:
                    filtered_items.append(item)
            elif inspection_type == '정기점검' and (item_type == '일상' or item_type == '정기'):
                if item['min'] is not None or item['max'] is not None:
                    filtered_items.append(item)

        # 입도분석 항목 추가
        if spec['particle_size_type']:
            cursor.execute('''
                SELECT mesh_size, min_value, max_value
                FROM particle_size
                WHERE powder_name = ?
            ''', (powder_name,))
            particle_specs = [dict_from_row(row) for row in cursor.fetchall()]

            if particle_specs:
                particle_item_type = spec['particle_size_type']

                if inspection_type == '일상점검' and particle_item_type == '일상':
                    filtered_items.append({
                        'name': 'ParticleSize',
                        'displayName': '입도분석',
                        'unit': '%',
                        'isParticleSize': True,
                        'particleSpecs': particle_specs
                    })
                elif inspection_type == '정기점검' and (particle_item_type == '일상' or particle_item_type == '정기'):
                    filtered_items.append({
                        'name': 'ParticleSize',
                        'displayName': '입도분석',
                        'unit': '%',
                        'isParticleSize': True,
                        'particleSpecs': particle_specs
                    })

        return filtered_items
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

# ============================================
# API: 검사 시작
# ============================================

def _do_start_inspection():
    """검사 시작 또는 기존 검사 이어하기 (내부 구현)"""
    data = request.json
    powder_name = data.get('powderName')
    lot_number = data.get('lotNumber')
    inspection_type = data.get('inspectionType')
    inspector = data.get('inspector')
    category = data.get('category', 'incoming')  # 기본값은 incoming

    if not all([powder_name, lot_number]):
        return jsonify({'success': False, 'message': '필수 입력 항목이 누락되었습니다.'})

    with closing(get_db()) as conn:
        cursor = conn.cursor()

        # 1. 진행중인 검사 확인
        cursor.execute('''
            SELECT * FROM inspection_progress
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        progress_row = cursor.fetchone()

        if progress_row:
            # 기존 진행중 검사가 있음
            progress_data = dict_from_row(progress_row)
            items = get_inspection_items(powder_name, progress_data['inspection_type'], conn)
            return jsonify({
                'success': True,
                'isExisting': True,
                'data': {
                    'powderName': progress_data['powder_name'],
                    'lotNumber': progress_data['lot_number'],
                    'inspectionType': progress_data['inspection_type'],
                    'inspector': progress_data['inspector'],
                    'startTime': to_kst_str(progress_data['start_time']),
                    'completedItems': json.loads(progress_data['completed_items'] or '[]'),
                    'totalItems': json.loads(progress_data['total_items'] or '[]'),
                    'progress': progress_data['progress']
                },
                'items': items
            })

        # 2. 완료된 검사 확인
        cursor.execute('''
            SELECT * FROM inspection_result
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        result_row = cursor.fetchone()

        if result_row:
            return jsonify({
                'success': True,
                'isExisting': True,
                'data': {
                    'powderName': powder_name,
                    'lotNumber': lot_number,
                    'inspectionType': inspection_type,
                    'inspector': inspector,
                    'isCompleted': True,
                    'progress': '완료'
                },
                'items': []
            })

        # 3. 새 검사 시작
        items = get_inspection_items(powder_name, inspection_type, conn)

        if not items:
            return jsonify({'success': False, 'message': '해당 분말의 검사 항목이 없습니다.'})

        item_names = [item['name'] for item in items]

        # 진행중검사 테이블에 추가
        cursor.execute('''
            INSERT INTO inspection_progress
            (powder_name, lot_number, inspection_type, inspector, completed_items, total_items, progress, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (powder_name, lot_number, inspection_type, inspector,
              json.dumps([]), json.dumps(item_names), f'0/{len(item_names)}', category))

        conn.commit()

        return jsonify({
            'success': True,
            'isExisting': False,
            'data': {
                'powderName': powder_name,
                'lotNumber': lot_number,
                'inspectionType': inspection_type,
                'inspector': inspector,
                'completedItems': [],
                'totalItems': item_names
            },
            'items': items
        })


@app.route('/api/start-inspection', methods=['POST'])
def start_inspection():
    """검사 시작 또는 기존 검사 이어하기 (재시도 로직 포함)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            return _do_start_inspection()
        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        return jsonify({'success': False, 'message': str(last_error)})

# ============================================
# API: 미완료 검사 목록
# ============================================

@app.route('/api/incomplete-inspections', methods=['GET'])
def get_incomplete_inspections():
    """진행중인 검사 목록 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inspection_progress ORDER BY start_time DESC')
            inspections = [dict_from_row(row) for row in cursor.fetchall()]

            # JSON 파싱 및 시간(KST) 변환
            for inspection in inspections:
                inspection['completedItems'] = json.loads(inspection['completed_items'] or '[]')
                inspection['totalItems'] = json.loads(inspection['total_items'] or '[]')
                convert_times_in_dict(inspection)

            return jsonify({'success': True, 'data': inspections})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 진행중인 검사 삭제
# ============================================

@app.route('/api/delete-incomplete-inspection/<powder_name>/<lot_number>', methods=['DELETE'])
def delete_incomplete_inspection(powder_name, lot_number):
    """진행중인 검사 삭제"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 진행중인 검사가 있는지 확인
            cursor.execute('''
                SELECT * FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '진행중인 검사를 찾을 수 없습니다.'})

            # 진행중인 검사만 삭제 (완료된 검사는 삭제하지 않음)
            cursor.execute('''
                DELETE FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            conn.commit()

            return jsonify({'success': True, 'message': '진행중인 검사가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 검사 항목 저장
# ============================================

@app.route('/api/save-item', methods=['POST'])
def save_inspection_item():
    """검사 항목 저장 (단일 트랜잭션으로 통합)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            data = request.json
            powder_name = data.get('powderName')
            lot_number = data.get('lotNumber')
            item_name = data.get('itemName')
            values = data.get('values')

            print(f"저장 요청: {powder_name}, {lot_number}, {item_name}, {values}")

            # 특수 항목 처리
            if item_name == 'ApparentDensity':
                return save_apparent_density(powder_name, lot_number, values)
            elif item_name == 'Moisture':
                return save_moisture(powder_name, lot_number, values)
            elif item_name == 'Ash':
                return save_ash(powder_name, lot_number, values)

            # 일반 항목 처리
            valid_values = [float(v) for v in values if v != '' and v is not None]

            if not valid_values:
                return jsonify({'success': False, 'message': '유효한 측정값이 없습니다.'})

            average = sum(valid_values) / len(valid_values)
            average = round(average, 2)

            # 단일 트랜잭션으로 모든 작업 수행
            with closing(get_db()) as conn:
                # 규격 확인
                result = check_spec(powder_name, lot_number, item_name, average, conn)

                # 데이터 저장
                _do_save_to_result_table(powder_name, lot_number, item_name, values, average, result, conn)

                # 진행 상태 업데이트
                _do_update_progress(powder_name, lot_number, item_name, conn)

                # 모든 작업 성공 시 커밋
                conn.commit()

            return jsonify({'success': True, 'average': f'{average:.2f}', 'result': result})

        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                print(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                print(f"오류: {str(e)}")
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        print(f"최종 오류: {str(last_error)}")
        return jsonify({'success': False, 'message': str(last_error)})

# ============================================
# API: 입도분석 저장
# ============================================

@app.route('/api/save-particle-size', methods=['POST'])
def save_particle_size():
    """입도분석 데이터 저장 (단일 트랜잭션으로 통합)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            data = request.json
            powder_name = data.get('powderName')
            lot_number = data.get('lotNumber')
            particle_data = data.get('particleData') or {}

            # DB에 정의된 모든 입도 규격을 조회하여, 모든 항목이 측정되어 있고
            # 규격 내에 있는지 확인해야 전체 PASS가 된다.
            with closing(get_db()) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT mesh_size, min_value, max_value FROM particle_size WHERE powder_name = ? ORDER BY id', (powder_name,))
                specs = [dict_from_row(r) for r in cursor.fetchall()]

            overall_result = 'PASS'

            # 프론트엔드와의 키 매핑(인덱스 기반) - 기본 매핑 (index 0..5)
            mesh_ids = ['180', '150', '106', '75', '45', '45M']

            # 각 규격에 대해 측정값 존재 및 규격 만족 여부 확인
            for idx, spec in enumerate(specs):
                key = mesh_ids[idx] if idx < len(mesh_ids) else spec.get('mesh_size')
                entry = particle_data.get(key)

                if not entry:
                    # 측정값 누락 -> 불합격 처리
                    overall_result = 'FAIL'
                    particle_data[key] = {'val1': None, 'val2': None, 'avg': None, 'result': '불합격'}
                    continue

                avg = entry.get('avg')
                try:
                    if avg is None:
                        entry['result'] = '불합격'
                        overall_result = 'FAIL'
                    else:
                        avg_val = float(avg)
                        min_v = spec.get('min_value')
                        max_v = spec.get('max_value')
                        if (min_v is not None and avg_val < min_v) or (max_v is not None and avg_val > max_v):
                            entry['result'] = '불합격'
                            overall_result = 'FAIL'
                        else:
                            entry['result'] = '합격'
                except Exception:
                    entry['result'] = '불합격'
                    overall_result = 'FAIL'

            # 만약 DB에 규격이 하나도 없다면 기존 방식대로 전달된 데이터만으로 불합격 여부 확인
            if not specs:
                for mesh_id, mesh_data in particle_data.items():
                    if mesh_data.get('result') == '불합격':
                        overall_result = 'FAIL'

            # 단일 트랜잭션으로 모든 작업 수행
            with closing(get_db()) as conn:
                # 데이터 저장
                _do_save_particle_to_result_table(powder_name, lot_number, particle_data, overall_result, conn)

                # 진행 상태 업데이트
                _do_update_progress(powder_name, lot_number, 'ParticleSize', conn)

                # 모든 작업 성공 시 커밋
                conn.commit()

            return jsonify({'success': True, 'result': overall_result})

        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                print(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        return jsonify({'success': False, 'message': str(last_error)})

# ============================================
# API: 검사 결과 조회
# ============================================

@app.route('/api/search-results', methods=['GET'])
def search_inspection_results():
    """검사 결과 조회 (category, dateFrom, dateTo로 필터링 가능)"""
    try:
        category = request.args.get('category', '')
        powder_name = request.args.get('powderName', '')
        lot_number = request.args.get('lotNumber', '')
        date_from = request.args.get('dateFrom', '')
        date_to = request.args.get('dateTo', '')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM inspection_result WHERE 1=1'
            params = []

            if category:
                query += ' AND category = ?'
                params.append(category)

            if powder_name:
                query += ' AND powder_name = ?'
                params.append(powder_name)

            if lot_number:
                query += ' AND lot_number = ?'
                params.append(lot_number)

            if date_from:
                query += ' AND inspection_time >= ?'
                params.append(date_from + ' 00:00:00')

            if date_to:
                query += ' AND inspection_time <= ?'
                params.append(date_to + ' 23:59:59')

            query += ' ORDER BY inspection_time DESC'

            cursor.execute(query, params)
            results = [dict_from_row(row) for row in cursor.fetchall()]

            # 완료된 검사만 필터링
            results = [r for r in results if r['final_result'] in ['PASS', 'FAIL']]

            # 시간 필드 KST 변환
            for r in results:
                convert_times_in_dict(r)

            return jsonify({'success': True, 'data': results})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 검사 상세 조회
# ============================================

@app.route('/api/inspection-detail/<powder_name>/<lot_number>', methods=['GET'])
def get_inspection_detail(powder_name, lot_number):
    """검사 상세 정보 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM inspection_result
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            row = cursor.fetchone()

            if not row:
                return jsonify({'success': False, 'message': '검사 결과를 찾을 수 없습니다.'})

            result = dict_from_row(row)

            # 분말 사양 추가
            cursor.execute('SELECT * FROM powder_spec WHERE powder_name = ?', (powder_name,))
            spec_row = cursor.fetchone()
            if spec_row:
                result['powderSpec'] = dict_from_row(spec_row)

            # 입도분석 규격 추가
            cursor.execute('''
                SELECT mesh_size, min_value, max_value
                FROM particle_size
                WHERE powder_name = ?
            ''', (powder_name,))
            particle_specs = [dict_from_row(r) for r in cursor.fetchall()]
            if particle_specs:
                result['particleSizeSpecs'] = particle_specs

            # 시간 필드 KST 변환
            convert_times_in_dict(result)

            return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 검사 삭제
# ============================================

@app.route('/api/delete-inspection', methods=['POST'])
def delete_inspection():
    """검사 결과 삭제"""
    try:
        data = request.json
        powder_name = data.get('powderName')
        lot_number = data.get('lotNumber')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 검사 결과 삭제
            cursor.execute('''
                DELETE FROM inspection_result
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            # 진행중 검사 삭제
            cursor.execute('''
                DELETE FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            conn.commit()

            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# 헬퍼 함수들
# ============================================

def save_apparent_density(powder_name, lot_number, values):
    """겉보기밀도 저장 (단일 트랜잭션으로 통합)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            # values: [emptyCup1, powderWeight1, emptyCup2, powderWeight2, emptyCup3, powderWeight3]
            densities = []
            for i in range(3):
                empty_cup = values[i * 2]
                powder_weight = values[i * 2 + 1]
                if empty_cup and powder_weight:
                    density = (float(powder_weight) - float(empty_cup)) / 25
                    densities.append(density)

            if not densities:
                return jsonify({'success': False, 'message': '유효한 측정값이 없습니다.'})

            average = round(sum(densities) / len(densities), 2)

            # 단일 트랜잭션으로 모든 작업 수행
            with closing(get_db()) as conn:
                result = check_spec(powder_name, lot_number, 'ApparentDensity', average, conn)
                _do_save_to_result_table(powder_name, lot_number, 'ApparentDensity', values, average, result, conn)
                _do_update_progress(powder_name, lot_number, 'ApparentDensity', conn)
                conn.commit()

            return jsonify({'success': True, 'average': f'{average:.2f}', 'result': result})

        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                print(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        return jsonify({'success': False, 'message': str(last_error)})

def save_moisture(powder_name, lot_number, values):
    """수분도 저장 (단일 트랜잭션으로 통합)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            # values: [initialWeight1, driedWeight1, initialWeight2, driedWeight2, initialWeight3, driedWeight3]
            moisture_values = []
            for i in range(3):
                initial = values[i * 2]
                dried = values[i * 2 + 1]
                if initial and dried:
                    moisture = ((float(initial) - float(dried)) / float(initial)) * 100
                    moisture_values.append(moisture)

            if not moisture_values:
                return jsonify({'success': False, 'message': '유효한 측정값이 없습니다.'})

            average = round(sum(moisture_values) / len(moisture_values), 2)

            # 단일 트랜잭션으로 모든 작업 수행
            with closing(get_db()) as conn:
                result = check_spec(powder_name, lot_number, 'Moisture', average, conn)
                _do_save_to_result_table(powder_name, lot_number, 'Moisture', values, average, result, conn)
                _do_update_progress(powder_name, lot_number, 'Moisture', conn)
                conn.commit()

            return jsonify({'success': True, 'average': f'{average:.2f}', 'result': result})

        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                print(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        return jsonify({'success': False, 'message': str(last_error)})

def save_ash(powder_name, lot_number, values):
    """회분도 저장 (단일 트랜잭션으로 통합)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            # values: [initialWeight1, ashWeight1, initialWeight2, ashWeight2, initialWeight3, ashWeight3]
            ash_values = []
            for i in range(3):
                initial = values[i * 2]
                ash = values[i * 2 + 1]
                if initial and ash:
                    ash_percent = ((float(initial) - float(ash)) / float(initial)) * 100
                    ash_values.append(ash_percent)

            if not ash_values:
                return jsonify({'success': False, 'message': '유효한 측정값이 없습니다.'})

            average = round(sum(ash_values) / len(ash_values), 2)

            # 단일 트랜잭션으로 모든 작업 수행
            with closing(get_db()) as conn:
                result = check_spec(powder_name, lot_number, 'Ash', average, conn)
                _do_save_to_result_table(powder_name, lot_number, 'Ash', values, average, result, conn)
                _do_update_progress(powder_name, lot_number, 'Ash', conn)
                conn.commit()

            return jsonify({'success': True, 'average': f'{average:.2f}', 'result': result})

        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                print(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return jsonify({'success': False, 'message': str(e)})

    if last_error:
        return jsonify({'success': False, 'message': str(last_error)})

def check_spec(powder_name, lot_number, item_name, average, conn=None):
    """규격 확인하여 PASS/FAIL 판정

    Args:
        powder_name: 분말명
        lot_number: LOT번호
        item_name: 검사 항목명
        average: 평균값
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()

        # 검사 타입 확인
        cursor.execute('''
            SELECT inspection_type FROM inspection_progress
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        progress_row = cursor.fetchone()

        if not progress_row:
            cursor.execute('''
                SELECT inspection_type FROM inspection_result
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))
            progress_row = cursor.fetchone()

        if not progress_row:
            return 'PASS'

        inspection_type = progress_row[0]
        items = get_inspection_items(powder_name, inspection_type, conn)

        for item in items:
            if item['name'] == item_name:
                min_val = item.get('min')
                max_val = item.get('max')

                if min_val is not None and average < min_val:
                    return 'FAIL'
                if max_val is not None and average > max_val:
                    return 'FAIL'

        return 'PASS'
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

def save_to_result_table(powder_name, lot_number, item_name, values, average, result):
    """검사 결과 테이블에 저장 (재시도 로직 포함)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            _do_save_to_result_table(powder_name, lot_number, item_name, values, average, result)
            return  # 성공하면 즉시 반환
        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                time.sleep(retry_delay * (2 ** attempt))  # 지수 백오프
                continue
            else:
                raise  # 다른 오류거나 마지막 시도이면 그대로 throw

    # 모든 재시도 실패
    if last_error:
        raise last_error

def _do_save_to_result_table(powder_name, lot_number, item_name, values, average, result, conn=None):
    """실제 저장 로직

    Args:
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()

        # 기존 행 확인
        cursor.execute('''
            SELECT id FROM inspection_result
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        existing = cursor.fetchone()

        # 컬럼명 매핑
        column_map = {
            'FlowRate': ['flow_rate_1', 'flow_rate_2', 'flow_rate_3', 'flow_rate_avg', 'flow_rate_result'],
            'ApparentDensity': [
                'apparent_density_empty_cup_1', 'apparent_density_powder_weight_1', 'apparent_density_1',
                'apparent_density_empty_cup_2', 'apparent_density_powder_weight_2', 'apparent_density_2',
                'apparent_density_empty_cup_3', 'apparent_density_powder_weight_3', 'apparent_density_3',
                'apparent_density_avg', 'apparent_density_result'
            ],
            'CContent': ['c_content_1', 'c_content_2', 'c_content_3', 'c_content_avg', 'c_content_result'],
            'CuContent': ['cu_content_1', 'cu_content_2', 'cu_content_3', 'cu_content_avg', 'cu_content_result'],
            'Moisture': [
                'moisture_initial_weight_1', 'moisture_dried_weight_1', 'moisture_1',
                'moisture_initial_weight_2', 'moisture_dried_weight_2', 'moisture_2',
                'moisture_initial_weight_3', 'moisture_dried_weight_3', 'moisture_3',
                'moisture_avg', 'moisture_result'
            ],
            'Ash': [
                'ash_initial_weight_1', 'ash_ash_weight_1', 'ash_1',
                'ash_initial_weight_2', 'ash_ash_weight_2', 'ash_2',
                'ash_initial_weight_3', 'ash_ash_weight_3', 'ash_3',
                'ash_avg', 'ash_result'
            ],
            'SinterChangeRate': ['sinter_change_rate_1', 'sinter_change_rate_2', 'sinter_change_rate_3', 'sinter_change_rate_avg', 'sinter_change_rate_result'],
            'SinterStrength': ['sinter_strength_1', 'sinter_strength_2', 'sinter_strength_3', 'sinter_strength_avg', 'sinter_strength_result'],
            'FormingStrength': ['forming_strength_1', 'forming_strength_2', 'forming_strength_3', 'forming_strength_avg', 'forming_strength_result'],
            'FormingLoad': ['forming_load_1', 'forming_load_2', 'forming_load_3', 'forming_load_avg', 'forming_load_result']
        }

        if existing:
            # 기존 행 업데이트
            columns = column_map.get(item_name, [])

            if item_name in ['ApparentDensity', 'Moisture', 'Ash']:
                # 특수 항목 (계산값 포함)
                update_special_item(cursor, existing[0], item_name, columns, values, average, result)
            else:
                # 일반 항목
                update_parts = []
                update_values = []

                if len(values) >= 1 and values[0]:
                    update_parts.append(f'{columns[0]} = ?')
                    update_values.append(float(values[0]))
                if len(values) >= 2 and values[1]:
                    update_parts.append(f'{columns[1]} = ?')
                    update_values.append(float(values[1]))
                if len(values) >= 3 and values[2]:
                    update_parts.append(f'{columns[2]} = ?')
                    update_values.append(float(values[2]))

                update_parts.append(f'{columns[3]} = ?')
                update_values.append(average)

                update_parts.append(f'{columns[4]} = ?')
                update_values.append(result)

                update_values.append(existing[0])

                query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
                cursor.execute(query, update_values)

        else:
            # 새 행 생성
            cursor.execute('''
                SELECT inspection_type, inspector FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))
            progress_data = cursor.fetchone()

            inspection_type = progress_data[0] if progress_data else '일상점검'
            inspector = progress_data[1] if progress_data else '미지정'

            cursor.execute('''
                INSERT INTO inspection_result (powder_name, lot_number, inspection_type, inspector)
                VALUES (?, ?, ?, ?)
            ''', (powder_name, lot_number, inspection_type, inspector))

            new_id = cursor.lastrowid

            # 방금 생성한 행에 데이터 업데이트
            columns = column_map.get(item_name, [])

            if item_name in ['ApparentDensity', 'Moisture', 'Ash']:
                update_special_item(cursor, new_id, item_name, columns, values, average, result)
            else:
                update_parts = []
                update_values = []

                if len(values) >= 1 and values[0]:
                    update_parts.append(f'{columns[0]} = ?')
                    update_values.append(float(values[0]))
                if len(values) >= 2 and values[1]:
                    update_parts.append(f'{columns[1]} = ?')
                    update_values.append(float(values[1]))
                if len(values) >= 3 and values[2]:
                    update_parts.append(f'{columns[2]} = ?')
                    update_values.append(float(values[2]))

                update_parts.append(f'{columns[3]} = ?')
                update_values.append(average)

                update_parts.append(f'{columns[4]} = ?')
                update_values.append(result)

                update_values.append(new_id)

                query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
                cursor.execute(query, update_values)

        # 연결을 직접 생성한 경우에만 커밋
        if owns_connection:
            conn.commit()
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

def update_special_item(cursor, row_id, item_name, columns, values, average, result):
    """특수 항목 (겉보기밀도, 수분도, 회분도) 업데이트"""

    if item_name == 'ApparentDensity':
        # 겉보기밀도: 원본 데이터 + 계산값 저장
        update_parts = []
        update_values = []

        for i in range(3):
            empty_cup = values[i * 2] if i * 2 < len(values) else None
            powder_weight = values[i * 2 + 1] if i * 2 + 1 < len(values) else None

            if empty_cup:
                update_parts.append(f'{columns[i * 3]} = ?')
                update_values.append(float(empty_cup))

            if powder_weight:
                update_parts.append(f'{columns[i * 3 + 1]} = ?')
                update_values.append(float(powder_weight))

            if empty_cup and powder_weight:
                density = (float(powder_weight) - float(empty_cup)) / 25
                update_parts.append(f'{columns[i * 3 + 2]} = ?')
                update_values.append(round(density, 2))

        update_parts.append(f'{columns[9]} = ?')
        update_values.append(average)

        update_parts.append(f'{columns[10]} = ?')
        update_values.append(result)

        update_values.append(row_id)

        query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
        cursor.execute(query, update_values)

    elif item_name in ['Moisture', 'Ash']:
        # 수분도/회분도: 원본 데이터 + 계산값 저장
        update_parts = []
        update_values = []

        for i in range(3):
            val1 = values[i * 2] if i * 2 < len(values) else None
            val2 = values[i * 2 + 1] if i * 2 + 1 < len(values) else None

            if val1:
                update_parts.append(f'{columns[i * 3]} = ?')
                update_values.append(float(val1))

            if val2:
                update_parts.append(f'{columns[i * 3 + 1]} = ?')
                update_values.append(float(val2))

            if val1 and val2:
                if item_name == 'Moisture':
                    calc_val = ((float(val1) - float(val2)) / float(val1)) * 100
                else:  # Ash
                    calc_val = (float(val2) / float(val1)) * 100

                update_parts.append(f'{columns[i * 3 + 2]} = ?')
                update_values.append(round(calc_val, 2))

        update_parts.append(f'{columns[9]} = ?')
        update_values.append(average)

        update_parts.append(f'{columns[10]} = ?')
        update_values.append(result)

        update_values.append(row_id)

        query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
        cursor.execute(query, update_values)

def save_particle_to_result_table(powder_name, lot_number, particle_data, overall_result):
    """입도분석 결과 저장 (재시도 로직 포함)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            _do_save_particle_to_result_table(powder_name, lot_number, particle_data, overall_result)
            return  # 성공하면 즉시 반환
        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                time.sleep(retry_delay * (2 ** attempt))  # 지수 백오프
                continue
            else:
                raise  # 다른 오류거나 마지막 시도이면 그대로 throw

    # 모든 재시도 실패
    if last_error:
        raise last_error

def _do_save_particle_to_result_table(powder_name, lot_number, particle_data, overall_result, conn=None):
    """실제 입도분석 저장 로직

    Args:
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()

        # 기존 행 확인
        cursor.execute('''
            SELECT id FROM inspection_result
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        existing = cursor.fetchone()

        mesh_mapping = {
            '180': 'particle_size_180',
            '150': 'particle_size_150',
            '106': 'particle_size_106',
            '75': 'particle_size_75',
            '45': 'particle_size_45',
            '45M': 'particle_size_45m'
        }

        update_parts = []
        update_values = []

        for mesh_id, prefix in mesh_mapping.items():
            data = particle_data.get(mesh_id)

            # Only update columns for meshes that were actually provided in the payload.
            # This prevents overwriting existing DB values with FAIL when the client
            # omitted a mesh key unintentionally.
            if not data:
                continue

            val1 = data.get('val1')
            val2 = data.get('val2')
            avg = data.get('avg')
            mesh_result = 'PASS' if data.get('result') == '합격' else 'FAIL'

            if val1 is not None and val1 != '':
                update_parts.append(f'{prefix}_1 = ?')
                update_values.append(float(val1))
            if val2 is not None and val2 != '':
                update_parts.append(f'{prefix}_2 = ?')
                update_values.append(float(val2))
            # avg may be '0' or '0.0' string; check against None and empty string
            if avg is not None and avg != '':
                try:
                    update_parts.append(f'{prefix}_avg = ?')
                    update_values.append(float(avg))
                except Exception:
                    # if parsing fails, skip avg
                    pass

            update_parts.append(f'{prefix}_result = ?')
            update_values.append(mesh_result)

        update_parts.append('particle_size_result = ?')
        update_values.append(overall_result)

        if existing:
            update_values.append(existing[0])
            query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
            cursor.execute(query, update_values)
        else:
            cursor.execute('''
                SELECT inspection_type, inspector FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))
            progress_data = cursor.fetchone()

            inspection_type = progress_data[0] if progress_data else '일상점검'
            inspector = progress_data[1] if progress_data else '미지정'

            cursor.execute('''
                INSERT INTO inspection_result (powder_name, lot_number, inspection_type, inspector)
                VALUES (?, ?, ?, ?)
            ''', (powder_name, lot_number, inspection_type, inspector))

            new_id = cursor.lastrowid
            update_values.append(new_id)

            query = f"UPDATE inspection_result SET {', '.join(update_parts)} WHERE id = ?"
            cursor.execute(query, update_values)

        # 연결을 직접 생성한 경우에만 커밋
        if owns_connection:
            conn.commit()
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

def update_progress(powder_name, lot_number, item_name):
    """진행중 검사 업데이트 (재시도 로직 포함)"""
    import time
    max_retries = 5
    retry_delay = 0.05  # 50ms

    last_error = None
    for attempt in range(max_retries):
        try:
            _do_update_progress(powder_name, lot_number, item_name)
            return
        except Exception as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                last_error = e
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                raise

    if last_error:
        raise last_error

def _do_update_progress(powder_name, lot_number, item_name, conn=None):
    """실제 진행 업데이트 로직

    Args:
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT completed_items, total_items FROM inspection_progress
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        progress_row = cursor.fetchone()

        if not progress_row:
            # 완료된 검사인 경우 최종 결과만 업데이트
            update_final_result(powder_name, lot_number, conn)
            return

        completed_items = json.loads(progress_row[0] or '[]')
        total_items = json.loads(progress_row[1] or '[]')

        if item_name not in completed_items:
            completed_items.append(item_name)

        progress = f'{len(completed_items)}/{len(total_items)}'

        cursor.execute('''
            UPDATE inspection_progress
            SET completed_items = ?, progress = ?
            WHERE powder_name = ? AND lot_number = ?
        ''', (json.dumps(completed_items), progress, powder_name, lot_number))

        # 모든 항목 완료 시 진행중 검사에서 제거
        if len(completed_items) == len(total_items):
            cursor.execute('''
                DELETE FROM inspection_progress
                WHERE powder_name = ? AND lot_number = ?
            ''', (powder_name, lot_number))

            update_final_result(powder_name, lot_number, conn)

        # 연결을 직접 생성한 경우에만 커밋
        if owns_connection:
            conn.commit()
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

def update_final_result(powder_name, lot_number, conn=None):
    """최종 결과 업데이트

    Args:
        powder_name: 분말명
        lot_number: LOT번호
        conn: 기존 DB 연결 (없으면 새로 생성)
    """
    # 연결이 제공되지 않은 경우 새로 생성
    owns_connection = conn is None
    if owns_connection:
        conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM inspection_result
            WHERE powder_name = ? AND lot_number = ?
        ''', (powder_name, lot_number))
        result_row = cursor.fetchone()

        if not result_row:
            return

        result_data = dict_from_row(result_row)

        # 모든 _result 컬럼 확인
        final_result = 'PASS'
        for key, value in result_data.items():
            if key.endswith('_result') and key != 'final_result':
                if value == 'FAIL':
                    final_result = 'FAIL'
                    break

        cursor.execute('''
            UPDATE inspection_result
            SET final_result = ?
            WHERE powder_name = ? AND lot_number = ?
        ''', (final_result, powder_name, lot_number))

        # 연결을 직접 생성한 경우에만 커밋
        if owns_connection:
            conn.commit()
    finally:
        # 직접 생성한 연결만 닫기
        if owns_connection:
            conn.close()

# ============================================
# 관리자 API
# ============================================

# --------------------------------------------
# 분말 목록 조회 (카테고리별)
# --------------------------------------------

@app.route('/api/powders', methods=['GET'])
def get_powders_by_category():
    """카테고리별 분말 목록 조회"""
    try:
        category = request.args.get('category')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            if category:
                cursor.execute('SELECT powder_name, category FROM powder_spec WHERE category = ? ORDER BY powder_name', (category,))
            else:
                cursor.execute('SELECT powder_name, category FROM powder_spec ORDER BY powder_name')

            powders = [{'powder_name': row[0], 'category': row[1]} for row in cursor.fetchall()]
            return jsonify({'success': True, 'powders': powders})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --------------------------------------------
# 분말 사양 관리
# --------------------------------------------

@app.route('/api/admin/powder-spec', methods=['GET'])
def admin_get_all_powder_specs():
    """모든 분말 사양 조회 (관리자용)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM powder_spec ORDER BY powder_name')
            specs = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': specs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/powder-spec', methods=['POST'])
def admin_add_powder_spec():
    """분말 사양 추가"""
    try:
        data = request.json

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 중복 확인
            cursor.execute('SELECT id FROM powder_spec WHERE powder_name = ?', (data['powder_name'],))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 분말명입니다.'})

            # 삽입
            cursor.execute('''
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
            ''', (
                data.get('powder_name'),
                data.get('flow_rate_min'), data.get('flow_rate_max'), data.get('flow_rate_type'),
                data.get('apparent_density_min'), data.get('apparent_density_max'), data.get('apparent_density_type'),
                data.get('c_content_min'), data.get('c_content_max'), data.get('c_content_type'),
                data.get('cu_content_min'), data.get('cu_content_max'), data.get('cu_content_type'),
                data.get('moisture_min'), data.get('moisture_max'), data.get('moisture_type'),
                data.get('ash_min'), data.get('ash_max'), data.get('ash_type'),
                data.get('sinter_change_rate_min'), data.get('sinter_change_rate_max'), data.get('sinter_change_rate_type'),
                data.get('sinter_strength_min'), data.get('sinter_strength_max'), data.get('sinter_strength_type'),
                data.get('forming_strength_min'), data.get('forming_strength_max'), data.get('forming_strength_type'),
                data.get('forming_load_min'), data.get('forming_load_max'), data.get('forming_load_type'),
                data.get('particle_size_type'),
                data.get('category', 'incoming')
            ))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/powder-spec/<int:spec_id>', methods=['PUT'])
def admin_update_powder_spec(spec_id):
    """분말 사양 수정"""
    try:
        data = request.json

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE powder_spec SET
                    powder_name = ?,
                    flow_rate_min = ?, flow_rate_max = ?, flow_rate_type = ?,
                    apparent_density_min = ?, apparent_density_max = ?, apparent_density_type = ?,
                    c_content_min = ?, c_content_max = ?, c_content_type = ?,
                    cu_content_min = ?, cu_content_max = ?, cu_content_type = ?,
                    moisture_min = ?, moisture_max = ?, moisture_type = ?,
                    ash_min = ?, ash_max = ?, ash_type = ?,
                    sinter_change_rate_min = ?, sinter_change_rate_max = ?, sinter_change_rate_type = ?,
                    sinter_strength_min = ?, sinter_strength_max = ?, sinter_strength_type = ?,
                    forming_strength_min = ?, forming_strength_max = ?, forming_strength_type = ?,
                    forming_load_min = ?, forming_load_max = ?, forming_load_type = ?,
                    particle_size_type = ?,
                    category = ?
                WHERE id = ?
            ''', (
                data.get('powder_name'),
                data.get('flow_rate_min'), data.get('flow_rate_max'), data.get('flow_rate_type'),
                data.get('apparent_density_min'), data.get('apparent_density_max'), data.get('apparent_density_type'),
                data.get('c_content_min'), data.get('c_content_max'), data.get('c_content_type'),
                data.get('cu_content_min'), data.get('cu_content_max'), data.get('cu_content_type'),
                data.get('moisture_min'), data.get('moisture_max'), data.get('moisture_type'),
                data.get('ash_min'), data.get('ash_max'), data.get('ash_type'),
                data.get('sinter_change_rate_min'), data.get('sinter_change_rate_max'), data.get('sinter_change_rate_type'),
                data.get('sinter_strength_min'), data.get('sinter_strength_max'), data.get('sinter_strength_type'),
                data.get('forming_strength_min'), data.get('forming_strength_max'), data.get('forming_strength_type'),
                data.get('forming_load_min'), data.get('forming_load_max'), data.get('forming_load_type'),
                data.get('particle_size_type'),
                data.get('category', 'incoming'),
                spec_id
            ))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/powder-spec/<int:spec_id>', methods=['DELETE'])
def admin_delete_powder_spec(spec_id):
    """분말 사양 삭제"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM powder_spec WHERE id = ?', (spec_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --------------------------------------------
# 입도분석 규격 관리
# --------------------------------------------

@app.route('/api/admin/particle-size', methods=['GET'])
def admin_get_all_particle_sizes():
    """모든 입도분석 규격 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM particle_size ORDER BY powder_name, id')
            specs = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': specs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/particle-size/<powder_name>', methods=['GET'])
def admin_get_particle_size_by_powder(powder_name):
    """특정 분말의 입도분석 규격 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM particle_size WHERE powder_name = ? ORDER BY id', (powder_name,))
            specs = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': specs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/particle-size', methods=['POST'])
def admin_add_particle_size():
    """입도분석 규격 추가"""
    try:
        data = request.json

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 중복 확인
            cursor.execute('''
                SELECT id FROM particle_size
                WHERE powder_name = ? AND mesh_size = ?
            ''', (data['powder_name'], data['mesh_size']))

            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 규격입니다.'})

            cursor.execute('''
                INSERT INTO particle_size (powder_name, mesh_size, min_value, max_value)
                VALUES (?, ?, ?, ?)
            ''', (data['powder_name'], data['mesh_size'], data['min_value'], data['max_value']))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/particle-size/<int:spec_id>', methods=['PUT'])
def admin_update_particle_size(spec_id):
    """입도분석 규격 수정"""
    try:
        data = request.json

        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE particle_size SET
                    powder_name = ?, mesh_size = ?, min_value = ?, max_value = ?
                WHERE id = ?
            ''', (data['powder_name'], data['mesh_size'], data['min_value'], data['max_value'], spec_id))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/particle-size/<int:spec_id>', methods=['DELETE'])
def admin_delete_particle_size(spec_id):
    """입도분석 규격 삭제"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM particle_size WHERE id = ?', (spec_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/particle-size/bulk', methods=['POST'])
def admin_bulk_save_particle_size():
    """입도분석 규격 일괄 저장"""
    try:
        data = request.json
        powder_name = data.get('powder_name')
        specs = data.get('specs', [])

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 기존 입도분석 규격 삭제
            cursor.execute('DELETE FROM particle_size WHERE powder_name = ?', (powder_name,))

            # 새 규격 추가
            for spec in specs:
                cursor.execute('''
                    INSERT INTO particle_size (powder_name, mesh_size, min_value, max_value)
                    VALUES (?, ?, ?, ?)
                ''', (spec['powder_name'], spec['mesh_size'], spec['min_value'], spec['max_value']))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --------------------------------------------
# 검사자 관리
# --------------------------------------------

@app.route('/api/admin/inspector', methods=['GET'])
def admin_get_all_inspectors():
    """모든 검사자 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inspector ORDER BY name')
            inspectors = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': inspectors})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/inspector', methods=['POST'])
def admin_add_inspector():
    """검사자 추가"""
    try:
        data = request.json
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'success': False, 'message': '검사자 이름을 입력하세요.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 중복 확인
            cursor.execute('SELECT id FROM inspector WHERE name = ?', (name,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 검사자입니다.'})

            cursor.execute('INSERT INTO inspector (name) VALUES (?)', (name,))
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/inspector/<int:inspector_id>', methods=['DELETE'])
def admin_delete_inspector(inspector_id):
    """검사자 삭제"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM inspector WHERE id = ?', (inspector_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 작업자 관리 (Operator Management)
# ============================================

@app.route('/api/operator-list', methods=['GET'])
def get_operator_list():
    """작업자 목록 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM operator ORDER BY name')
            operators = [row[0] for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': operators})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/operator', methods=['GET'])
def admin_get_all_operators():
    """모든 작업자 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM operator ORDER BY name')
            operators = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify({'success': True, 'data': operators})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/operator', methods=['POST'])
def admin_add_operator():
    """작업자 추가"""
    try:
        data = request.json
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'success': False, 'message': '작업자 이름을 입력하세요.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 중복 확인
            cursor.execute('SELECT id FROM operator WHERE name = ?', (name,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 작업자입니다.'})

            cursor.execute('INSERT INTO operator (name) VALUES (?)', (name,))
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/operator/<int:operator_id>', methods=['DELETE'])
def admin_delete_operator(operator_id):
    """작업자 삭제"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM operator WHERE id = ?', (operator_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: Recipe(배합 규격서) 관리
# ============================================

@app.route('/api/admin/recipes', methods=['GET'])
def admin_get_recipes():
    """Recipe 목록 조회 (제품별 그룹핑)"""
    try:
        product_name = request.args.get('product_name', None)

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            if product_name:
                # 특정 제품의 Recipe만 조회
                cursor.execute('''
                    SELECT * FROM recipe
                    WHERE product_name = ? AND is_active = 1
                    ORDER BY id
                ''', (product_name,))
            else:
                # 모든 Recipe 조회
                cursor.execute('''
                    SELECT * FROM recipe
                    WHERE is_active = 1
                    ORDER BY product_name, id
                ''')

            recipes = [dict_from_row(row) for row in cursor.fetchall()]

            # 제품별 그룹핑
            products = {}
            for recipe in recipes:
                pname = recipe['product_name']
                if pname not in products:
                    products[pname] = {
                        'product_name': pname,
                        'product_code': recipe['product_code'],
                        'recipes': []
                    }
                products[pname]['recipes'].append(recipe)

            return jsonify({
                'success': True,
                'data': list(products.values()),
                'total_products': len(products),
                'total_recipes': len(recipes)
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/recipe', methods=['POST'])
def admin_add_recipe():
    """Recipe 추가"""
    try:
        data = request.json

        required_fields = ['product_name', 'powder_name', 'ratio']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '필수 항목이 누락되었습니다.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO recipe (
                    product_name, product_code, powder_name, powder_category,
                    ratio, target_weight, tolerance_percent, is_main, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['product_name'],
                data.get('product_code', ''),
                data['powder_name'],
                data.get('powder_category', 'incoming'),
                data['ratio'],
                data.get('target_weight', None),
                data.get('tolerance_percent', 5.0),
                1 if data.get('is_main', False) else 0,
                data.get('created_by', '관리자')
            ))

            conn.commit()
            return jsonify({'success': True, 'recipe_id': cursor.lastrowid})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/recipe/<int:recipe_id>', methods=['PUT'])
def admin_update_recipe(recipe_id):
    """Recipe 수정"""
    try:
        data = request.json

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE recipe SET
                    product_name = ?,
                    product_code = ?,
                    powder_name = ?,
                    powder_category = ?,
                    ratio = ?,
                    target_weight = ?,
                    tolerance_percent = ?,
                    is_main = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                data['product_name'],
                data.get('product_code', ''),
                data['powder_name'],
                data.get('powder_category', 'incoming'),
                data['ratio'],
                data.get('target_weight', None),
                data.get('tolerance_percent', 5.0),
                1 if data.get('is_main', False) else 0,
                recipe_id
            ))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/recipe/<int:recipe_id>', methods=['DELETE'])
def admin_delete_recipe(recipe_id):
    """Recipe 삭제 (소프트 삭제)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 실제 삭제 대신 is_active = 0으로 변경
            cursor.execute('''
                UPDATE recipe SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (recipe_id,))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/recipe/product/<product_name>', methods=['DELETE'])
def admin_delete_product_recipes(product_name):
    """제품의 모든 Recipe 삭제 (소프트 삭제)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE recipe SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE product_name = ?
            ''', (product_name,))

            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 배합 작업 (Blending Work)
# ============================================

@app.route('/api/blending/products', methods=['GET'])
def get_blending_products():
    """배합 가능한 제품 목록 조회 (Recipe가 있는 제품만)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT DISTINCT product_name, product_code
                FROM recipe
                WHERE is_active = 1
                ORDER BY product_name
            ''')

            products = [dict_from_row(row) for row in cursor.fetchall()]

            return jsonify({'success': True, 'data': products})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/recipe/<product_name>', methods=['GET'])
def get_blending_recipe(product_name):
    """특정 제품의 Recipe 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM recipe
                WHERE product_name = ? AND is_active = 1
                ORDER BY id
            ''', (product_name,))

            recipes = [dict_from_row(row) for row in cursor.fetchall()]

            return jsonify({'success': True, 'data': recipes})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/start', methods=['POST'])
def start_blending_work():
    """배합 작업 시작"""
    try:
        data = request.json

        required_fields = ['product_name', 'batch_lot', 'target_total_weight', 'operator']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '필수 항목이 누락되었습니다.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 중복 확인 (batch_lot)
            cursor.execute('''
                SELECT id FROM blending_work WHERE batch_lot = ?
            ''', (data['batch_lot'],))

            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 배합 LOT입니다.'})

            # work_order가 있으면 중복 확인
            # work_order가 있으면 중복 확인 (단, 작업지시서 ID가 주어진 경우엔 동일 작업지시번호로
            # 여러 작업을 생성할 수 있도록 허용)
            if data.get('work_order') and not data.get('work_order_id'):
                cursor.execute('''
                    SELECT id FROM blending_work WHERE work_order = ?
                ''', (data['work_order'],))

                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '이미 존재하는 작업지시 번호입니다.'})

            # Main 분말 중량 정보를 JSON으로 변환
            main_powder_weights_json = None
            if 'main_powder_weights' in data and data['main_powder_weights']:
                import json
                main_powder_weights_json = json.dumps(data['main_powder_weights'], ensure_ascii=False)

            # 배합 작업 레코드 생성
            cursor.execute('''
                INSERT INTO blending_work (
                    work_order_id, work_order, product_name, product_code, batch_lot,
                    target_total_weight, operator, status, main_powder_weights
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
            ''', (
                data.get('work_order_id'),  # 작업지시서 ID (optional)
                data.get('work_order'),      # 작업지시 번호 (optional)
                data['product_name'],
                data.get('product_code', ''),
                data['batch_lot'],
                data['target_total_weight'],
                data['operator'],
                main_powder_weights_json
            ))

            work_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                'success': True,
                'work_id': work_id,
                'batch_lot': data['batch_lot']
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/generate-lot', methods=['GET'])
def generate_batch_lot():
    """배합 LOT 번호 자동 생성"""
    try:
        # YYYYMMDD-XXX 형식 (KST 기준 날짜)
        today = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')
        prefix = f'{today}-'

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 오늘 생성된 배치 중 마지막 번호 조회
            cursor.execute('''
                SELECT batch_lot FROM blending_work
                WHERE batch_lot LIKE ?
                ORDER BY batch_lot DESC
                LIMIT 1
            ''', (f'{prefix}%',))

            row = cursor.fetchone()

            if row:
                # 마지막 번호에서 1 증가
                last_lot = row[0]
                last_num = int(last_lot.split('-')[-1])
                next_num = last_num + 1
            else:
                # 오늘 첫 번째
                next_num = 1

            new_lot = f'{prefix}{next_num:03d}'

            return jsonify({'success': True, 'batch_lot': new_lot})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/work/<int:work_id>', methods=['GET'])
def get_blending_work(work_id):
    """배합 작업 상세 조회 (Recipe 포함)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 배합 작업 정보 조회
            cursor.execute('''
                SELECT * FROM blending_work
                WHERE id = ?
            ''', (work_id,))

            work_row = cursor.fetchone()

            if not work_row:
                return jsonify({'success': False, 'message': '배합 작업을 찾을 수 없습니다.'})

            work = dict_from_row(work_row)

            # Main 분말 중량 정보 파싱
            import json
            if work.get('main_powder_weights'):
                try:
                    work['main_powder_weights'] = json.loads(work['main_powder_weights'])
                except:
                    work['main_powder_weights'] = {}
            else:
                work['main_powder_weights'] = {}

            # Recipe 조회
            cursor.execute('''
                SELECT * FROM recipe
                WHERE product_name = ? AND is_active = 1
                ORDER BY id
            ''', (work['product_name'],))

            recipes = [dict_from_row(row) for row in cursor.fetchall()]

            # 이미 투입된 원재료 조회
            cursor.execute('''
                SELECT * FROM material_input
                WHERE blending_work_id = ?
                ORDER BY id
            ''', (work_id,))

            material_inputs = [dict_from_row(row) for row in cursor.fetchall()]

            # Main 분말들 찾기
            main_recipes = [r for r in recipes if r.get('is_main')]

            # 각 Recipe에 목표 중량 계산
            if main_recipes:
                # Main 분말 중량 합계 및 비율 합계
                total_main_weight = sum(work['main_powder_weights'].get(r['powder_name'], 0) for r in main_recipes)
                total_main_ratio = sum(r['ratio'] for r in main_recipes)

                for recipe in recipes:
                    if recipe.get('is_main'):
                        # Main 분말: 개별 지정 중량
                        recipe['calculated_weight'] = work['main_powder_weights'].get(recipe['powder_name'], 0)
                    elif total_main_weight > 0 and total_main_ratio > 0:
                        # 다른 분말: 전체 main 중량 × (해당 비율 / 전체 main 비율)
                        recipe['calculated_weight'] = total_main_weight * (recipe['ratio'] / total_main_ratio)
                    else:
                        recipe['calculated_weight'] = 0
            else:
                # Main 분말이 없는 경우 기존 방식
                for recipe in recipes:
                    recipe['calculated_weight'] = (work['target_total_weight'] * recipe['ratio'] / 100) if work['target_total_weight'] else 0

            return jsonify({
                'success': True,
                'work': work,
                'recipes': recipes,
                'material_inputs': material_inputs
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/work/<int:work_id>', methods=['DELETE'])
def delete_blending_work(work_id):
    """배합 작업 삭제 (진행중인 작업만 삭제 가능)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 작업 상태 확인
            cursor.execute('''
                SELECT status, batch_lot FROM blending_work WHERE id = ?
            ''', (work_id,))

            work = cursor.fetchone()

            if not work:
                return jsonify({'success': False, 'message': '배합 작업을 찾을 수 없습니다.'})

            if work[0] == 'completed':
                return jsonify({'success': False, 'message': '완료된 작업은 삭제할 수 없습니다.'})

            # 관련 원재료 투입 데이터 삭제
            cursor.execute('''
                DELETE FROM material_input WHERE blending_work_id = ?
            ''', (work_id,))

            # 배합 작업 삭제
            cursor.execute('''
                DELETE FROM blending_work WHERE id = ?
            ''', (work_id,))

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'배합 LOT "{work[1]}"이(가) 삭제되었습니다.'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/completed-lots/<powder_name>', methods=['GET'])
def get_completed_lots(powder_name):
    """특정 분말의 수입검사 완료된 LOT 번호 목록 조회"""
    try:
        category = request.args.get('category', 'incoming')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 수입검사 완료(PASS)된 LOT만 조회 (최근 5개)
            cursor.execute('''
                SELECT lot_number, inspection_time, final_result
                FROM inspection_result
                WHERE powder_name = ? AND category = ? AND final_result = 'PASS'
                ORDER BY inspection_time DESC
                LIMIT 5
            ''', (powder_name, category))

            lots = []
            for row in cursor.fetchall():
                lot_dict = dict_from_row(row)
                lots.append({
                    'lot_number': lot_dict['lot_number'],
                    'inspection_time': lot_dict['inspection_time']
                })

            return jsonify({'success': True, 'lots': lots})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/validate-lot/<lot_number>', methods=['GET'])
def validate_material_lot(lot_number):
    """원재료 LOT 검증 (수입검사 완료 여부 확인)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 수입검사 결과에서 LOT 조회
            cursor.execute('''
                SELECT powder_name, lot_number, final_result, inspection_time
                FROM inspection_result
                WHERE lot_number = ? AND category = 'incoming'
            ''', (lot_number,))

            row = cursor.fetchone()

            if not row:
                return jsonify({
                    'success': False,
                    'valid': False,
                    'message': f'LOT {lot_number}는 수입검사 기록이 없습니다.'
                })

            result = dict_from_row(row)

            if result['final_result'] != 'PASS':
                return jsonify({
                    'success': False,
                    'valid': False,
                    'message': f'LOT {lot_number}는 수입검사에서 불합격 처리되었습니다.'
                })

            return jsonify({
                'success': True,
                'valid': True,
                'powder_name': result['powder_name'],
                'lot_number': result['lot_number'],
                'inspection_time': result['inspection_time']
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/material-input', methods=['POST'])
def save_material_input():
    """원재료 투입 기록 저장"""
    try:
        data = request.json

        required_fields = ['blending_work_id', 'powder_name', 'material_lot', 'target_weight', 'actual_weight']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '필수 항목이 누락되었습니다.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 1. 이종분말 검증 (제품명과 LOT번호 둘 다 비교하여 검증)
            # 복수 LOT 지원: 쉼표로 구분된 LOT를 분리하여 검증
            material_lots = [lot.strip() for lot in data['material_lot'].split(',')]

            for lot in material_lots:
                # 제품명과 LOT 번호로 함께 조회 (lot번호가 동일해도 제품명이 다르면 구분)
                cursor.execute('''
                    SELECT powder_name FROM inspection_result
                    WHERE lot_number = ? AND powder_name = ? AND category = 'incoming'
                ''', (lot, data['powder_name']))

                lot_row = cursor.fetchone()

                if not lot_row:
                    # 먼저 LOT가 존재하는지 확인
                    cursor.execute('''
                        SELECT powder_name FROM inspection_result
                        WHERE lot_number = ? AND category = 'incoming'
                    ''', (lot,))
                    
                    check_row = cursor.fetchone()
                    
                    if not check_row:
                        return jsonify({
                            'success': False,
                            'message': f'LOT {lot}의 수입검사 기록을 찾을 수 없습니다.'
                        })
                    else:
                        # LOT는 있지만 제품명이 다른 경우
                        actual_powder = check_row[0]
                        return jsonify({
                            'success': False,
                            'message': f'이종분말 검출! 투입하려는 분말({data["powder_name"]})과 LOT {lot}의 실제 분말({actual_powder})이 다릅니다.',
                            'is_wrong_material': True
                        })

            # 2. 중량 편차 계산
            target_weight = float(data['target_weight'])
            actual_weight = float(data['actual_weight'])
            weight_deviation = ((actual_weight - target_weight) / target_weight * 100) if target_weight > 0 else 0
            weight_deviation = round(weight_deviation, 2)

            # 3. 허용 오차 확인
            tolerance = float(data.get('tolerance_percent', 5.0))
            is_valid = abs(weight_deviation) <= tolerance

            validation_message = None
            if not is_valid:
                validation_message = f'중량 편차({abs(weight_deviation):.2f}%)가 허용 오차({tolerance}%)를 초과했습니다.'

                # NG(부적정) 판정일 경우 저장 거부
                return jsonify({
                    'success': False,
                    'is_valid': False,
                    'message': f'부적정(NG) 판정되어 저장할 수 없습니다.\n{validation_message}',
                    'validation_message': validation_message,
                    'weight_deviation': weight_deviation
                })

            # 4. material_input 테이블에 저장 (적정 판정된 경우만)
            cursor.execute('''
                INSERT INTO material_input (
                    blending_work_id, powder_name, powder_category, material_lot,
                    target_weight, actual_weight, weight_deviation, is_valid,
                    validation_message, input_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['blending_work_id'],
                data['powder_name'],
                data.get('powder_category', 'incoming'),
                data['material_lot'],
                target_weight,
                actual_weight,
                weight_deviation,
                1 if is_valid else 0,
                validation_message,
                data.get('operator', '미지정')
            ))

            material_input_id = cursor.lastrowid

            # 5. 배합 작업의 실제 총 중량 업데이트
            cursor.execute('''
                SELECT COALESCE(SUM(actual_weight), 0) FROM material_input
                WHERE blending_work_id = ?
            ''', (data['blending_work_id'],))

            total_actual_weight = cursor.fetchone()[0]

            cursor.execute('''
                UPDATE blending_work
                SET actual_total_weight = ?
                WHERE id = ?
            ''', (total_actual_weight, data['blending_work_id']))

            conn.commit()

            return jsonify({
                'success': True,
                'material_input_id': material_input_id,
                'weight_deviation': weight_deviation,
                'is_valid': is_valid,
                'validation_message': validation_message
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/complete/<int:work_id>', methods=['PUT'])
def complete_blending_work(work_id):
    """배합 작업 완료 처리"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 모든 원재료가 투입되었는지 확인
            cursor.execute('''
                SELECT COUNT(*) FROM recipe
                WHERE product_name = (
                    SELECT product_name FROM blending_work WHERE id = ?
                ) AND is_active = 1
            ''', (work_id,))

            expected_count = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM material_input
                WHERE blending_work_id = ?
            ''', (work_id,))

            actual_count = cursor.fetchone()[0]

            if actual_count < expected_count:
                return jsonify({
                    'success': False,
                    'message': f'아직 모든 원재료가 투입되지 않았습니다. ({actual_count}/{expected_count})'
                })

            # 배합 작업 상태를 완료로 변경
            cursor.execute('''
                UPDATE blending_work
                SET status = 'completed', end_time = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (work_id,))

            conn.commit()

            return jsonify({'success': True, 'message': '배합 작업이 완료되었습니다.'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending/works', methods=['GET'])
def get_blending_works():
    """배합작업 목록 조회 (완료된 작업 포함)"""
    try:
        status = request.args.get('status', 'all')  # all, completed, in_progress
        product_name = request.args.get('product_name')
        batch_lot = request.args.get('batch_lot')
        completed_date = request.args.get('completed_date')  # YYYY-MM-DD

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # Build dynamic query with optional filters
            base_select = '''
                SELECT
                    id, work_order, product_name, product_code, batch_lot,
                    target_total_weight, actual_total_weight,
                    blending_time, blending_temperature, blending_rpm,
                    operator, status, start_time, end_time, notes
                FROM blending_work
            '''

            where_clauses = []
            params = []

            if status and status != 'all':
                where_clauses.append('status = ?')
                params.append(status)

            if product_name:
                where_clauses.append('product_name LIKE ?')
                params.append(f"%{product_name}%")

            if batch_lot:
                where_clauses.append('batch_lot LIKE ?')
                params.append(f"%{batch_lot}%")

            if completed_date:
                # filter by DATE(end_time) == completed_date
                where_clauses.append("DATE(end_time) = ?")
                params.append(completed_date)

            query = base_select
            if where_clauses:
                query += ' WHERE ' + ' AND '.join(where_clauses)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, tuple(params))

            works = []
            for row in cursor.fetchall():
                work_dict = dict_from_row(row)
                works.append(work_dict)

            return jsonify({'success': True, 'works': works})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# API: 추적성 (Traceability)
# ============================================

@app.route('/api/traceability/batch/<batch_lot>', methods=['GET'])
def trace_by_batch_lot(batch_lot):
    """배합 LOT로 추적 (Backward Traceability): 배합 → 원재료 → 수입검사"""
    product_name = request.args.get('product_name', '')
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 1. 배합 작업 정보 조회
            cursor.execute('''
                SELECT * FROM blending_work
                WHERE batch_lot = ?
            ''', (batch_lot,))

            work_row = cursor.fetchone()

            if not work_row:
                return jsonify({
                    'success': False,
                    'message': f'배합 LOT {batch_lot}를 찾을 수 없습니다.'
                })

            work = dict_from_row(work_row)

            # 2. 원재료 투입 이력 조회
            cursor.execute('''
                SELECT * FROM material_input
                WHERE blending_work_id = ?
                ORDER BY id
            ''', (work['id'],))

            material_inputs = [dict_from_row(row) for row in cursor.fetchall()]

            # 3. 각 원재료의 수입검사 결과 조회 (제품명과 lot번호로 조회)
            for material in material_inputs:
                cursor.execute('''
                    SELECT powder_name, lot_number, inspection_type, inspector,
                           inspection_time, final_result
                    FROM inspection_result
                    WHERE lot_number = ? AND powder_name = ? AND category = 'incoming'
                ''', (material['material_lot'], material['powder_name']))

                inspection_row = cursor.fetchone()
                if inspection_row:
                    material['incoming_inspection'] = dict_from_row(inspection_row)
                else:
                    material['incoming_inspection'] = None

            return jsonify({
                'success': True,
                'trace_type': 'backward',
                'batch_lot': batch_lot,
                'blending_work': work,
                'material_inputs': material_inputs
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/traceability/material/<material_lot>', methods=['GET'])
def trace_by_material_lot(material_lot):
    """원재료 LOT와 분말명으로 추적 (Forward Traceability): 수입검사 → 사용된 배합들"""
    powder_name = request.args.get('powder_name', '')
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 1. 수입검사 결과 조회 (제품명과 lot번호로 조회)
            if powder_name:
                cursor.execute('''
                    SELECT * FROM inspection_result
                    WHERE lot_number = ? AND powder_name = ? AND category = 'incoming'
                ''', (material_lot, powder_name))
            else:
                # powder_name이 없으면 lot번호만으로 검색
                cursor.execute('''
                    SELECT * FROM inspection_result
                    WHERE lot_number = ? AND category = 'incoming'
                ''', (material_lot,))

            inspection_row = cursor.fetchone()

            if not inspection_row:
                if powder_name:
                    return jsonify({
                        'success': False,
                        'message': f'분말명({powder_name})과 LOT {material_lot}의 수입검사 기록을 찾을 수 없습니다.'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'원재료 LOT {material_lot}의 수입검사 기록을 찾을 수 없습니다.'
                    })

            inspection = dict_from_row(inspection_row)

            # 2. 이 LOT과 분말명이 사용된 모든 배합 작업 조회
            cursor.execute('''
                SELECT
                    mi.*,
                    bw.work_order,
                    bw.product_name,
                    bw.batch_lot,
                    bw.target_total_weight,
                    bw.actual_total_weight,
                    bw.operator,
                    bw.status,
                    bw.start_time,
                    bw.end_time
                FROM material_input mi
                JOIN blending_work bw ON mi.blending_work_id = bw.id
                WHERE mi.material_lot = ? AND mi.powder_name = ?
                ORDER BY bw.start_time DESC
            ''', (material_lot, powder_name))

            usages = [dict_from_row(row) for row in cursor.fetchall()]

            return jsonify({
                'success': True,
                'trace_type': 'forward',
                'material_lot': material_lot,
                'incoming_inspection': inspection,
                'used_in_batches': usages
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/traceability/search', methods=['GET'])
def search_traceability():
    """통합 추적성 검색 (분말명과 LOT번호로 검색)"""
    try:
        lot_number = request.args.get('lot_number', '')
        powder_name = request.args.get('powder_name', '')

        if not lot_number:
            return jsonify({'success': False, 'message': 'LOT 번호를 입력하세요.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            result = {
                'success': True,
                'lot_number': lot_number,
                'powder_name': powder_name,
                'found_as': []
            }

            # 1. 배합 LOT로 검색
            cursor.execute('''
                SELECT COUNT(*) FROM blending_work
                WHERE batch_lot = ?
            ''', (lot_number,))

            if cursor.fetchone()[0] > 0:
                result['found_as'].append('batch_lot')

            # 2. 원재료 LOT로 검색 (분말명도 함께 검색)
            if powder_name:
                cursor.execute('''
                    SELECT COUNT(*) FROM inspection_result
                    WHERE lot_number = ? AND powder_name = ? AND category = 'incoming'
                ''', (lot_number, powder_name))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM inspection_result
                    WHERE lot_number = ? AND category = 'incoming'
                ''', (lot_number,))

            if cursor.fetchone()[0] > 0:
                result['found_as'].append('material_lot')

            if not result['found_as']:
                if powder_name:
                    return jsonify({
                        'success': False,
                        'message': f'분말명({powder_name})과 LOT {lot_number}를 찾을 수 없습니다.'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'LOT {lot_number}를 찾을 수 없습니다.'
                    })

            return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# 배합작업지시서 (Blending Order) API
# ============================================

@app.route('/api/blending-orders', methods=['POST'])
def create_blending_order():
    """배합작업지시서 생성"""
    try:
        data = request.json

        required_fields = ['product_name', 'total_target_weight']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '필수 항목이 누락되었습니다.'})

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 작업지시번호 자동 생성 (WO-YYYYMMDD-001 형식)
            today = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')

            cursor.execute('''
                SELECT work_order_number FROM blending_order
                WHERE work_order_number LIKE ?
                ORDER BY work_order_number DESC
                LIMIT 1
            ''', (f'WO-{today}-%',))

            last_order = cursor.fetchone()

            if last_order:
                # 마지막 번호 추출 및 증가
                last_num = int(last_order[0].split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            work_order_number = f'WO-{today}-{new_num:03d}'

            # 작업지시서 저장 (work_date가 전달되면 created_date에 사용)
            work_date = data.get('work_date')
            if work_date:
                cursor.execute('''
                    INSERT INTO blending_order (
                        work_order_number, product_name, product_code,
                        total_target_weight, created_by, notes, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    work_order_number,
                    data['product_name'],
                    data.get('product_code'),
                    float(data['total_target_weight']),
                    data.get('created_by', '미지정'),
                    data.get('notes'),
                    work_date
                ))
            else:
                cursor.execute('''
                    INSERT INTO blending_order (
                        work_order_number, product_name, product_code,
                        total_target_weight, created_by, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    work_order_number,
                    data['product_name'],
                    data.get('product_code'),
                    float(data['total_target_weight']),
                    data.get('created_by', '미지정'),
                    data.get('notes')
                ))

            order_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                'success': True,
                'order_id': order_id,
                'work_order_number': work_order_number,
                'message': f'작업지시서가 생성되었습니다. ({work_order_number})'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending-orders', methods=['GET'])
def get_blending_orders():
    """배합작업지시서 목록 조회"""
    try:
        status_filter = request.args.get('status', 'all')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            if status_filter == 'all':
                cursor.execute('''
                    SELECT * FROM blending_order
                    ORDER BY created_date DESC, id DESC
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM blending_order
                    WHERE status = ?
                    ORDER BY created_date DESC, id DESC
                ''', (status_filter,))

            rows = cursor.fetchall()
            orders = []

            for row in rows:
                order = dict(row)

                # 진도율 계산
                cursor.execute('''
                    SELECT COALESCE(SUM(target_total_weight), 0)
                    FROM blending_work
                    WHERE work_order_id = ? AND status = 'completed'
                ''', (order['id'],))

                completed_weight = cursor.fetchone()[0]
                total_target_weight = order['total_target_weight']

                if total_target_weight > 0:
                    progress_percent = (completed_weight / total_target_weight) * 100
                else:
                    progress_percent = 0

                order['completed_weight'] = completed_weight
                order['progress_percent'] = round(progress_percent, 1)

                # 진행 중인 배합 작업 수
                cursor.execute('''
                    SELECT COUNT(*) FROM blending_work
                    WHERE work_order_id = ? AND status = 'in_progress'
                ''', (order['id'],))

                order['in_progress_count'] = cursor.fetchone()[0]

                # 완료된 배합 작업 수
                cursor.execute('''
                    SELECT COUNT(*) FROM blending_work
                    WHERE work_order_id = ? AND status = 'completed'
                ''', (order['id'],))

                order['completed_count'] = cursor.fetchone()[0]

                # 자동으로 상태 업데이트 (진도율 100%면 완료)
                if progress_percent >= 100 and order['status'] != 'completed':
                    cursor.execute('''
                        UPDATE blending_order
                        SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (order['id'],))
                    conn.commit()
                    order['status'] = 'completed'

                orders.append(order)

            return jsonify({
                'success': True,
                'orders': orders
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending-orders/<int:order_id>', methods=['GET'])
def get_blending_order(order_id):
    """배합작업지시서 상세 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM blending_order WHERE id = ?', (order_id,))
            row = cursor.fetchone()

            if not row:
                return jsonify({'success': False, 'message': '작업지시서를 찾을 수 없습니다.'})

            order = dict(row)

            # 진도율 계산
            cursor.execute('''
                SELECT COALESCE(SUM(target_total_weight), 0)
                FROM blending_work
                WHERE work_order_id = ? AND status = 'completed'
            ''', (order_id,))

            completed_weight = cursor.fetchone()[0]
            total_target_weight = order['total_target_weight']

            if total_target_weight > 0:
                progress_percent = (completed_weight / total_target_weight) * 100
            else:
                progress_percent = 0

            order['completed_weight'] = completed_weight
            order['progress_percent'] = round(progress_percent, 1)

            # 연관된 배합 작업 목록
            cursor.execute('''
                SELECT * FROM blending_work
                WHERE work_order_id = ?
                ORDER BY start_time DESC
            ''', (order_id,))

            order['blending_works'] = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                'success': True,
                'order': order
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/blending-orders/<int:order_id>', methods=['DELETE'])
def delete_blending_order(order_id):
    """작업지시서 삭제 (연관된 배합작업이 있으면 삭제 불가)"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 연관된 배합작업이 있는지 확인
            cursor.execute('SELECT COUNT(*) FROM blending_work WHERE work_order_id = ?', (order_id,))
            cnt = cursor.fetchone()[0]
            if cnt > 0:
                return jsonify({'success': False, 'message': '연관된 배합작업이 있어 삭제할 수 없습니다. 관련 작업을 먼저 삭제하세요.'})

            cursor.execute('DELETE FROM blending_order WHERE id = ?', (order_id,))
            conn.commit()

            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/blending-orders/<int:order_id>/progress', methods=['GET'])
def get_blending_order_progress(order_id):
    """배합작업지시서 진도율 조회"""
    try:
        with closing(get_db()) as conn:
            cursor = conn.cursor()

            # 작업지시서 정보
            cursor.execute('SELECT total_target_weight FROM blending_order WHERE id = ?', (order_id,))
            row = cursor.fetchone()

            if not row:
                return jsonify({'success': False, 'message': '작업지시서를 찾을 수 없습니다.'})

            total_target_weight = row[0]

            # 완료된 중량 합계
            cursor.execute('''
                SELECT COALESCE(SUM(target_total_weight), 0)
                FROM blending_work
                WHERE work_order_id = ? AND status = 'completed'
            ''', (order_id,))

            completed_weight = cursor.fetchone()[0]

            # 진도율 계산
            if total_target_weight > 0:
                progress_percent = (completed_weight / total_target_weight) * 100
            else:
                progress_percent = 0

            # 남은 중량
            remaining_weight = total_target_weight - completed_weight

            return jsonify({
                'success': True,
                'total_target_weight': total_target_weight,
                'completed_weight': completed_weight,
                'remaining_weight': remaining_weight,
                'progress_percent': round(progress_percent, 1)
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# 서버 실행
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("분말 검사 시스템 서버 시작")
    print("=" * 50)
    print("접속 주소: http://localhost:5000")
    print("내부 네트워크 접속: http://<이 PC의 IP>:5000")
    print("종료: Ctrl+C")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
