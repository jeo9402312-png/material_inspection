// 분말 검사 시스템 - 메인 JavaScript

// API Base URL
const API_BASE = '';

// 현재 검사 데이터
let currentInspection = null;
let currentItems = [];
// 임시 판정 결과 저장
let pendingResults = {};

// 다국어 지원
let currentLang = localStorage.getItem('language') || 'ko';

// 안전한 이벤트 리스너 추가 헬퍼 함수
function safeAddEventListener(elementId, eventType, handler) {
    const element = document.getElementById(elementId);
    if (element) {
        element.addEventListener(eventType, handler);
        return true;
    }
    return false;
}

// 번역 헬퍼 함수
function t(key) {
    return translations[currentLang][key] || key;
}

// 언어 전환 함수
function toggleLanguage() {
    currentLang = currentLang === 'ko' ? 'en' : 'ko';
    localStorage.setItem('language', currentLang);
    updateLanguage();
}

function updateLanguage() {
    const t = translations[currentLang];

    // data-i18n 속성을 가진 모든 요소 업데이트
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (t[key]) {
            element.textContent = t[key];
        }
    });

    // data-i18n-placeholder 속성을 가진 모든 요소 업데이트
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        if (t[key]) {
            element.placeholder = t[key];
        }
    });

    // 언어 버튼 텍스트 업데이트
    document.getElementById('langText').textContent = currentLang === 'ko' ? 'English' : '한국어';
}

        // ============================================
        // 준비중 메뉴 안내
        // ============================================
        function showComingSoon(menuName) {
            const message = currentLang === 'ko'
                ? `"${menuName}" 기능은 현재 개발 중입니다.\n\n향후 업데이트에서 제공될 예정입니다.`
                : `"${menuName}" feature is currently under development.\n\nIt will be available in a future update.`;
            alert(message);
        }

        // ============================================
        // 페이지 전환
        // ============================================
        function showPage(pageName) {
            // 페이지 전환
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            document.getElementById(pageName).classList.add('active');

            // 네비게이션 active 상태 업데이트
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            const activeNav = document.querySelector(`.nav-item[data-page="${pageName}"]`);
            if (activeNav) {
                activeNav.classList.add('active');
            }

            // 페이지별 초기화
            if (pageName === 'dashboard') {
                loadIncompleteInspections();
            } else if (pageName === 'incoming') {
                loadPowderList('incoming');
                loadInspectorList('incoming');
            } else if (pageName === 'mixing') {
                // mixing 페이지는 완료된 배합작업 목록만 보여줌
                loadMixingPage();
            } else if (pageName === 'blending') {
                // hide form initially so only orders list shows
                hideBlendingForm();
                loadBlendingPage();
            } else if (pageName === 'search') {
                loadPowderListForSearch();
            } else if (pageName === 'blending-log') {
                loadBlendingWorks();
            } else if (pageName === 'blending-orders') {
                loadBlendingOrdersPage();
            } else if (pageName === 'admin') {
                loadAdminPage();
            }
        }

        // ============================================
        // 관리자 페이지: 탭 전환
        // ============================================
        function showAdminTab(tabName) {
            // 탭 버튼 active 상태 변경
            document.querySelectorAll('.admin-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.closest('.admin-tab').classList.add('active');

            // 탭 콘텐츠 전환
            document.querySelectorAll('.admin-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
        }

        // ============================================
        // 대시보드: 진행중 검사 목록
        // ============================================
        async function loadIncompleteInspections() {
            try {
                const response = await fetch(`${API_BASE}/api/incomplete-inspections`);
                const data = await response.json();

                const listDiv = document.getElementById('incompleteList');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('category')}</th><th>${t('powderName')}</th><th>${t('lotNumber')}</th><th>${t('inspectionType')}</th><th>${t('inspector')}</th><th>${t('progress')}</th><th>${t('action')}</th></tr>`;

                    data.data.forEach(item => {
                        const categoryBadge = item.category === 'incoming'
                            ? `<span class="badge" style="background: #2196F3;">${t('incoming')}</span>`
                            : `<span class="badge" style="background: #FF9800;">${t('mixing')}</span>`;

                        html += `
                            <tr>
                                <td>${categoryBadge}</td>
                                <td>${item.powder_name}</td>
                                <td>${item.lot_number}</td>
                                <td>${item.inspection_type}</td>
                                <td>${item.inspector}</td>
                                <td><span class="badge progress">${item.progress}</span></td>
                                <td>
                                    <button class="btn" onclick="continueInspection('${item.powder_name}', '${item.lot_number}', '${item.category}')" style="margin-right: 5px;">${t('continue')}</button>
                                    <button class="btn danger" onclick="deleteIncompleteInspection('${item.powder_name}', '${item.lot_number}')">${t('delete')}</button>
                                </td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noOngoingInspections')}</div>`;
                }
            } catch (error) {
                document.getElementById('incompleteList').innerHTML = `<div class="empty-message">오류: ${error.message}</div>`;
            }
        }

        // 진행중인 검사 삭제
        async function deleteIncompleteInspection(powderName, lotNumber) {
            if (!confirm(t('deleteInspectionConfirm'))) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/delete-incomplete-inspection/${encodeURIComponent(powderName)}/${encodeURIComponent(lotNumber)}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert(t('deleteSuccess'));
                    loadIncompleteInspections();  // 목록 새로고침
                } else {
                    alert(t('deleteError') + ': ' + data.message);
                }
            } catch (error) {
                alert(t('deleteError') + ': ' + error.message);
            }
        }

        // ============================================
        // 검사 시작
        // ============================================
        async function loadPowderList(category = null) {
            try {
                const url = category
                    ? `${API_BASE}/api/powder-list?category=${category}`
                    : `${API_BASE}/api/powder-list`;
                const response = await fetch(url);
                const data = await response.json();

                const selectId = category ? `${category}PowderName` : 'powderName';
                const select = document.getElementById(selectId);
                if (!select) return;

                select.innerHTML = '<option value="">선택하세요</option>';

                if (data.success) {
                    data.data.forEach(powder => {
                        const option = document.createElement('option');
                        option.value = powder;
                        option.textContent = powder;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                alert('분말 목록 로딩 실패: ' + error.message);
            }
        }

        async function loadInspectorList(category = null) {
            try {
                const response = await fetch(`${API_BASE}/api/inspector-list`);
                const data = await response.json();

                const selectId = category ? `${category}Inspector` : 'inspector';
                const select = document.getElementById(selectId);
                if (!select) return;

                select.innerHTML = '<option value="">선택하세요</option>';

                if (data.success) {
                    data.data.forEach(inspector => {
                        const option = document.createElement('option');
                        option.value = inspector;
                        option.textContent = inspector;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                alert('검사자 목록 로딩 실패: ' + error.message);
            }
        }

        // 수입검사 폼 처리
        const incomingFormElement = document.getElementById('incomingForm');

        if (incomingFormElement) {

            incomingFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const powderName = document.getElementById('incomingPowderName').value;
            const lotNumber = document.getElementById('incomingLotNumber').value;
            const inspectionType = document.getElementById('incomingInspectionType').value;
            const inspector = document.getElementById('incomingInspector').value;
            const category = 'incoming';

            await startInspection(powderName, lotNumber, inspectionType, inspector, category);
        });
        }

        // 배합검사 폼 처리
        const mixingFormElement = document.getElementById('mixingForm');

        if (mixingFormElement) {

            mixingFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const powderName = document.getElementById('mixingPowderName').value;
            const lotNumber = document.getElementById('mixingLotNumber').value;
            const inspectionType = document.getElementById('mixingInspectionType').value;
            const inspector = document.getElementById('mixingInspector').value;
            const category = 'mixing';

            await startInspection(powderName, lotNumber, inspectionType, inspector, category);
        });
        }

        // 배합작업 조회에서 넘어온 경우 LOT 정보 자동 채우기
        function checkAndFillBlendingInspectionLot() {
            const batchLot = sessionStorage.getItem('blendingInspectionLot');
            const productName = sessionStorage.getItem('blendingInspectionProduct');

            if (batchLot && productName) {
                // LOT 정보 채우기 (배합 LOT는 제품명과 동일)
                setTimeout(() => {
                    const powderSelect = document.getElementById('mixingPowderName');
                    if (powderSelect) {
                        // 제품명을 분말명 선택에서 찾기
                        for (let option of powderSelect.options) {
                            if (option.value === productName) {
                                option.selected = true;
                                break;
                            }
                        }
                    }

                    const lotInput = document.getElementById('mixingLotNumber');
                    if (lotInput) {
                        lotInput.value = batchLot;
                    }

                    // sessionStorage 클리어
                    sessionStorage.removeItem('blendingInspectionLot');
                    sessionStorage.removeItem('blendingInspectionProduct');
                }, 300);  // 분말 목록 로딩 대기
            }
        }

        // 검사 시작 공통 함수
        async function startInspection(powderName, lotNumber, inspectionType, inspector, category) {
            try {
                const response = await fetch(`${API_BASE}/api/start-inspection`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ powderName, lotNumber, inspectionType, inspector, category })
                });

                const data = await response.json();

                if (data.success) {
                    if (data.isExisting && data.data.isCompleted) {
                        alert('이미 완료된 검사입니다.');
                        return;
                    }

                    currentInspection = data.data;
                    currentItems = data.items;

                    showInspectionPage();
                } else {
                    alert('검사 시작 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 검사 진행 페이지
        // ============================================
        async function continueInspection(powderName, lotNumber, category) {
            // Fetch existing inspection data
            try {
                const response = await fetch(`${API_BASE}/api/start-inspection`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ powderName, lotNumber, inspectionType: '', inspector: '', category })
                });

                const data = await response.json();

                if (data.success) {
                    currentInspection = data.data;
                    currentItems = data.items;
                    showInspectionPage();
                } else {
                    alert('검사 로딩 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        function showInspectionPage() {
            document.getElementById('infoPowderName').textContent = currentInspection.powderName;
            document.getElementById('infoLotNumber').textContent = currentInspection.lotNumber;
            document.getElementById('infoInspector').textContent = currentInspection.inspector;

            const completed = currentInspection.completedItems || [];
            const total = currentInspection.totalItems || [];
            document.getElementById('infoProgress').textContent = `${completed.length}/${total.length}`;

            renderInspectionItems();
            showPage('inspection');
        }

        function renderInspectionItems() {
            const container = document.getElementById('inspectionItems');
            container.innerHTML = '';

            const completed = currentInspection.completedItems || [];

            currentItems.forEach(item => {
                const isCompleted = completed.includes(item.name);

                const itemDiv = document.createElement('div');
                itemDiv.className = 'card';
                itemDiv.style.borderLeft = isCompleted ? '5px solid #4CAF50' : '5px solid #667eea';
                itemDiv.style.boxShadow = isCompleted ? '0 2px 8px rgba(76, 175, 80, 0.2)' : '0 2px 8px rgba(102, 126, 234, 0.2)';

                let html = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h3 style="margin: 0; color: #2c3e50; font-size: 1.3em;">${item.displayName}</h3>
                        ${isCompleted ? '<span class="badge pass" style="font-size: 1em; padding: 6px 12px;">✓ 완료</span>' : '<span class="badge progress" style="font-size: 1em; padding: 6px 12px;">진행중</span>'}
                    </div>
                    <div style="padding: 10px; background: #f5f7fa; border-radius: 5px; margin-bottom: 15px;">
                        <strong style="color: #667eea;">측정 단위:</strong> ${item.unit} |
                        <strong style="color: #667eea;">규격:</strong> ${item.min || '-'} ~ ${item.max || '-'} ${item.unit}
                    </div>
                `;

                if (!isCompleted) {
                    html += `<div id="item-${item.name}"></div>`;
                }

                itemDiv.innerHTML = html;
                container.appendChild(itemDiv);

                if (!isCompleted) {
                    renderItemInputs(item);
                }
            });
        }

        function renderItemInputs(item) {
            const container = document.getElementById(`item-${item.name}`);

            if (item.isParticleSize) {
                // 입도분석
                let html = '<h4 style="margin-bottom: 15px; color: #667eea;">📊 입도분석 측정</h4>';
                html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">';
                item.particleSpecs.forEach((spec, index) => {
                    html += `
                        <div style="padding: 15px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="font-weight: 600; margin-bottom: 8px; color: #2c3e50;">${spec.mesh_size}</div>
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 10px;">규격: ${spec.min_value}~${spec.max_value}%</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                                <input type="number" step="0.1" placeholder="1차" id="${item.name}_${index}_1" style="padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                <input type="number" step="0.1" placeholder="2차" id="${item.name}_${index}_2" style="padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                html += `<div style="display: flex; gap:8px; margin-top: 20px;\"><button class="btn" onclick="judgeParticleSize('${item.name}')" style="flex:1;">🔎 판정</button><button class="btn" id="final-save-${item.name}" onclick="finalSaveParticleSize('${item.name}')" style="flex:1;" disabled>💾 최종저장</button></div>`;
                html += '<div class="result-display" id="result-' + item.name + '" style="display:none; margin-top: 15px;"></div>';
                container.innerHTML = html;

            } else if (item.isWeightBased) {
                // 중량 기반 항목 (겉보기밀도, 수분도, 회분도)
                let label1 = '', label2 = '';
                if (item.name === 'ApparentDensity') {
                    label1 = '빈컵중량';
                    label2 = '분말중량';
                } else if (item.name === 'Moisture') {
                    label1 = '초기중량';
                    label2 = '건조후중량';
                } else if (item.name === 'Ash') {
                    label1 = '초기중량';
                    label2 = '회분중량';
                }

                let html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0;">';
                for (let i = 1; i <= 3; i++) {
                    html += `
                        <div style="padding: 15px; background: #f9f9f9; border-radius: 8px; border: 2px solid #e0e0e0;">
                            <div style="font-weight: 600; margin-bottom: 10px; text-align: center; color: #667eea;">${i}차 측정</div>
                            <div style="margin-bottom: 8px;">
                                <label style="font-size: 0.85em; color: #666;">${label1} (g)</label>
                                <input type="number" step="0.01" placeholder="${label1}" id="${item.name}_${label1}_${i}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px; margin-top: 4px;">
                            </div>
                            <div>
                                <label style="font-size: 0.85em; color: #666;">${label2} (g)</label>
                                <input type="number" step="0.01" placeholder="${label2}" id="${item.name}_${label2}_${i}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px; margin-top: 4px;">
                            </div>
                        </div>
                    `;
                }
                html += '</div>';
                html += `<div style="display: flex; gap:8px; margin-top: 10px;\"><button class="btn" onclick="judgeItem('${item.name}', true)" style="flex:1;">🔎 판정</button><button class="btn" id="final-save-${item.name}" onclick="finalSaveItem('${item.name}', true)" style="flex:1;" disabled>💾 최종저장</button></div>`;
                html += '<div class="result-display" id="result-' + item.name + '" style="display:none; margin-top: 15px;"></div>';
                container.innerHTML = html;

            } else {
                // 일반 항목
                let html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0;">';
                for (let i = 1; i <= 3; i++) {
                    html += `
                        <div style="text-align: center;">
                            <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #667eea;">${i}차 측정</label>
                            <input type="number" step="0.01" placeholder="값 입력" id="${item.name}_${i}" style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 1.1em; text-align: center;">
                        </div>
                    `;
                }
                html += '</div>';
                html += `<div style="display: flex; gap:8px; margin-top: 10px;\"><button class="btn" onclick="judgeItem('${item.name}', false)" style="flex:1;">🔎 판정</button><button class="btn" id="final-save-${item.name}" onclick="finalSaveItem('${item.name}', false)" style="flex:1;" disabled>💾 최종저장</button></div>`;
                html += '<div class="result-display" id="result-' + item.name + '" style="display:none; margin-top: 15px;"></div>';
                container.innerHTML = html;
            }
        }

        // 로컬 판정: 입력값으로 평균/판정 계산 후 화면에 표시만 하고, 최종 저장 버튼을 활성화
        function judgeItem(itemName, isWeightBased) {
            const item = currentItems.find(i => i.name === itemName);
            if (!item) return alert('항목 정보를 찾을 수 없습니다.');

            let values = [];
            let average = null;
            let result = 'PASS';

            if (isWeightBased) {
                let label1 = '', label2 = '';
                if (itemName === 'ApparentDensity') {
                    label1 = '빈컵중량';
                    label2 = '분말중량';
                } else if (itemName === 'Moisture') {
                    label1 = '초기중량';
                    label2 = '건조후중량';
                } else if (itemName === 'Ash') {
                    label1 = '초기중량';
                    label2 = '회분중량';
                }

                const calcVals = [];
                for (let i = 1; i <= 3; i++) {
                    const val1 = document.getElementById(`${itemName}_${label1}_${i}`).value;
                    const val2 = document.getElementById(`${itemName}_${label2}_${i}`).value;
                    values.push(val1 || '', val2 || '');

                    if (itemName === 'ApparentDensity') {
                        if (val1 && val2) {
                            const density = (parseFloat(val2) - parseFloat(val1)) / 25;
                            calcVals.push(density);
                        }
                    } else if (itemName === 'Moisture') {
                        if (val1 && val2) {
                            const m = ((parseFloat(val1) - parseFloat(val2)) / parseFloat(val1)) * 100;
                            calcVals.push(m);
                        }
                    } else if (itemName === 'Ash') {
                        if (val1 && val2) {
                            // Ash: use decrease rate like Moisture ((initial - ash)/initial)*100
                            const a = ((parseFloat(val1) - parseFloat(val2)) / parseFloat(val1)) * 100;
                            calcVals.push(a);
                        }
                    }
                }

                if (calcVals.length > 0) {
                    average = Math.round((calcVals.reduce((s, v) => s + v, 0) / calcVals.length) * 100) / 100;
                }

            } else {
                const vals = [];
                for (let i = 1; i <= 3; i++) {
                    const val = document.getElementById(`${itemName}_${i}`).value;
                    values.push(val || '');
                    if (val !== '') vals.push(parseFloat(val));
                }
                if (vals.length > 0) {
                    average = Math.round((vals.reduce((s, v) => s + v, 0) / vals.length) * 100) / 100;
                }
            }

            // 규격 판정 (로컬)
            if (average !== null) {
                const min = item.min;
                const max = item.max;
                if ((min !== null && min !== undefined && average < min) || (max !== null && max !== undefined && average > max)) {
                    result = 'FAIL';
                } else {
                    result = 'PASS';
                }
            } else {
                return alert('유효한 측정값이 없습니다.');
            }

            // 결과 표시 및 임시저장
            const resultDiv = document.getElementById('result-' + itemName);
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `평균: ${average} | 결과: <span class="badge ${result === 'PASS' ? 'pass' : 'fail'}">${result}</span>`;

            pendingResults[itemName] = { values: values, average: average, result: result };

            // 최종 저장 버튼 활성화
            const finalBtn = document.getElementById(`final-save-${itemName}`);
            if (finalBtn) finalBtn.disabled = false;
        }

        // 서버에 실제 저장 (최종 저장)
        async function finalSaveItem(itemName, isWeightBased) {
            const pending = pendingResults[itemName];
            if (!pending) return alert('먼저 판정(검증)을 수행하세요.');

            try {
                const response = await fetch(`${API_BASE}/api/save-item`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        powderName: currentInspection.powderName,
                        lotNumber: currentInspection.lotNumber,
                        itemName: itemName,
                        values: pending.values
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const resultDiv = document.getElementById('result-' + itemName);
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `평균: ${data.average} | 결과: <span class="badge ${data.result === 'PASS' ? 'pass' : 'fail'}">${data.result}</span>`;

                    // 완료 항목에 추가
                    if (!currentInspection.completedItems.includes(itemName)) {
                        currentInspection.completedItems.push(itemName);
                    }

                    // pending 제거 및 버튼 비활성화
                    delete pendingResults[itemName];
                    const finalBtn = document.getElementById(`final-save-${itemName}`);
                    if (finalBtn) finalBtn.disabled = true;

                    // 검사 진행 상황 갱신
                    setTimeout(async () => {
                        await checkInspectionCompletion();
                        renderInspectionItems();
                    }, 500);
                } else {
                    alert('저장 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        async function checkInspectionCompletion() {
            // 모든 항목이 완료되었는지 확인
            const totalItems = currentInspection.totalItems || [];
            const completedItems = currentInspection.completedItems || [];

            if (completedItems.length === totalItems.length && totalItems.length > 0) {
                // 모든 검사항목 완료
                alert('모든 검사항목이 완료되었습니다!');
                // 검사 카테고리에 따라 적절한 페이지로 이동
                if (currentInspection.category === 'incoming') {
                    showPage('incoming');
                } else if (currentInspection.category === 'mixing') {
                    showPage('mixing');
                }
            }
        }

        async function saveParticleSize(itemName) {
            const item = currentItems.find(i => i.name === itemName);
            const particleData = {};

            const meshIds = ['180', '150', '106', '75', '45', '45M'];

                item.particleSpecs.forEach((spec, index) => {
                const val1 = document.getElementById(`${itemName}_${index}_1`).value;
                const val2 = document.getElementById(`${itemName}_${index}_2`).value;

                // Accept single measurement as valid: use whichever value is provided
                if (val1 || val2) {
                    const num1 = val1 ? parseFloat(val1) : null;
                    const num2 = val2 ? parseFloat(val2) : null;
                    let avg;
                    if (num1 !== null && num2 !== null) {
                        avg = ((num1 + num2) / 2).toFixed(1);
                    } else {
                        avg = (num1 !== null ? num1 : num2).toFixed(1);
                    }

                    const result = (parseFloat(avg) >= spec.min_value && parseFloat(avg) <= spec.max_value) ? '합격' : '불합격';

                    particleData[meshIds[index]] = {
                        val1: val1 || null,
                        val2: val2 || null,
                        avg: avg,
                        result: result
                    };
                }
            });

            try {
                const response = await fetch(`${API_BASE}/api/save-particle-size`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        powderName: currentInspection.powderName,
                        lotNumber: currentInspection.lotNumber,
                        particleData: particleData
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const resultDiv = document.getElementById('result-' + itemName);
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `결과: <span class="badge ${data.result === 'PASS' ? 'pass' : 'fail'}">${data.result}</span>`;

                    // 완료된 항목에 추가
                    if (!currentInspection.completedItems.includes(itemName)) {
                        currentInspection.completedItems.push(itemName);
                    }

                    // 저장 성공 후 검사 진행 상황 다시 로드
                    setTimeout(async () => {
                        await checkInspectionCompletion();
                        renderInspectionItems();
                    }, 1500);
                } else {
                    alert('저장 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // 입도분석 로컬 판정: 결과만 표시하고 최종저장 버튼 활성화
        function judgeParticleSize(itemName) {
            const item = currentItems.find(i => i.name === itemName);
            if (!item) return alert('항목 정보를 찾을 수 없습니다.');

            const particleData = {};
            const meshIds = ['180', '150', '106', '75', '45', '45M'];
            let overallResult = 'PASS';
            let anyMeasured = false;

            // Build detailed result HTML
            let detailHtml = '<div style="display:flex;flex-direction:column;gap:8px;">';

            item.particleSpecs.forEach((spec, index) => {
                const meshLabel = spec.mesh_size || meshIds[index] || (`mesh${index}`);
                const val1El = document.getElementById(`${itemName}_${index}_1`);
                const val2El = document.getElementById(`${itemName}_${index}_2`);
                const val1 = val1El ? val1El.value : '';
                const val2 = val2El ? val2El.value : '';

                if (val1 || val2) {
                    anyMeasured = true;
                    const num1 = val1 ? parseFloat(val1) : null;
                    const num2 = val2 ? parseFloat(val2) : null;
                    let avg;
                    if (num1 !== null && num2 !== null) {
                        avg = ((num1 + num2) / 2).toFixed(1);
                    } else {
                        avg = (num1 !== null ? num1 : num2).toFixed(1);
                    }

                    const meshResult = (parseFloat(avg) >= spec.min_value && parseFloat(avg) <= spec.max_value) ? '합격' : '불합격';
                    if (meshResult === '불합격') overallResult = 'FAIL';

                    particleData[meshIds[index]] = { val1: val1 || null, val2: val2 || null, avg: avg, result: meshResult };

                    detailHtml += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:#fff;border-radius:6px;border:1px solid #eee;">\
                        <div style="font-weight:600">${meshLabel}</div>\
                        <div style="font-size:0.95em;color:#444">평균: ${avg}%</div>\
                        <div><span class="badge ${meshResult === '합격' ? 'pass' : 'fail'}">${meshResult}</span></div>\
                    </div>`;
                } else {
                    // not measured
                    particleData[meshIds[index]] = { val1: val1 || null, val2: val2 || null, avg: null, result: '미측정' };
                    detailHtml += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:#fff;border-radius:6px;border:1px solid #eee;">\
                        <div style="font-weight:600">${meshLabel}</div>\
                        <div style="font-size:0.95em;color:#999">평균: -</div>\
                        <div><span class="badge" style="background:#bdbdbd;">미측정</span></div>\
                    </div>`;
                    overallResult = 'FAIL';
                }
            });

            detailHtml += '</div>';

            if (!anyMeasured) return alert('유효한 측정값이 없습니다.');

            const resultDiv = document.getElementById('result-' + itemName);
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `전체결과: <span class="badge ${overallResult === 'PASS' ? 'pass' : 'fail'}">${overallResult}</span><div style="margin-top:10px;">${detailHtml}</div>`;

            pendingResults[itemName] = { particleData: particleData, result: overallResult };
            const finalBtn = document.getElementById(`final-save-${itemName}`);
            if (finalBtn) finalBtn.disabled = (overallResult !== 'PASS');
        }

        // 입도분석 최종 저장
        async function finalSaveParticleSize(itemName) {
            const pending = pendingResults[itemName];
            if (!pending) return alert('먼저 판정(검증)을 수행하세요.');

            if (pending.result !== 'PASS') return alert('모든 항목이 합격일 때만 최종저장할 수 있습니다.');

            try {
                const response = await fetch(`${API_BASE}/api/save-particle-size`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        powderName: currentInspection.powderName,
                        lotNumber: currentInspection.lotNumber,
                        particleData: pending.particleData
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const resultDiv = document.getElementById('result-' + itemName);
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `결과: <span class="badge ${data.result === 'PASS' ? 'pass' : 'fail'}">${data.result}</span>`;

                    if (!currentInspection.completedItems.includes(itemName)) {
                        currentInspection.completedItems.push(itemName);
                    }

                    delete pendingResults[itemName];
                    const finalBtn = document.getElementById(`final-save-${itemName}`);
                    if (finalBtn) finalBtn.disabled = true;

                    setTimeout(async () => {
                        await checkInspectionCompletion();
                        renderInspectionItems();
                    }, 500);
                } else {
                    alert('저장 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 검사 결과 조회
        // ============================================
        async function loadPowderListForSearch() {
            try {
                const response = await fetch(`${API_BASE}/api/powder-list`);
                const data = await response.json();

                const select = document.getElementById('searchPowderName');
                select.innerHTML = '<option value="">전체</option>';

                if (data.success) {
                    data.data.forEach(powder => {
                        const option = document.createElement('option');
                        option.value = powder;
                        option.textContent = powder;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('분말 목록 로딩 실패:', error);
            }
        }

        const searchFormElement = document.getElementById('searchForm');


        if (searchFormElement) {


            searchFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const category = document.getElementById('searchCategory').value;
            const powderName = document.getElementById('searchPowderName').value;
            const lotNumber = document.getElementById('searchLotNumber').value;
            const dateFrom = document.getElementById('searchDateFrom').value;
            const dateTo = document.getElementById('searchDateTo').value;

            try {
                const params = new URLSearchParams();
                if (category) params.append('category', category);
                if (powderName) params.append('powderName', powderName);
                if (lotNumber) params.append('lotNumber', lotNumber);
                if (dateFrom) params.append('dateFrom', dateFrom);
                if (dateTo) params.append('dateTo', dateTo);

                const response = await fetch(`${API_BASE}/api/search-results?${params}`);
                const data = await response.json();

                const resultsDiv = document.getElementById('searchResults');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('category')}</th><th>${t('powderName')}</th><th>${t('lotNumber')}</th><th>${t('inspector')}</th><th>${t('inspectionTime')}</th><th>${t('inspectionType')}</th><th>${t('finalResult')}</th><th>${t('detail')}</th></tr>`;

                    data.data.forEach(item => {
                        const badgeClass = item.final_result === 'PASS' ? 'pass' : 'fail';
                        const categoryBadge = item.category === 'incoming'
                            ? `<span class="badge" style="background: #2196F3;">${t('incoming')}</span>`
                            : `<span class="badge" style="background: #FF9800;">${t('mixing')}</span>`;

                        html += `
                            <tr>
                                <td>${categoryBadge}</td>
                                <td>${item.powder_name}</td>
                                <td>${item.lot_number}</td>
                                <td>${item.inspector}</td>
                                <td>${item.inspection_time}</td>
                                <td>${item.inspection_type}</td>
                                <td><span class="badge ${badgeClass}">${item.final_result}</span></td>
                                <td><button class="btn" onclick="viewDetail('${item.powder_name}', '${item.lot_number}')">${t('view')}</button></td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = `<div class="empty-message">${t('noResults')}</div>`;
                }
            } catch (error) {
                document.getElementById('searchResults').innerHTML = `<div class="empty-message">오류: ${error.message}</div>`;
            }
        });
        }

        async function viewDetail(powderName, lotNumber) {
            try {
                const response = await fetch(`${API_BASE}/api/inspection-detail/${powderName}/${lotNumber}`);
                const data = await response.json();

                if (data.success) {
                    renderDetailPage(data.data);
                    showPage('detail');
                } else {
                    alert('상세 정보 로딩 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        function renderDetailPage(detail) {
            const container = document.getElementById('detailContent');

            let html = `
                <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 20px;">
                    <h2 style="margin-bottom: 15px;">${detail.powder_name} - LOT ${detail.lot_number}</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div>
                            <p style="opacity: 0.9;">${t('inspector')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${detail.inspector}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9;">${t('inspectionTime')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${detail.inspection_time}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9;">${t('inspectionType')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${detail.inspection_type}</p>
                        </div>
                    </div>
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                        <p style="font-size: 1.1em; opacity: 0.9;">${t('finalResult')}</p>
                        <p style="font-size: 1.5em; font-weight: 700; margin-top: 5px;">${detail.final_result}</p>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">${t('inspectionDetails')}</div>
                    <div class="detail-grid">
            `;

            // 각 검사 항목 표시
            const items = [
                { nameKey: 'flowRate', prefix: 'flow_rate', unit: 's/50g' },
                { nameKey: 'apparentDensity', prefix: 'apparent_density', unit: 'g/cm³' },
                { nameKey: 'cContent', prefix: 'c_content', unit: '%' },
                { nameKey: 'cuContent', prefix: 'cu_content', unit: '%' },
                { nameKey: 'moisture', prefix: 'moisture', unit: '%' },
                { nameKey: 'ash', prefix: 'ash', unit: '%' },
                { nameKey: 'sinterChangeRate', prefix: 'sinter_change_rate', unit: '%' },
                { nameKey: 'sinterStrength', prefix: 'sinter_strength', unit: 'MPa' },
                { nameKey: 'formingStrength', prefix: 'forming_strength', unit: 'N' },
                { nameKey: 'formingLoad', prefix: 'forming_load', unit: 'MPa' }
            ];

            items.forEach(item => {
                const avg = detail[`${item.prefix}_avg`];
                const result = detail[`${item.prefix}_result`];

                if (avg !== null && avg !== undefined && avg !== '') {
                    const badgeClass = result === 'PASS' ? 'pass' : 'fail';
                    html += `
                        <div class="detail-item">
                            <h4>${t(item.nameKey)}</h4>
                            <p>${t('average')}: <strong>${avg} ${item.unit}</strong></p>
                            <p>${t('result')}: <span class="badge ${badgeClass}">${result}</span></p>
                        </div>
                    `;
                }
            });
            // 입도분석 표시 (있으면)
            if (detail.particleSizeSpecs && detail.particleSizeSpecs.length > 0) {
                html += `</div></div><div class="card" style="margin-top:16px;"><div class="card-title">${t('particleSize')}</div>`;
                html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;">';

                // helper: mesh label -> column suffix
                const meshKey = (mesh) => {
                    if (!mesh) return mesh;
                    const s = mesh.toString().trim();
                    if (s.startsWith('-')) return '45m';
                    // extract digits
                    const m = s.match(/(\d+)/);
                    if (!m) return s.replace(/[^a-zA-Z0-9]/g, '');
                    const num = m[1];
                    if (num === '45' && s.startsWith('-')) return '45m';
                    return num;
                };

                detail.particleSizeSpecs.forEach((spec) => {
                    const key = meshKey(spec.mesh_size);
                    const avgField = `particle_size_${key}_avg`;
                    const resField = `particle_size_${key}_result`;

                    const avg = detail[avgField];
                    const res = detail[resField];
                    const displayRes = res === 'PASS' ? '합격' : (res === 'FAIL' ? '불합격' : (res || '-'));

                    html += `
                        <div style="padding:12px;border-radius:8px;background:#fafafa;border:1px solid #eee;">
                            <div style="font-weight:700;margin-bottom:6px;">${spec.mesh_size}</div>
                            <div style="font-size:0.95em;color:#444;">규격: ${spec.min_value}~${spec.max_value}%</div>
                            <div style="margin-top:8px;">평균: <strong>${avg !== null && avg !== undefined ? avg : '-' }%</strong></div>
                            <div>판정: <span class="badge ${res === 'PASS' ? 'pass' : (res === 'FAIL' ? 'fail' : '')}">${displayRes}</span></div>
                        </div>
                    `;
                });

                html += '</div></div>';
            } else {
                html += '</div></div>';
            }
            container.innerHTML = html;
        }

        // ============================================
        // 관리자 페이지 함수들
        // ============================================

        // 관리자 페이지 로드
        async function loadAdminPage() {
            await loadPowderSpecs();
            // particlePowderSelect 관련 DOM이 없는 경우(템플릿에 미구현) 로딩 건너뛰기
            if (document.getElementById('particlePowderSelect')) {
                await loadParticlePowderList();
            }
            await loadInspectors();
            await loadOperators();
            await loadProductRecipes();
        }

        // ============================================
        // 분말 사양 관리
        // ============================================

        async function loadPowderSpecs() {
            try {
                const response = await fetch(`${API_BASE}/api/admin/powder-spec`);
                const data = await response.json();

                const listDiv = document.getElementById('powderList');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('category')}</th><th>${t('powderName')}</th><th>${t('configuredItems')}</th><th>${t('action')}</th></tr>`;

                    data.data.forEach(spec => {
                        const categoryBadge = spec.category === 'incoming'
                            ? `<span class="badge" style="background: #2196F3;">${t('incoming')}</span>`
                            : `<span class="badge" style="background: #FF9800;">${t('mixing')}</span>`;

                        const activeItems = [];
                        if (spec.flow_rate_type !== '비활성' && (spec.flow_rate_min || spec.flow_rate_max)) activeItems.push(t('flowRate'));
                        if (spec.apparent_density_type !== '비활성' && (spec.apparent_density_min || spec.apparent_density_max)) activeItems.push(t('apparentDensity'));
                        if (spec.c_content_type !== '비활성' && (spec.c_content_min || spec.c_content_max)) activeItems.push(t('cContent'));
                        if (spec.cu_content_type !== '비활성' && (spec.cu_content_min || spec.cu_content_max)) activeItems.push(t('cuContent'));
                        if (spec.moisture_type !== '비활성' && (spec.moisture_min || spec.moisture_max)) activeItems.push(t('moisture'));
                        if (spec.ash_type !== '비활성' && (spec.ash_min || spec.ash_max)) activeItems.push(t('ash'));
                        if (spec.sinter_change_rate_type !== '비활성' && (spec.sinter_change_rate_min || spec.sinter_change_rate_max)) activeItems.push(t('sinterChangeRate'));
                        if (spec.sinter_strength_type !== '비활성' && (spec.sinter_strength_min || spec.sinter_strength_max)) activeItems.push(t('sinterStrength'));
                        if (spec.forming_strength_type !== '비활성' && (spec.forming_strength_min || spec.forming_strength_max)) activeItems.push(t('formingStrength'));
                        if (spec.forming_load_type !== '비활성' && (spec.forming_load_min || spec.forming_load_max)) activeItems.push(t('formingLoad'));
                        if (spec.particle_size_type !== '비활성') activeItems.push(t('particleSize'));

                        html += `
                            <tr>
                                <td>${categoryBadge}</td>
                                <td><strong>${spec.powder_name}</strong></td>
                                <td>${activeItems.join(', ') || t('noConfig')}</td>
                                <td>
                                    <button class="btn secondary" onclick="editPowderSpec(${spec.id})" style="padding: 8px 12px; margin-right: 5px;">${t('edit')}</button>
                                    <button class="btn danger" onclick="deletePowderSpec(${spec.id}, '${spec.powder_name}')" style="padding: 8px 12px;">${t('delete')}</button>
                                </td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noPowders')}</div>`;
                }
            } catch (error) {
                console.error('분말 목록 로딩 실패:', error);
            }
        }

        function showAddPowderForm() {
            document.getElementById('powderFormTitle').textContent = t('addPowder');
            document.getElementById('powderSpecId').value = '';
            document.getElementById('powderForm').reset();
            document.getElementById('adminPowderCategory').value = '';  // 선택하게 함
            document.getElementById('adminPowderNameInput').style.display = 'none';
            document.getElementById('adminPowderNameSelect').style.display = 'none';
            document.getElementById('adminPowderNameInput').removeAttribute('required');
            document.getElementById('adminPowderNameSelect').removeAttribute('required');

            // 폼 리셋 후 모든 검사 항목을 '비활성'으로 초기화하고 입도필드 표시여부 결정
            setTimeout(() => {
                // 타입을 모두 비활성으로 설정
                const typeIds = ['flowRateType','apparentDensityType','cContentType','cuContentType','moistureType','ashType','sinterChangeRateType','sinterStrengthType','formingStrengthType','formingLoadType','particleSizeType'];
                typeIds.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.value = '비활성';
                });

                // 모든 min/max 입력 필드 초기화
                const fieldIds = ['flowRateMin','flowRateMax','apparentDensityMin','apparentDensityMax','cContentMin','cContentMax','cuContentMin','cuContentMax','moistureMin','moistureMax','ashMin','ashMax','sinterChangeRateMin','sinterChangeRateMax','sinterStrengthMin','sinterStrengthMax','formingStrengthMin','formingStrengthMax','formingLoadMin','formingLoadMax','particle_180_min','particle_180_max','particle_150_min','particle_150_max','particle_106_min','particle_106_max','particle_75_min','particle_75_max','particle_45_min','particle_45_max','particle_45m_min','particle_45m_max'];
                fieldIds.forEach(id => {
                    const f = document.getElementById(id);
                    if (f) f.value = '';
                });

                toggleParticleInputs();
            }, 0);

            document.getElementById('powderFormContainer').style.display = 'block';
        }

        function toggleParticleInputs() {
            const particleType = document.getElementById('particleSizeType').value;
            const particleInputs = document.getElementById('particleSizeInputs');

            if (particleType === '비활성') {
                particleInputs.style.display = 'none';
            } else {
                particleInputs.style.display = 'block';
            }
        }

        async function handlePowderCategoryChange() {
            const category = document.getElementById('adminPowderCategory').value;
            const inputField = document.getElementById('adminPowderNameInput');
            const selectField = document.getElementById('adminPowderNameSelect');

            if (category === 'incoming') {
                // 수입검사: 직접 입력
                inputField.style.display = 'block';
                selectField.style.display = 'none';
                inputField.setAttribute('required', 'required');
                selectField.removeAttribute('required');
                inputField.value = '';
            } else if (category === 'mixing') {
                // 배합검사: 배합규격서의 제품명에서 선택
                selectField.style.display = 'block';
                inputField.style.display = 'none';
                selectField.setAttribute('required', 'required');
                inputField.removeAttribute('required');

                // 배합규격서 제품명 목록 로드
                try {
                    const response = await fetch(`${API_BASE}/api/admin/recipes`);
                    const data = await response.json();

                    let options = '<option value="">' + t('selectPlaceholder') + '</option>';
                    if (data.success && data.data.length > 0) {
                        // 중복 제거를 위해 Set 사용
                        const productNames = [...new Set(data.data.map(p => p.product_name))];
                        productNames.forEach(name => {
                            options += `<option value="${name}">${name}</option>`;
                        });
                    }
                    selectField.innerHTML = options;
                } catch (error) {
                    console.error('Failed to load product names:', error);
                }
            } else {
                // 미선택 상태
                inputField.style.display = 'none';
                selectField.style.display = 'none';
                inputField.removeAttribute('required');
                selectField.removeAttribute('required');
            }
        }

        function hidePowderForm() {
            document.getElementById('powderFormContainer').style.display = 'none';
            document.getElementById('powderForm').reset();
        }

        async function editPowderSpec(specId) {
            try {
                const response = await fetch(`${API_BASE}/api/admin/powder-spec`);
                const data = await response.json();

                if (data.success) {
                    const spec = data.data.find(s => s.id === specId);
                    if (spec) {
                        document.getElementById('powderFormTitle').textContent = t('editPowder');
                        document.getElementById('powderSpecId').value = spec.id;

                        // 검사구분 먼저 설정
                        document.getElementById('adminPowderCategory').value = spec.category || 'incoming';

                        // 검사구분에 따라 필드 변경
                        await handlePowderCategoryChange();

                        // 분말명 설정
                        if (spec.category === 'incoming') {
                            document.getElementById('adminPowderNameInput').value = spec.powder_name;
                        } else if (spec.category === 'mixing') {
                            document.getElementById('adminPowderNameSelect').value = spec.powder_name;
                        }

                        // 각 항목 값 채우기
                        document.getElementById('flowRateMin').value = spec.flow_rate_min || '';
                        document.getElementById('flowRateMax').value = spec.flow_rate_max || '';
                        document.getElementById('flowRateType').value = spec.flow_rate_type || '일상';

                        document.getElementById('apparentDensityMin').value = spec.apparent_density_min || '';
                        document.getElementById('apparentDensityMax').value = spec.apparent_density_max || '';
                        document.getElementById('apparentDensityType').value = spec.apparent_density_type || '일상';

                        document.getElementById('cContentMin').value = spec.c_content_min || '';
                        document.getElementById('cContentMax').value = spec.c_content_max || '';
                        document.getElementById('cContentType').value = spec.c_content_type || '일상';

                        document.getElementById('cuContentMin').value = spec.cu_content_min || '';
                        document.getElementById('cuContentMax').value = spec.cu_content_max || '';
                        document.getElementById('cuContentType').value = spec.cu_content_type || '일상';

                        document.getElementById('moistureMin').value = spec.moisture_min || '';
                        document.getElementById('moistureMax').value = spec.moisture_max || '';
                        document.getElementById('moistureType').value = spec.moisture_type || '일상';

                        document.getElementById('ashMin').value = spec.ash_min || '';
                        document.getElementById('ashMax').value = spec.ash_max || '';
                        document.getElementById('ashType').value = spec.ash_type || '일상';

                        document.getElementById('sinterChangeRateMin').value = spec.sinter_change_rate_min || '';
                        document.getElementById('sinterChangeRateMax').value = spec.sinter_change_rate_max || '';
                        document.getElementById('sinterChangeRateType').value = spec.sinter_change_rate_type || '일상';

                        document.getElementById('sinterStrengthMin').value = spec.sinter_strength_min || '';
                        document.getElementById('sinterStrengthMax').value = spec.sinter_strength_max || '';
                        document.getElementById('sinterStrengthType').value = spec.sinter_strength_type || '일상';

                        document.getElementById('formingStrengthMin').value = spec.forming_strength_min || '';
                        document.getElementById('formingStrengthMax').value = spec.forming_strength_max || '';
                        document.getElementById('formingStrengthType').value = spec.forming_strength_type || '일상';

                        document.getElementById('formingLoadMin').value = spec.forming_load_min || '';
                        document.getElementById('formingLoadMax').value = spec.forming_load_max || '';
                        document.getElementById('formingLoadType').value = spec.forming_load_type || '일상';

                        document.getElementById('particleSizeType').value = spec.particle_size_type || '일상';
                        toggleParticleInputs();

                        // 입도분석 규격 로드
                        if (spec.particle_size_type !== '비활성') {
                            const particleResponse = await fetch(`${API_BASE}/api/admin/particle-size?powder_name=${encodeURIComponent(spec.powder_name)}`);
                            const particleData = await particleResponse.json();

                            if (particleData.success && particleData.data.length > 0) {
                                particleData.data.forEach(ps => {
                                    let meshId = '';
                                    if (ps.mesh_size === '+180 um') meshId = '180';
                                    else if (ps.mesh_size === '+150 um') meshId = '150';
                                    else if (ps.mesh_size === '+106 um') meshId = '106';
                                    else if (ps.mesh_size === '+75 um') meshId = '75';
                                    else if (ps.mesh_size === '+45 um') meshId = '45';
                                    else if (ps.mesh_size === '-45 um') meshId = '45m';

                                    if (meshId) {
                                        document.getElementById(`particle_${meshId}_min`).value = ps.min_value || '';
                                        document.getElementById(`particle_${meshId}_max`).value = ps.max_value || '';
                                    }
                                });
                            }
                        }

                        document.getElementById('powderFormContainer').style.display = 'block';
                    }
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        const powderFormElement = document.getElementById('powderForm');


        if (powderFormElement) {


            powderFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const specId = document.getElementById('powderSpecId').value;
            const category = document.getElementById('adminPowderCategory').value;

            // 검사구분에 따라 분말명 가져오기
            let powderName;
            if (category === 'incoming') {
                powderName = document.getElementById('adminPowderNameInput').value;
            } else if (category === 'mixing') {
                powderName = document.getElementById('adminPowderNameSelect').value;
            }

            const powderData = {
                powder_name: powderName,
                category: category,
                flow_rate_min: document.getElementById('flowRateMin').value || null,
                flow_rate_max: document.getElementById('flowRateMax').value || null,
                flow_rate_type: document.getElementById('flowRateType').value,
                apparent_density_min: document.getElementById('apparentDensityMin').value || null,
                apparent_density_max: document.getElementById('apparentDensityMax').value || null,
                apparent_density_type: document.getElementById('apparentDensityType').value,
                c_content_min: document.getElementById('cContentMin').value || null,
                c_content_max: document.getElementById('cContentMax').value || null,
                c_content_type: document.getElementById('cContentType').value,
                cu_content_min: document.getElementById('cuContentMin').value || null,
                cu_content_max: document.getElementById('cuContentMax').value || null,
                cu_content_type: document.getElementById('cuContentType').value,
                moisture_min: document.getElementById('moistureMin').value || null,
                moisture_max: document.getElementById('moistureMax').value || null,
                moisture_type: document.getElementById('moistureType').value,
                ash_min: document.getElementById('ashMin').value || null,
                ash_max: document.getElementById('ashMax').value || null,
                ash_type: document.getElementById('ashType').value,
                sinter_change_rate_min: document.getElementById('sinterChangeRateMin').value || null,
                sinter_change_rate_max: document.getElementById('sinterChangeRateMax').value || null,
                sinter_change_rate_type: document.getElementById('sinterChangeRateType').value,
                sinter_strength_min: document.getElementById('sinterStrengthMin').value || null,
                sinter_strength_max: document.getElementById('sinterStrengthMax').value || null,
                sinter_strength_type: document.getElementById('sinterStrengthType').value,
                forming_strength_min: document.getElementById('formingStrengthMin').value || null,
                forming_strength_max: document.getElementById('formingStrengthMax').value || null,
                forming_strength_type: document.getElementById('formingStrengthType').value,
                forming_load_min: document.getElementById('formingLoadMin').value || null,
                forming_load_max: document.getElementById('formingLoadMax').value || null,
                forming_load_type: document.getElementById('formingLoadType').value,
                particle_size_type: document.getElementById('particleSizeType').value
            };

            try {
                const url = specId ? `${API_BASE}/api/admin/powder-spec/${specId}` : `${API_BASE}/api/admin/powder-spec`;
                const method = specId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(powderData)
                });

                const data = await response.json();

                if (data.success) {
                    // 입도분석 데이터 저장
                    const particleType = document.getElementById('particleSizeType').value;
                    if (particleType !== '비활성') {
                        const particleSpecs = [];
                        const meshSizes = [
                            { id: '180', name: '+180 um' },
                            { id: '150', name: '+150 um' },
                            { id: '106', name: '+106 um' },
                            { id: '75', name: '+75 um' },
                            { id: '45', name: '+45 um' },
                            { id: '45m', name: '-45 um' }
                        ];

                        meshSizes.forEach(mesh => {
                            const minVal = document.getElementById(`particle_${mesh.id}_min`).value;
                            const maxVal = document.getElementById(`particle_${mesh.id}_max`).value;
                            if (minVal && maxVal) {
                                particleSpecs.push({
                                    powder_name: powderName,
                                    mesh_size: mesh.name,
                                    min_value: parseFloat(minVal),
                                    max_value: parseFloat(maxVal)
                                });
                            }
                        });

                        // 입도분석 규격 저장
                        if (particleSpecs.length > 0) {
                            await fetch(`${API_BASE}/api/admin/particle-size/bulk`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    powder_name: powderName,
                                    specs: particleSpecs
                                })
                            });
                        }
                    }

                    alert('저장되었습니다.');
                    hidePowderForm();
                    loadPowderSpecs();
                    loadParticlePowderList();
                    // 검사 페이지의 분말 목록도 갱신
                    loadPowderList('incoming');
                    loadPowderList('mixing');
                } else {
                    alert('저장 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        });
        }

        async function deletePowderSpec(specId, powderName) {
            if (!confirm(`'${powderName}' 분말을 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE}/api/admin/powder-spec/${specId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('삭제되었습니다.');
                    loadPowderSpecs();
                    loadParticlePowderList();
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 입도분석 규격 관리
        // ============================================

        async function loadParticlePowderList() {
            try {
                const response = await fetch(`${API_BASE}/api/powder-list`);
                const data = await response.json();

                const select = document.getElementById('particlePowderSelect');
                if (!select) {
                    console.warn('particlePowderSelect 요소를 찾을 수 없습니다.');
                    return;
                }

                select.innerHTML = '<option value="">분말을 선택하세요</option>';

                if (data.success) {
                    data.data.forEach(powder => {
                        const option = document.createElement('option');
                        option.value = powder;
                        option.textContent = powder;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('분말 목록 로딩 실패:', error);
            }
        }

        async function loadParticleSpecs() {
            const powderName = document.getElementById('particlePowderSelect').value;

            if (!powderName) {
                document.getElementById('particleList').innerHTML = `<div class="empty-message">${t('selectPowderPlaceholder')}</div>`;
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/admin/particle-size/${powderName}`);
                const data = await response.json();

                const listDiv = document.getElementById('particleList');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('meshSize')}</th><th>${t('minValue')} (%)</th><th>${t('maxValue')} (%)</th><th>${t('action')}</th></tr>`;

                    data.data.forEach(spec => {
                        html += `
                            <tr>
                                <td>${spec.mesh_size}</td>
                                <td>${spec.min_value}</td>
                                <td>${spec.max_value}</td>
                                <td>
                                    <button class="btn secondary" onclick="editParticleSpec(${spec.id})" style="padding: 8px 12px; margin-right: 5px;">${t('edit')}</button>
                                    <button class="btn danger" onclick="deleteParticleSpec(${spec.id}, '${spec.mesh_size}')" style="padding: 8px 12px;">${t('delete')}</button>
                                </td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noParticleSpecs')}</div>`;
                }
            } catch (error) {
                console.error('입도분석 규격 로딩 실패:', error);
            }
        }

        function showAddParticleForm() {
            const powderName = document.getElementById('particlePowderSelect').value;
            if (!powderName) {
                alert('먼저 분말을 선택하세요.');
                return;
            }

            document.getElementById('particleFormTitle').textContent = t('addParticleSpec');
            document.getElementById('particleSpecId').value = '';
            document.getElementById('particleForm').reset();
            document.getElementById('particleFormContainer').style.display = 'block';
        }

        function hideParticleForm() {
            document.getElementById('particleFormContainer').style.display = 'none';
            document.getElementById('particleForm').reset();
        }

        async function editParticleSpec(specId) {
            try {
                const powderName = document.getElementById('particlePowderSelect').value;
                const response = await fetch(`${API_BASE}/api/admin/particle-size/${powderName}`);
                const data = await response.json();

                if (data.success) {
                    const spec = data.data.find(s => s.id === specId);
                    if (spec) {
                        document.getElementById('particleFormTitle').textContent = t('editParticleSpec');
                        document.getElementById('particleSpecId').value = spec.id;
                        document.getElementById('particleMeshSize').value = spec.mesh_size;
                        document.getElementById('particleMinValue').value = spec.min_value;
                        document.getElementById('particleMaxValue').value = spec.max_value;
                        document.getElementById('particleFormContainer').style.display = 'block';
                    }
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        const particleFormElement = document.getElementById('particleForm');


        if (particleFormElement) {


            particleFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const specId = document.getElementById('particleSpecId').value;
            const powderName = document.getElementById('particlePowderSelect').value;
            const particleData = {
                powder_name: powderName,
                mesh_size: document.getElementById('particleMeshSize').value,
                min_value: document.getElementById('particleMinValue').value,
                max_value: document.getElementById('particleMaxValue').value
            };

            try {
                const url = specId ? `${API_BASE}/api/admin/particle-size/${specId}` : `${API_BASE}/api/admin/particle-size`;
                const method = specId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(particleData)
                });

                const data = await response.json();

                if (data.success) {
                    alert('저장되었습니다.');
                    hideParticleForm();
                    loadParticleSpecs();
                } else {
                    alert('저장 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        });
        }

        async function deleteParticleSpec(specId, meshSize) {
            if (!confirm(`'${meshSize}' 규격을 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE}/api/admin/particle-size/${specId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('삭제되었습니다.');
                    loadParticleSpecs();
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 검사자 관리
        // ============================================

        async function loadInspectors() {
            try {
                const response = await fetch(`${API_BASE}/api/admin/inspector`);
                const data = await response.json();

                const listDiv = document.getElementById('inspectorList');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('inspectorName')}</th><th>${t('action')}</th></tr>`;

                    data.data.forEach(inspector => {
                        html += `
                            <tr>
                                <td>${inspector.name}</td>
                                <td>
                                    <button class="btn danger" onclick="deleteInspector(${inspector.id}, '${inspector.name}')" style="padding: 8px 12px;">${t('delete')}</button>
                                </td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noInspectors')}</div>`;
                }
            } catch (error) {
                console.error('검사자 목록 로딩 실패:', error);
            }
        }

        async function addInspector() {
            const name = document.getElementById('newInspectorName').value.trim();

            if (!name) {
                alert('검사자 이름을 입력하세요.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/admin/inspector`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });

                const data = await response.json();

                if (data.success) {
                    alert('추가되었습니다.');
                    document.getElementById('newInspectorName').value = '';
                    loadInspectors();
                } else {
                    alert('추가 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        async function deleteInspector(inspectorId, name) {
            if (!confirm(`'${name}' 검사자를 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE}/api/admin/inspector/${inspectorId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('삭제되었습니다.');
                    loadInspectors();
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 작업자 관리
        // ============================================

        async function loadOperators() {
            try {
                const response = await fetch(`${API_BASE}/api/admin/operator`);
                const data = await response.json();

                const listDiv = document.getElementById('operatorList');

                if (data.success && data.data.length > 0) {
                    let html = `<table><tr><th>${t('operatorName')}</th><th>${t('action')}</th></tr>`;

                    data.data.forEach(operator => {
                        html += `
                            <tr>
                                <td>${operator.name}</td>
                                <td>
                                    <button class="btn danger" onclick="deleteOperator(${operator.id}, '${operator.name}')" style="padding: 8px 12px;">${t('delete')}</button>
                                </td>
                            </tr>
                        `;
                    });

                    html += '</table>';
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noOperators')}</div>`;
                }
            } catch (error) {
                console.error('작업자 목록 로딩 실패:', error);
            }
        }

        async function addOperator() {
            const name = document.getElementById('newOperatorName').value.trim();

            if (!name) {
                alert('작업자 이름을 입력하세요.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/admin/operator`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });

                const data = await response.json();

                if (data.success) {
                    alert('추가되었습니다.');
                    document.getElementById('newOperatorName').value = '';
                    loadOperators();
                } else {
                    alert('추가 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        async function deleteOperator(operatorId, name) {
            if (!confirm(`'${name}' 작업자를 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE}/api/admin/operator/${operatorId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('삭제되었습니다.');
                    loadOperators();
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // Recipe(배합 규격서) 관리
        // ============================================

        let recipeLineCount = 0;

        async function loadProductRecipes() {
            try {
                const response = await fetch(`${API_BASE}/api/admin/recipes`);
                const data = await response.json();

                const listDiv = document.getElementById('productList');

                if (data.success && data.data.length > 0) {
                    let html = '';

                    data.data.forEach(product => {
                        const totalRatio = product.recipes.reduce((sum, r) => sum + parseFloat(r.ratio || 0), 0);

                        html += `
                            <div class="card" style="margin-bottom: 15px; border-left: 4px solid #667eea;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div>
                                        <h3 style="margin: 0;">${product.product_name}</h3>
                                        ${product.product_code ? `<small style="color: #666;">${t('productCode')}: ${product.product_code}</small>` : ''}
                                    </div>
                                    <div style="display: flex; gap: 10px;">
                                        <button class="btn primary" onclick="editProduct('${product.product_name}')" style="padding: 8px 12px;">${t('edit')}</button>
                                        <button class="btn danger" onclick="deleteProduct('${product.product_name}')" style="padding: 8px 12px;">${t('delete')}</button>
                                    </div>
                                </div>

                                <table style="width: 100%; font-size: 0.9em;">
                                    <tr>
                                        <th>${t('powderName')}</th>
                                        <th>${t('category')}</th>
                                        <th>${t('ratio')} (%)</th>
                                        <th>${t('tolerance')} (%)</th>
                                    </tr>`;

                        product.recipes.forEach(recipe => {
                            const categoryBadge = recipe.powder_category === 'incoming'
                                ? `<span class="badge" style="background: #2196F3;">${t('incoming')}</span>`
                                : `<span class="badge" style="background: #FF9800;">${t('mixing')}</span>`;

                            html += `
                                <tr>
                                    <td>${recipe.powder_name}</td>
                                    <td>${categoryBadge}</td>
                                    <td>${formatTwo(recipe.ratio)}%</td>
                                    <td>±${formatTwo(recipe.tolerance_percent)}%</td>
                                </tr>`;
                        });

                        html += `
                                    <tr style="font-weight: bold; background: #f5f5f5;">
                                        <td>${t('totalRatio')}</td>
                                        <td colspan="3">${totalRatio.toFixed(2)}%</td>
                                    </tr>
                                </table>
                            </div>`;
                    });

                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = `<div class="empty-message">${t('noProducts')}</div>`;
                }
            } catch (error) {
                console.error('Recipe 목록 로딩 실패:', error);
            }
        }

        async function showAddProductForm() {
            document.getElementById('productFormTitle').textContent = t('addNewProduct');
            document.getElementById('recipeProductName').value = '';
            document.getElementById('recipeProductName').readOnly = false; // 새 제품 추가 시 수정 가능
            document.getElementById('recipeProductCode').value = '';
            document.getElementById('recipeLines').innerHTML = '';
            recipeLineCount = 0;

            // 초기 Recipe 라인 1개 추가 (await로 분말 목록 로드 완료 대기)
            await addRecipeLine();

            document.getElementById('productFormContainer').style.display = 'block';
        }

        function hideProductForm() {
            document.getElementById('productFormContainer').style.display = 'none';
        }

        async function editProduct(productName) {
            try {
                // 제품의 Recipe 데이터 가져오기
                const response = await fetch(`${API_BASE}/api/admin/recipes?product_name=${encodeURIComponent(productName)}`);
                const data = await response.json();

                if (!data.success || !data.data || data.data.length === 0) {
                    alert('제품 정보를 찾을 수 없습니다.');
                    return;
                }

                const product = data.data[0]; // 첫 번째 제품 (제품명으로 필터링했으므로 1개만 있음)

                // 폼 제목 변경
                document.getElementById('productFormTitle').textContent = t('editProduct');

                // 제품 정보 입력
                document.getElementById('recipeProductName').value = product.product_name;
                document.getElementById('recipeProductName').readOnly = true; // 제품명은 수정 불가
                document.getElementById('recipeProductCode').value = product.product_code || '';

                // 기존 Recipe 라인 제거
                document.getElementById('recipeLines').innerHTML = '';
                recipeLineCount = 0;

                // 각 Recipe 라인 추가 및 데이터 채우기
                for (const recipe of product.recipes) {
                    await addRecipeLine();

                    // 방금 추가된 라인 (마지막 라인)
                    const lines = document.querySelectorAll('.recipe-line');
                    const lastLine = lines[lines.length - 1];

                    // 데이터 채우기
                    lastLine.querySelector('.recipe-powder-name').value = recipe.powder_name;
                    lastLine.querySelector('.recipe-ratio').value = formatTwo(recipe.ratio);
                    lastLine.querySelector('.recipe-tolerance').value = formatTwo(recipe.tolerance_percent);

                    // Main 분말 체크
                    if (recipe.is_main) {
                        lastLine.querySelector('.recipe-is-main').checked = true;
                    }
                }

                // 폼 표시
                document.getElementById('productFormContainer').style.display = 'block';

            } catch (error) {
                alert('오류: ' + error.message);
                console.error('Edit product error:', error);
            }
        }

        async function addRecipeLine() {
            const container = document.getElementById('recipeLines');
            const lineId = recipeLineCount++;

            // 수입검사용 분말 목록 가져오기
            let powderOptions = '<option value="">' + t('selectPlaceholder') + '</option>';
            try {
                const response = await fetch(`${API_BASE}/api/powders?category=incoming`);
                const data = await response.json();
                if (data.success && data.powders) {
                    data.powders.forEach(powder => {
                        powderOptions += `<option value="${powder.powder_name}">${powder.powder_name}</option>`;
                    });
                }
            } catch (error) {
                console.error('Failed to load powder list:', error);
            }

            const lineHtml = `
                <div class="recipe-line" data-line-id="${lineId}" style="display: grid; grid-template-columns: 2fr 1fr 1fr 80px 60px; gap: 10px; margin-bottom: 10px; padding: 10px; background: white; border-radius: 5px;">
                    <div class="form-group">
                        <label>${t('powderName')} *</label>
                        <select class="recipe-powder-name" required>
                            ${powderOptions}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t('ratio')} (%) *</label>
                        <input type="number" step="0.01" class="recipe-ratio" required placeholder="60.00">
                    </div>
                    <div class="form-group">
                        <label>${t('tolerance')} (%) *</label>
                        <input type="number" step="0.01" class="recipe-tolerance" required placeholder="0.50" value="0.50">
                    </div>
                    <div class="form-group" style="display: flex; align-items: end;">
                        <label style="display: flex; align-items: center; gap: 5px; margin-bottom: 0; cursor: pointer;">
                            <input type="checkbox" class="recipe-is-main" value="${lineId}">
                            <span style="font-size: 0.9em;">Main</span>
                        </label>
                    </div>
                    <div style="display: flex; align-items: end;">
                        <button type="button" class="btn danger" onclick="removeRecipeLine(${lineId})" style="padding: 10px; width: 100%;">×</button>
                    </div>
                </div>`;

            container.insertAdjacentHTML('beforeend', lineHtml);

            // 방금 추가된 체크박스에 이벤트 리스너 추가
            const newCheckbox = container.querySelector(`[data-line-id="${lineId}"] .recipe-is-main`);
            if (newCheckbox) {
                newCheckbox.addEventListener('change', function() {
                    const checkedBoxes = document.querySelectorAll('.recipe-is-main:checked');
                    if (checkedBoxes.length > 2) {
                        this.checked = false;
                        alert('Main 분말은 최대 2개까지만 선택할 수 있습니다.');
                    }
                });
            }
        }

        function removeRecipeLine(lineId) {
            const line = document.querySelector(`[data-line-id="${lineId}"]`);
            if (line) line.remove();
        }

        const productFormElement = document.getElementById('productForm');


        if (productFormElement) {


            productFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const productName = document.getElementById('recipeProductName').value.trim();
            const productCode = document.getElementById('recipeProductCode').value.trim();

            // 제품명 확인
            if (!productName) {
                alert('제품명을 입력하세요.');
                return;
            }

            // Recipe 라인 수집
            const lines = document.querySelectorAll('.recipe-line');

            // Recipe 라인 존재 확인
            if (lines.length === 0) {
                alert('배합 구성을 최소 1개 이상 추가하세요.');
                return;
            }

            const recipes = [];

            // Main 분말 확인 (체크박스로 변경, 최대 2개)
            const mainCheckboxes = document.querySelectorAll('.recipe-is-main:checked');
            const mainLineIds = Array.from(mainCheckboxes).map(cb => cb.value);

            lines.forEach(line => {
                const powderName = line.querySelector('.recipe-powder-name').value.trim();
                const ratio = line.querySelector('.recipe-ratio').value;
                const tolerance = line.querySelector('.recipe-tolerance').value;
                const lineId = line.getAttribute('data-line-id');
                const isMain = mainLineIds.includes(lineId);

                // 필수 항목 확인
                if (powderName && ratio && tolerance) {
                    recipes.push({
                        product_name: productName,
                        product_code: productCode,
                        powder_name: powderName,
                        powder_category: 'incoming',  // 항상 수입검사용 분말
                        ratio: parseFloat(ratio),
                        target_weight: null,
                        tolerance_percent: parseFloat(tolerance),
                        is_main: isMain
                    });
                }
            });

            // 유효한 Recipe가 있는지 확인
            if (recipes.length === 0) {
                alert('분말명과 비율을 입력하세요.');
                return;
            }

            // 비율 합계 확인
            const totalRatio = recipes.reduce((sum, r) => sum + r.ratio, 0);
            if (Math.abs(totalRatio - 100) > 0.1) {
                alert(`배합 비율의 합계가 100%가 아닙니다. 현재: ${totalRatio.toFixed(1)}%\n\n각 분말의 비율을 조정하여 합계가 100%가 되도록 해주세요.`);
                return;
            }

            try {
                // 수정 모드인지 확인 (제품명 필드가 readOnly이면 수정 모드)
                const isEditMode = document.getElementById('recipeProductName').readOnly;

                if (isEditMode) {
                    // 수정 모드: 기존 Recipe 삭제 후 새로 추가
                    const deleteResponse = await fetch(`${API_BASE}/api/admin/recipe/product/${encodeURIComponent(productName)}`, {
                        method: 'DELETE'
                    });

                    const deleteData = await deleteResponse.json();
                    if (!deleteData.success) {
                        throw new Error('기존 Recipe 삭제 실패: ' + deleteData.message);
                    }
                }

                // 각 Recipe를 개별적으로 저장
                for (const recipe of recipes) {
                    const response = await fetch(`${API_BASE}/api/admin/recipe`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(recipe)
                    });

                    const data = await response.json();
                    if (!data.success) {
                        throw new Error(data.message);
                    }
                }

                alert(isEditMode ? '수정되었습니다.' : '저장되었습니다.');
                hideProductForm();
                loadProductRecipes();
            } catch (error) {
                alert('저장 실패: ' + error.message);
            }
        });
        }

        async function deleteProduct(productName) {
            if (!confirm(`'${productName}' 제품의 모든 Recipe를 삭제하시겠습니까?`)) return;

            try {
                const response = await fetch(`${API_BASE}/api/admin/recipe/product/${encodeURIComponent(productName)}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('삭제되었습니다.');
                    loadProductRecipes();
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 배합 작업 (Blending Work)
        // ============================================

        let currentRecipe = null;
        let currentProductCode = '';

        async function loadBlendingPage() {
            // 목록 먼저 보이도록 폼 숨김
            hideBlendingForm();

            await loadProductsForBlending();
            await loadOperatorList();
            await generateAndSetBatchLot();

                // 작업지시서에서 시작한 경우 정보 자동 입력
                checkAndFillBlendingOrderInfo();

                // 이 화면에서도 작업지시서 목록을 보여주고 작업 시작 가능
                if (typeof loadBlendingOrdersForBlending === 'function') {
                    await loadBlendingOrdersForBlending();
                }
        }

        // --------------------------------------------
        // 배합검사 페이지: 완료된 배합작업 목록 로드
        // --------------------------------------------
        async function loadMixingPage() {
            try {
                const response = await fetch(`${API_BASE}/api/blending/works?status=completed`);
                const data = await response.json();

                const container = document.getElementById('mixingCompletedList');
                if (!container) return;

                if (!data.success || !data.works || data.works.length === 0) {
                    container.innerHTML = '<div class="empty-message">완료된 배합작업이 없습니다.</div>';
                    return;
                }

                let html = '<table class="data-table" style="width:100%"><thead><tr><th>작업지시번호</th><th>제품명</th><th>배합 LOT</th><th>작업자</th><th>완료시간</th><th>작업</th></tr></thead><tbody>';

                data.works.forEach(work => {
                    const endTime = work.end_time ? new Date(work.end_time).toLocaleString('ko-KR') : '-';
                    html += `
                        <tr>
                            <td>${work.work_order || '-'}</td>
                            <td>${work.product_name}</td>
                            <td><strong>${work.batch_lot}</strong></td>
                            <td>${work.operator || '-'}</td>
                            <td>${endTime}</td>
                            <td>
                                <button class="btn primary" onclick="startBlendingInspectionFromMixing('${work.batch_lot}', '${work.product_name}')" style="padding:6px 10px;">배합검사</button>
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (err) {
                console.error('mixing 목록 로딩 실패:', err);
                const container = document.getElementById('mixingCompletedList');
                if (container) container.innerHTML = '<div class="empty-message">목록을 불러올 수 없습니다.</div>';
            }
        }

        // 배합검사 시작 (mixing 페이지에서 클릭)
        function startBlendingInspectionFromMixing(batchLot, productName) {
            // 바로 검사 시작 API 호출과 검사 페이지 노출
            startInspection(productName, batchLot, '일상점검', '', 'mixing');
        }

        function checkAndFillBlendingOrderInfo() {
            const orderId = sessionStorage.getItem('blendingOrderId');
            const productName = sessionStorage.getItem('blendingOrderProduct');
            const workOrderNumber = sessionStorage.getItem('blendingOrderNumber');

            if (orderId && productName && workOrderNumber) {
                // 제품명 자동 선택
                const productSelect = document.getElementById('blendingProductName');
                if (productSelect) {
                    // 옵션에서 일치하는 값이 있으면 선택
                    let found = false;
                    for (let i = 0; i < productSelect.options.length; i++) {
                        if (productSelect.options[i].value === productName) {
                            productSelect.selectedIndex = i;
                            found = true;
                            break;
                        }
                    }
                    // 값이 없더라도 value에 설정
                    if (!found) {
                        productSelect.value = productName;
                    }

                    // change 이벤트 트리거 (다른 핸들러들도 반응하게끔)
                    productSelect.dispatchEvent(new Event('change', { bubbles: true }));

                    // 제품 선택 시 Recipe 자동 로드 (안전하게 호출)
                    if (typeof loadRecipeForProduct === 'function') {
                        loadRecipeForProduct();
                    }
                }

                // 작업지시번호 표시 (읽기 전용으로)
                const workOrderInput = document.getElementById('blendingWorkOrder');
                if (workOrderInput) {
                    workOrderInput.value = workOrderNumber;
                    workOrderInput.setAttribute('readonly', 'readonly');
                    workOrderInput.style.background = '#f0f0f0';
                }

                // sessionStorage 클리어 (한 번만 사용)
                // sessionStorage.removeItem('blendingOrderId');
                // sessionStorage.removeItem('blendingOrderProduct');
                // sessionStorage.removeItem('blendingOrderNumber');
            }
        }

        function hideBlendingForm() {
            const card = document.getElementById('blendingFormCard');
            if (card) card.style.display = 'none';
        }

        function showBlendingForm() {
            const card = document.getElementById('blendingFormCard');
            if (card) card.style.display = 'block';
        }

        async function loadProductsForBlending() {
            try {
                const response = await fetch(`${API_BASE}/api/blending/products`);
                const data = await response.json();

                const select = document.getElementById('blendingProductName');
                select.innerHTML = '<option value="">선택하세요</option>';

                if (data.success && data.data.length > 0) {
                    data.data.forEach(product => {
                        const option = document.createElement('option');
                        option.value = product.product_name;
                        option.dataset.productCode = product.product_code || '';
                        option.textContent = product.product_name;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('제품 목록 로딩 실패:', error);
            }
        }

        async function loadOperatorList() {
            try {
                const response = await fetch(`${API_BASE}/api/operator-list`);
                const data = await response.json();

                const select = document.getElementById('blendingOperator');
                select.innerHTML = '<option value="">선택하세요</option>';

                if (data.success) {
                    data.data.forEach(operator => {
                        const option = document.createElement('option');
                        option.value = operator;
                        option.textContent = operator;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('작업자 목록 로딩 실패:', error);
            }
        }

        async function generateAndSetBatchLot() {
            try {
                const response = await fetch(`${API_BASE}/api/blending/generate-lot`);
                const data = await response.json();

                if (data.success) {
                    document.getElementById('blendingBatchLot').value = data.batch_lot;
                }
            } catch (error) {
                console.error('배합 LOT 생성 실패:', error);
            }
        }

        async function loadRecipeForProduct() {
            const select = document.getElementById('blendingProductName');
            const productName = select.value;

            if (!productName) {
                document.getElementById('recipePreview').style.display = 'none';
                currentRecipe = null;
                return;
            }

            // 제품 코드 저장
            const selectedOption = select.options[select.selectedIndex];
            currentProductCode = selectedOption.dataset.productCode || '';

            try {
                const response = await fetch(`${API_BASE}/api/blending/recipe/${encodeURIComponent(productName)}`);
                const data = await response.json();

                if (data.success && data.data.length > 0) {
                    currentRecipe = data.data;
                    renderRecipePreview(data.data);
                } else {
                    alert('해당 제품의 Recipe가 없습니다.');
                    currentRecipe = null;
                }
            } catch (error) {
                alert('Recipe 로딩 실패: ' + error.message);
                currentRecipe = null;
            }
        }

        function renderRecipePreview(recipes) {
            const container = document.getElementById('recipePreviewContent');
            const blendingWeight = parseFloat(document.getElementById('blendingTargetWeight').value) || 0;

            // Main 분말들 찾기 (최대 2개)
            const mainRecipes = recipes.filter(r => r.is_main);

            // Main 분말 각각의 중량 가져오기
            let mainWeights = {};
            let totalMainWeight = 0;
            mainRecipes.forEach((recipe, index) => {
                const weightInput = document.getElementById(`mainPowderWeight_${index}`);
                const weight = weightInput ? parseFloat(weightInput.value) || 0 : 0;
                mainWeights[recipe.powder_name] = weight;
                totalMainWeight += weight;
            });

            // Main 분말 비율 합계
            const totalMainRatio = mainRecipes.reduce((sum, r) => sum + r.ratio, 0);

            let html = '<table style="width: 100%; font-size: 0.9em;">';
            html += `<tr>
                <th>${t('powderName')}</th>
                <th>${t('category')}</th>
                <th>${t('ratio')} (%)</th>
                <th>${t('calculatedWeight')} (kg)</th>
            </tr>`;

            recipes.forEach(recipe => {
                let calculatedWeight = '-';
                if (recipe.is_main) {
                    // Main 분말: 개별적으로 선택한 중량
                    const weight = mainWeights[recipe.powder_name] || 0;
                    if (weight > 0) {
                        calculatedWeight = formatNumber(weight.toFixed(2));
                    }
                } else if (totalMainWeight > 0 && totalMainRatio > 0) {
                    // 다른 분말: 전체 main 분말 중량 × (해당 분말 비율 / 전체 main 분말 비율)
                    const weight = totalMainWeight * (recipe.ratio / totalMainRatio);
                    calculatedWeight = formatNumber(weight.toFixed(2));
                }

                const categoryBadge = recipe.powder_category === 'incoming'
                    ? `<span class="badge" style="background: #2196F3;">${t('incoming')}</span>`
                    : `<span class="badge" style="background: #FF9800;">${t('mixing')}</span>`;

                const mainBadge = recipe.is_main ? ' <span class="badge" style="background: #FF5722; font-size: 0.75em;">MAIN</span>' : '';

                html += `<tr>
                    <td>${recipe.powder_name}${mainBadge}</td>
                    <td>${categoryBadge}</td>
                    <td>${formatTwo(recipe.ratio)}%</td>
                    <td>${calculatedWeight}</td>
                </tr>`;
            });

            html += '</table>';
            container.innerHTML = html;
            document.getElementById('recipePreview').style.display = 'block';

            // Main 분말 중량 선택 UI 생성
            renderMainPowderWeightSelectors(mainRecipes);
        }

        function renderMainPowderWeightSelectors(mainRecipes) {
            const container = document.getElementById('mainPowderWeightsContainer');

            if (!mainRecipes || mainRecipes.length === 0) {
                container.style.display = 'none';
                container.innerHTML = '';
                return;
            }

            let html = '';
            mainRecipes.forEach((recipe, index) => {
                html += `
                    <div class="form-group">
                        <label>${recipe.powder_name} 중량 (ton) *</label>
                        <select id="mainPowderWeight_${index}" class="main-powder-weight-select" data-powder-name="${recipe.powder_name}" required>
                            <option value="">선택하세요</option>
                            <option value="1000">1 ton (1,000 kg)</option>
                            <option value="2000">2 ton (2,000 kg)</option>
                            <option value="3000">3 ton (3,000 kg)</option>
                            <option value="4000">4 ton (4,000 kg)</option>
                            <option value="5000">5 ton (5,000 kg)</option>
                        </select>
                    </div>
                `;
            });

            // 합계 검증 메시지 영역
            if (mainRecipes.length > 1) {
                html += `
                    <div id="mainPowderWeightValidation" style="padding: 10px; margin-bottom: 10px; background: #fff3cd; border-radius: 5px; font-size: 0.9em;">
                        <strong>⚠️ 중요:</strong> Main 분말 중량의 합계가 배합중량과 일치해야 합니다.
                        <div id="mainPowderWeightSum" style="margin-top: 5px; font-weight: bold;"></div>
                    </div>
                `;
            }

            container.innerHTML = html;
            container.style.display = 'block';

            // Main 분말 중량 변경 시 이벤트 리스너 추가
            const weightSelects = container.querySelectorAll('.main-powder-weight-select');
            weightSelects.forEach(select => {
                select.addEventListener('change', () => {
                    updateMainPowderWeightValidation(mainRecipes);
                    if (currentRecipe) {
                        renderRecipePreview(currentRecipe);
                    }
                });
            });

            updateMainPowderWeightValidation(mainRecipes);
        }

        function updateMainPowderWeightValidation(mainRecipes) {
            if (!mainRecipes || mainRecipes.length <= 1) return;

            const blendingWeight = parseFloat(document.getElementById('blendingTargetWeight').value) || 0;
            let totalMainWeight = 0;
            let allSelected = true;

            mainRecipes.forEach((recipe, index) => {
                const select = document.getElementById(`mainPowderWeight_${index}`);
                const weight = select ? parseFloat(select.value) || 0 : 0;
                totalMainWeight += weight;
                if (!select || !select.value) {
                    allSelected = false;
                }
            });

            const sumDiv = document.getElementById('mainPowderWeightSum');
            if (sumDiv && blendingWeight > 0 && allSelected) {
                const isValid = totalMainWeight === blendingWeight;
                sumDiv.innerHTML = `
                    Main 분말 합계: ${formatNumber(totalMainWeight)} kg / 배합중량: ${formatNumber(blendingWeight)} kg
                    ${isValid ? '<span style="color: green;">✓ 일치</span>' : '<span style="color: red;">✗ 불일치</span>'}
                `;
                sumDiv.style.color = isValid ? 'green' : 'red';
            } else if (sumDiv) {
                sumDiv.innerHTML = '';
            }
        }

        // 목표 총 중량 변경 시 Recipe 미리보기 업데이트
        const blendingTargetWeightElement = document.getElementById('blendingTargetWeight');

        if (blendingTargetWeightElement) {

            blendingTargetWeightElement.addEventListener('change', () => {
            if (currentRecipe) {
                const mainRecipes = currentRecipe.filter(r => r.is_main);
                updateMainPowderWeightValidation(mainRecipes);
                renderRecipePreview(currentRecipe);
            }
        });
        }

        // 배합 작업 폼 제출
        const blendingFormElement = document.getElementById('blendingForm');

        if (blendingFormElement) {

            blendingFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const productName = document.getElementById('blendingProductName').value;
            const workOrder = document.getElementById('blendingWorkOrder').value;
            const batchLot = document.getElementById('blendingBatchLot').value;
            const targetWeight = document.getElementById('blendingTargetWeight').value;
            const operator = document.getElementById('blendingOperator').value;

            // 작업지시서 ID 가져오기 (있는 경우)
            const orderId = sessionStorage.getItem('blendingOrderId');

            if (!currentRecipe || currentRecipe.length === 0) {
                alert('제품을 선택하고 레시피를 확인해주세요.');
                return;
            }

            // Main 분말 중량 검증
            const mainRecipes = currentRecipe.filter(r => r.is_main);
            let mainPowderWeights = {};
            let totalMainWeight = 0;

            for (let i = 0; i < mainRecipes.length; i++) {
                const select = document.getElementById(`mainPowderWeight_${i}`);
                if (!select || !select.value) {
                    alert(`${mainRecipes[i].powder_name}의 중량을 선택해주세요.`);
                    return;
                }
                const weight = parseFloat(select.value);
                mainPowderWeights[mainRecipes[i].powder_name] = weight;
                totalMainWeight += weight;
            }

            // Main 분말이 2개 이상일 때 합계 검증
            if (mainRecipes.length > 1) {
                const blendingWeight = parseFloat(targetWeight);
                if (totalMainWeight !== blendingWeight) {
                    alert(`Main 분말 중량의 합계(${formatNumber(totalMainWeight)} kg)가 배합중량(${formatNumber(blendingWeight)} kg)과 일치하지 않습니다.\n\n각 Main 분말의 중량을 조정해주세요.`);
                    return;
                }
            }

            try {
                const requestBody = {
                    product_name: productName,
                    product_code: currentProductCode,
                    batch_lot: batchLot,
                    target_total_weight: parseFloat(targetWeight),
                    operator: operator,
                    main_powder_weights: mainPowderWeights  // Main 분말 중량 정보 추가
                };

                // 작업지시서 ID 추가 (있는 경우)
                if (orderId) {
                    requestBody.work_order_id = parseInt(orderId);
                }

                // 작업지시 번호 추가 (있는 경우)
                if (workOrder && !workOrder.includes('(자동)')) {
                    requestBody.work_order = workOrder;
                }

                const response = await fetch(`${API_BASE}/api/blending/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (data.success) {
                    alert(`배합 작업이 시작되었습니다.\n배합 LOT: ${data.batch_lot}`);
                    // 원재료 투입 페이지로 이동
                    loadMaterialInputPage(data.work_id);
                } else {
                    alert('작업 시작 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        });
        }

        // ============================================
        // 원재료 투입 (Material Input)
        // ============================================

        let currentBlendingWork = null;
        let currentBlendingRecipes = [];
        let currentMaterialInputs = [];

        async function loadMaterialInputPage(workId) {
            try {
                const response = await fetch(`${API_BASE}/api/blending/work/${workId}`);
                const data = await response.json();

                if (data.success) {
                    currentBlendingWork = data.work;
                    currentBlendingRecipes = data.recipes;
                    currentMaterialInputs = data.material_inputs;

                    renderMaterialInputPage();
                    showPage('material-input');
                } else {
                    alert('배합 작업 로딩 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        function renderMaterialInputPage() {
            // 작업 정보 표시
            document.getElementById('materialWorkOrder').textContent = currentBlendingWork.work_order;
            document.getElementById('materialProductName').textContent = currentBlendingWork.product_name;
            document.getElementById('materialBatchLot').textContent = currentBlendingWork.batch_lot;

            const inputCount = currentMaterialInputs.length;
            const totalCount = currentBlendingRecipes.length;
            document.getElementById('materialProgress').textContent = `${inputCount}/${totalCount}`;

            // 원재료 투입 목록을 표 형태로 렌더링
            const container = document.getElementById('materialInputList');

            let html = `
                <table class="material-input-table" style="width: 100%; border-collapse: collapse; font-size: 1.1em;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">분말명</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">LOT 번호</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">목표중량<br>(kg)</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">허용최소<br>(kg)</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">허용최대<br>(kg)</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">계량중량<br>(kg)</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">판정</th>
                            <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">상태</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            currentBlendingRecipes.forEach((recipe, index) => {
                // 이미 투입된 원재료인지 확인
                const existingInput = currentMaterialInputs.find(input => input.powder_name === recipe.powder_name);
                const isCompleted = !!existingInput;

                // 허용 범위 계산
                // calculated_weight는 백엔드에서 Main 분말 중량을 고려하여 계산됨
                const targetWeight = recipe.calculated_weight;
                const tolerancePercent = recipe.tolerance_percent;
                const minWeight = (targetWeight * (1 - tolerancePercent / 100)).toFixed(2);
                const maxWeight = (targetWeight * (1 + tolerancePercent / 100)).toFixed(2);

                const rowBg = isCompleted ? '#f0f8f0' : '#ffffff';

                html += `<tr style="background: ${rowBg}; border-bottom: 2px solid #eee;">`;

                // 분말명
                html += `<td style="padding: 15px; border: 1px solid #ddd; font-weight: 600; font-size: 1.1em;">${recipe.powder_name}</td>`;

                // LOT 번호 (최대 2개: 기본 1개, 필요시 추가)
                if (isCompleted) {
                    html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${existingInput.material_lot}</td>`;
                } else {
                    html += `
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <div style="display:flex; gap:8px; align-items:center;">
                                <select id="lot-${recipe.id}-1" onchange="validateLotSelection('${recipe.id}', '${recipe.powder_name}', 1)"
                                    data-powder="${recipe.powder_name}" data-category="${recipe.powder_category}"
                                    style="flex:1; padding: 8px; font-size: 1em; border: 2px solid #ddd; border-radius: 5px;">
                                    <option value="">LOT 1 선택</option>
                                    <option value="">로딩 중...</option>
                                </select>
                                <button type="button" class="btn secondary" id="add-lot-btn-${recipe.id}" onclick="showSecondLot('${recipe.id}')" style="padding:6px 10px;">+ 추가</button>
                            </div>
                            <div id="lot-${recipe.id}-2-container" style="margin-top:8px; display:none;">
                                <select id="lot-${recipe.id}-2" onchange="validateLotSelection('${recipe.id}', '${recipe.powder_name}', 2)"
                                    data-powder="${recipe.powder_name}" data-category="${recipe.powder_category}"
                                    style="width:100%; padding:8px; font-size:1em; border:2px solid #ddd; border-radius:5px;">
                                    <option value="">LOT 2 선택</option>
                                    <option value="">로딩 중...</option>
                                </select>
                            </div>
                        </td>
                    `;
                }

                // 목표중량
                html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; font-size: 1.2em; font-weight: 600;">${formatNumber(targetWeight.toFixed(2))}</td>`;

                // 허용최소
                html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; font-size: 1.1em; color: #ff9800;">${formatNumber(minWeight)}</td>`;

                // 허용최대
                html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; font-size: 1.1em; color: #ff9800;">${formatNumber(maxWeight)}</td>`;

                // 계량중량 (Main 분말: 1~5ton 선택, 다른 분말: 최대 2개 입력)
                if (isCompleted) {
                    html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; font-size: 1.2em; font-weight: 600;">${formatNumber(existingInput.actual_weight)}</td>`;
                } else if (recipe.is_main) {
                    // Main 분말: 1~5ton 선택 (배합 작업 시 설정한 중량으로 초기화)
                    const mainWeight = currentBlendingWork.main_powder_weights && currentBlendingWork.main_powder_weights[recipe.powder_name]
                        ? currentBlendingWork.main_powder_weights[recipe.powder_name]
                        : '';
                    html += `
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <select id="weight-${recipe.id}-1"
                                onchange="checkWeightJudgement('${recipe.id}')"
                                style="width:100%; padding: 10px; font-size: 1.1em; border: 2px solid #ddd; border-radius: 5px; text-align: center;">
                                <option value="">중량 선택</option>
                                <option value="1000" ${mainWeight === 1000 ? 'selected' : ''}>1 ton (1,000 kg)</option>
                                <option value="2000" ${mainWeight === 2000 ? 'selected' : ''}>2 ton (2,000 kg)</option>
                                <option value="3000" ${mainWeight === 3000 ? 'selected' : ''}>3 ton (3,000 kg)</option>
                                <option value="4000" ${mainWeight === 4000 ? 'selected' : ''}>4 ton (4,000 kg)</option>
                                <option value="5000" ${mainWeight === 5000 ? 'selected' : ''}>5 ton (5,000 kg)</option>
                            </select>
                        </td>
                    `;
                } else {
                    // 다른 분말: 기존 방식 (최대 2개 입력)
                    html += `
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <input type="number" step="0.1" id="weight-${recipe.id}-1"
                                onchange="checkWeightJudgement('${recipe.id}')"
                                placeholder="중량1 (kg)"
                                style="width:100%; padding: 8px; font-size: 1.1em; border: 2px solid #ddd; border-radius: 5px; text-align: center; margin-bottom:4px;">
                            <input type="number" step="0.1" id="weight-${recipe.id}-2"
                                style="width:100%; padding: 8px; font-size: 1.1em; border: 2px solid #ddd; border-radius: 5px; text-align: center; display:none;"
                                placeholder="중량2 (kg)"
                                onchange="checkWeightJudgement('${recipe.id}')">
                        </td>
                    `;
                }

                // 판정
                if (isCompleted) {
                    const isValid = existingInput.is_valid;
                    const judgementBadge = isValid
                        ? '<span style="background: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px; font-weight: 600;">✓ 적정</span>'
                        : '<span style="background: #f44336; color: white; padding: 8px 16px; border-radius: 5px; font-weight: 600;">✗ 부적정</span>';
                    html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${judgementBadge}</td>`;
                } else {
                    html += `
                        <td style="padding: 15px; border: 1px solid #ddd; text-align: center;">
                            <button onclick="judgeWeight('${recipe.id}', ${targetWeight}, ${tolerancePercent})"
                                id="judge-${recipe.id}"
                                disabled
                                style="background: #2196F3; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 600;">
                                판정
                            </button>
                            <div id="judgement-${recipe.id}" style="margin-top: 5px; font-weight: 600;"></div>
                        </td>
                    `;
                }

                // 상태
                if (isCompleted) {
                    html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">
                        <span style="background: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px; font-weight: 600;">✓ 투입완료</span>
                    </td>`;
                } else {
                    html += `
                        <td style="padding: 15px; border: 1px solid #ddd; text-align: center;">
                            <button onclick="saveMaterialInput('${recipe.id}', '${recipe.powder_name}', ${targetWeight}, ${tolerancePercent}, '${recipe.powder_category}')"
                                id="save-${recipe.id}"
                                disabled
                                style="background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 1em; font-weight: 600;">
                                저장
                            </button>
                            <div id="status-${recipe.id}" style="margin-top: 5px; font-size: 0.9em;"></div>
                        </td>
                    `;
                }

                html += `</tr>`;

                // LOT 검증 메시지를 표시할 행 추가 (투입 대기중인 경우만)
                if (!isCompleted) {
                    html += `
                        <tr id="validation-row-${recipe.id}" style="display: none; background: #fff3cd;">
                            <td colspan="8" style="padding: 10px; border: 1px solid #ddd;">
                                <div id="validation-${recipe.id}" style="font-weight: 600;"></div>
                            </td>
                        </tr>
                    `;
                }
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;

            // 투입 대기 중인 원재료의 LOT 목록 로드
            currentBlendingRecipes.forEach(recipe => {
                const existingInput = currentMaterialInputs.find(input => input.powder_name === recipe.powder_name);
                if (!existingInput) {
                    loadCompletedLots(recipe.id, recipe.powder_name, recipe.powder_category);
                }
            });

            // 완료 버튼 활성화 확인 - 모든 원재료가 투입되고 모두 적정 판정인 경우만
            const allCompleted = currentMaterialInputs.length === currentBlendingRecipes.length;
            const allValid = currentMaterialInputs.every(input => input.is_valid);
            document.getElementById('completeBlendingBtn').disabled = !(allCompleted && allValid);

            if (allCompleted && !allValid) {
                alert('⚠️ 부적정 판정된 원재료가 있습니다. 모든 원재료가 적정 판정되어야 작업을 완료할 수 있습니다.');
            }
        }

        async function loadCompletedLots(recipeId, powderName, category) {
            try {
                        const lotSelect1 = document.getElementById(`lot-${recipeId}-1`);
                        const lotSelect2 = document.getElementById(`lot-${recipeId}-2`);
                        if (!lotSelect1) return;

                        const response = await fetch(`${API_BASE}/api/completed-lots/${encodeURIComponent(powderName)}?category=${category}`);
                        const data = await response.json();

                        if (data.success && data.lots && data.lots.length > 0) {
                            const optionsHtml = ['<option value="">LOT 선택</option>'];
                            data.lots.forEach(lot => {
                                const inspectionDate = new Date(lot.inspection_time).toLocaleDateString('ko-KR');
                                optionsHtml.push(`<option value="${lot.lot_number}">${lot.lot_number} (검사일: ${inspectionDate})</option>`);
                            });

                            lotSelect1.innerHTML = optionsHtml.join('');
                            if (lotSelect2) lotSelect2.innerHTML = optionsHtml.join('');
                        } else {
                            lotSelect1.innerHTML = '<option value="">사용 가능한 LOT 없음</option>';
                            if (lotSelect2) lotSelect2.innerHTML = '<option value="">사용 가능한 LOT 없음</option>';
                        }
            } catch (error) {
                console.error('LOT 목록 로딩 실패:', error);
                        const lotSelect1 = document.getElementById(`lot-${recipeId}-1`);
                        const lotSelect2 = document.getElementById(`lot-${recipeId}-2`);
                        if (lotSelect1) lotSelect1.innerHTML = '<option value="">로딩 실패</option>';
                        if (lotSelect2) lotSelect2.innerHTML = '<option value="">로딩 실패</option>';
            }
        }

        // show second lot and weight input for a recipe
        function showSecondLot(recipeId) {
            const lot2Container = document.getElementById(`lot-${recipeId}-2-container`);
            const weight2 = document.getElementById(`weight-${recipeId}-2`);
            const addBtn = document.getElementById(`add-lot-btn-${recipeId}`);
            const lot1 = document.getElementById(`lot-${recipeId}-1`);
            const lot2 = document.getElementById(`lot-${recipeId}-2`);

            // 기존 선택값 저장
            const lot1Value = lot1 ? lot1.value : '';

            if (lot2Container) lot2Container.style.display = 'block';
            if (weight2) weight2.style.display = 'block';
            if (addBtn) addBtn.style.display = 'none';

            // lot2의 옵션을 lot1과 동일하게 복사 (새로 로드하지 않음)
            if (lot1 && lot2) {
                lot2.innerHTML = lot1.innerHTML;
                // 기존 선택값 복원
                lot1.value = lot1Value;
            }
        }

        // 중량 입력 시 판정 버튼 활성화
        function checkWeightJudgement(recipeId) {
                    const weight1 = parseFloat(document.getElementById(`weight-${recipeId}-1`)?.value || 0);
                    const weight2El = document.getElementById(`weight-${recipeId}-2`);
                    const weight2 = weight2El ? parseFloat(weight2El.value || 0) : 0;
                    const judgeBtn = document.getElementById(`judge-${recipeId}`);

                    if (judgeBtn) {
                        const total = (isNaN(weight1) ? 0 : weight1) + (isNaN(weight2) ? 0 : weight2);
                        judgeBtn.disabled = !(total > 0);
                    }
        }

        // 판정 버튼 클릭 시 적정/부적정 판단
        function judgeWeight(recipeId, targetWeight, tolerancePercent) {
                    const weight1 = parseFloat(document.getElementById(`weight-${recipeId}-1`)?.value || 0);
                    const weight2 = parseFloat(document.getElementById(`weight-${recipeId}-2`)?.value || 0);
                    const judgementDiv = document.getElementById(`judgement-${recipeId}`);
                    const saveBtn = document.getElementById(`save-${recipeId}`);
                    const lot1 = document.getElementById(`lot-${recipeId}-1`);
                    const lot2 = document.getElementById(`lot-${recipeId}-2`);

                    const actualWeight = (isNaN(weight1) ? 0 : weight1) + (isNaN(weight2) ? 0 : weight2);
                    if (!actualWeight || actualWeight <= 0) {
                        alert('계량중량을 입력해주세요.');
                        return;
                    }

                    // 허용 범위 계산 (합산 기준)
                    const minWeight = targetWeight * (1 - tolerancePercent / 100);
                    const maxWeight = targetWeight * (1 + tolerancePercent / 100);

                    // 판정
                    const isValid = actualWeight >= minWeight && actualWeight <= maxWeight;

                    if (isValid) {
                        judgementDiv.innerHTML = '<span style="color: #4CAF50; font-size: 1.1em;">✓ 적정</span>';
                        judgementDiv.setAttribute('data-judgement', 'pass');

                        // LOT 중 하나라도 선택되어 있으면 저장 버튼 활성화
                        if ((lot1 && lot1.value) || (lot2 && lot2.value)) {
                            if (saveBtn) saveBtn.disabled = false;
                        }
                    } else {
                        const deviation = ((actualWeight - targetWeight) / targetWeight * 100).toFixed(2);
                        judgementDiv.innerHTML = `<span style="color: #f44336; font-size: 1.1em;">✗ 부적정<br>(${deviation > 0 ? '+' : ''}${deviation}%)</span>`;
                        judgementDiv.setAttribute('data-judgement', 'fail');
                        if (saveBtn) saveBtn.disabled = true;

                        alert(`⚠️ 허용범위를 벗어났습니다.\n허용범위: ${formatNumber(minWeight.toFixed(2))} ~ ${formatNumber(maxWeight.toFixed(2))} kg\n입력값(합계): ${formatNumber(actualWeight)} kg`);
                    }
        }

        // validate single lot selection (idx: 1 or 2)
        async function validateLotSelection(recipeId, expectedPowder, idx) {
            const lotSelect = document.getElementById(`lot-${recipeId}-${idx}`);
            const lotNumber = lotSelect ? lotSelect.value.trim() : '';
            const validationDiv = document.getElementById(`validation-${recipeId}`);
            const validationRow = document.getElementById(`validation-row-${recipeId}`);
            const saveBtn = document.getElementById(`save-${recipeId}`);
            const judgementDiv = document.getElementById(`judgement-${recipeId}`);

            // if no lot selected and other lot also empty -> hide
            const other = document.getElementById(`lot-${recipeId}-${idx === 1 ? 2 : 1}`);
            const otherVal = other ? other.value.trim() : '';

            if (!lotNumber && !otherVal) {
                if (validationDiv) validationDiv.innerHTML = '';
                if (validationRow) validationRow.style.display = 'none';
                if (saveBtn) saveBtn.disabled = true;
                return;
            }

            // validate each selected lot independently (if provided)
            try {
                if (lotNumber) {
                    const response = await fetch(`${API_BASE}/api/blending/validate-lot/${encodeURIComponent(lotNumber)}`);
                    const data = await response.json();

                    if (data.success && data.valid) {
                        if (data.powder_name === expectedPowder) {
                            if (validationDiv) validationDiv.innerHTML = `<p style="color: #4CAF50; font-weight: 600;">✓ LOT${idx} 검증 통과: ${data.powder_name} (검사일: ${data.inspection_time})</p>`;
                            if (validationRow) validationRow.style.display = 'table-row';
                            if (judgementDiv && judgementDiv.getAttribute('data-judgement') === 'pass') {
                                if (saveBtn) saveBtn.disabled = false;
                            }
                        } else {
                            if (validationDiv) validationDiv.innerHTML = `<p style="color: #f44336; font-weight: 600;">⚠️ 이종분말 검출! 투입 필요 분말: ${expectedPowder}, LOT의 실제 분말: ${data.powder_name}</p>`;
                            if (validationRow) validationRow.style.display = 'table-row';
                            if (saveBtn) saveBtn.disabled = true;
                        }
                    } else {
                        if (validationDiv) validationDiv.innerHTML = `<p style="color: #f44336; font-weight: 600;">⚠️ ${data.message}</p>`;
                        if (validationRow) validationRow.style.display = 'table-row';
                        if (saveBtn) saveBtn.disabled = true;
                    }
                } else {
                    // if only other lot is present, trigger its validation
                    if (otherVal) {
                        await validateLotSelection(recipeId, expectedPowder, idx === 1 ? 2 : 1);
                    }
                }
            } catch (error) {
                if (validationDiv) validationDiv.innerHTML = `<p style="color: #f44336;">오류: ${error.message}</p>`;
                if (validationRow) validationRow.style.display = 'table-row';
                if (saveBtn) saveBtn.disabled = true;
            }
        }

        async function saveMaterialInput(recipeId, powderName, targetWeight, tolerancePercent, powderCategory) {
            const lot1 = document.getElementById(`lot-${recipeId}-1`)?.value.trim() || '';
            const lot2 = document.getElementById(`lot-${recipeId}-2`)?.value.trim() || '';
            const w1 = parseFloat(document.getElementById(`weight-${recipeId}-1`)?.value || 0);
            const w2 = parseFloat(document.getElementById(`weight-${recipeId}-2`)?.value || 0);
            const actualWeightNum = (isNaN(w1) ? 0 : w1) + (isNaN(w2) ? 0 : w2);
            const judgementDiv = document.getElementById(`judgement-${recipeId}`);

            if ((!lot1 && !lot2) || !actualWeightNum) {
                alert('LOT 번호과 실제 중량(최소 1개)은 모두 입력하세요.');
                return;
            }

            // 판정 결과 확인 - 부적정(NG)일 경우 저장 방지
            if (judgementDiv) {
                const judgement = judgementDiv.getAttribute('data-judgement');
                if (judgement !== 'pass') {
                    alert('⚠️ 적정 판정된 원재료만 저장할 수 있습니다.\n먼저 판정 버튼을 클릭하여 적정 판정을 받아주세요.');
                    return;
                }
            }

            // 허용 범위 재확인
            const minWeight = targetWeight * (1 - tolerancePercent / 100);
            const maxWeight = targetWeight * (1 + tolerancePercent / 100);

            if (actualWeightNum < minWeight || actualWeightNum > maxWeight) {
                alert(`⚠️ 부적정(NG) 판정된 원재료는 저장할 수 없습니다.\n\n허용범위: ${formatNumber(minWeight.toFixed(2))} ~ ${formatNumber(maxWeight.toFixed(2))} kg\n입력값(합계): ${formatNumber(actualWeightNum)} kg\n\n적정 범위 내로 다시 계량해주세요.`);
                return;
            }

            // material_lot 합치기 (두개이면 쉼표로 구분)
            const materialLot = lot2 ? `${lot1},${lot2}` : lot1;

            try {
                const response = await fetch(`${API_BASE}/api/blending/material-input`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        blending_work_id: currentBlendingWork.id,
                        powder_name: powderName,
                        powder_category: powderCategory,
                        material_lot: materialLot,
                        target_weight: targetWeight,
                        actual_weight: actualWeightNum,
                        tolerance_percent: tolerancePercent,
                        operator: currentBlendingWork.operator
                    })
                });

                const data = await response.json();

                if (data.success) {
                    if (data.is_valid) {
                        alert('✓ 원재료 투입이 기록되었습니다.');
                        loadMaterialInputPage(currentBlendingWork.id);
                    } else {
                        alert(`⚠️ 부적정(NG) 판정되어 저장할 수 없습니다.\n${data.validation_message}`);
                    }
                } else {
                    if (data.is_wrong_material) {
                        alert(`❌ 이종분말 검출!\n\n${data.message}\n\n다시 확인해주세요.`);
                    } else {
                        alert('저장 실패: ' + data.message);
                    }
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        async function completeBlendingWork() {
            if (!currentBlendingWork) return;

            if (!confirm('모든 원재료 투입이 완료되었습니다.\n배합 작업을 완료하시겠습니까?')) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/blending/complete/${currentBlendingWork.id}`, {
                    method: 'PUT'
                });

                const data = await response.json();

                if (data.success) {
                    alert('배합 작업이 완료되었습니다!');
                    showPage('dashboard');
                } else {
                    alert('완료 처리 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        // ============================================
        // 배합작업 조회 (Blending Work Log)
        // ============================================

        async function loadBlendingWorks() {
            try {
                const statusFilter = document.getElementById('blendingLogStatusFilter').value;
                const completedDate = document.getElementById('filterCompletedDate') ? document.getElementById('filterCompletedDate').value : '';
                const productName = document.getElementById('filterProductName') ? document.getElementById('filterProductName').value.trim() : '';
                const batchLot = document.getElementById('filterBatchLot') ? document.getElementById('filterBatchLot').value.trim() : '';

                let url = `${API_BASE}/api/blending/works?status=${encodeURIComponent(statusFilter)}`;
                if (completedDate) url += `&completed_date=${encodeURIComponent(completedDate)}`;
                if (productName) url += `&product_name=${encodeURIComponent(productName)}`;
                if (batchLot) url += `&batch_lot=${encodeURIComponent(batchLot)}`;

                const response = await fetch(url);
                const data = await response.json();

                const tbody = document.getElementById('blendingWorksTableBody');

                if (!data.success || !data.works || data.works.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="empty-message">배합작업 내역이 없습니다.</td></tr>';
                    return;
                }

                tbody.innerHTML = data.works.map(work => {
                    const statusClass = work.status === 'completed' ? 'completed' : 'in-progress';
                    const statusText = work.status === 'completed' ? '완료' : '진행중';
                    const startTime = work.start_time ? new Date(work.start_time).toLocaleString('ko-KR') : '-';
                    const endTime = work.end_time ? new Date(work.end_time).toLocaleString('ko-KR') : '-';

                    return `
                        <tr>
                            <td>${work.work_order}</td>
                            <td>${work.product_name}</td>
                            <td><strong>${work.batch_lot}</strong></td>
                            <td>${work.operator || '-'}</td>
                            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                            <td>${startTime}</td>
                            <td>${endTime}</td>
                            <td>
                                ${work.status === 'completed' ?
                                    `<button class="btn" onclick="loadMaterialInputPage(${work.id})" style="padding: 6px 12px; font-size: 0.9em; background:#2196F3; color:white; border:none; border-radius:4px;">
                                        입력현황
                                    </button>` :
                                    `<div style="display: flex; gap: 5px;">
                                        <button class="btn" onclick="continueBlendingWork(${work.id})" style="padding: 6px 12px; font-size: 0.9em; background:#2196F3; color:white; border:none; border-radius:4px;">
                                            작업 계속
                                        </button>
                                        <button class="btn danger" onclick="deleteBlendingWork(${work.id}, '${work.batch_lot}')" style="padding: 6px 12px; font-size: 0.9em; background:#f44336; color:white; border:none; border-radius:4px;">
                                            삭제
                                        </button>
                                    </div>`
                                }
                            </td>
                        </tr>
                    `;
                }).join('');

            } catch (error) {
                console.error('배합작업 목록 로딩 실패:', error);
                document.getElementById('blendingWorksTableBody').innerHTML =
                    '<tr><td colspan="8" class="empty-message">오류 발생: ' + error.message + '</td></tr>';
            }
        }

        function startBlendingInspection(batchLot, productName) {
            // 배합검사 페이지로 이동하면서 LOT 정보 전달
            sessionStorage.setItem('blendingInspectionLot', batchLot);
            sessionStorage.setItem('blendingInspectionProduct', productName);
            showPage('mixing');
        }

        function resetBlendingFilters() {
            const dateEl = document.getElementById('filterCompletedDate');
            const prodEl = document.getElementById('filterProductName');
            const lotEl = document.getElementById('filterBatchLot');
            const statusEl = document.getElementById('blendingLogStatusFilter');
            if (dateEl) dateEl.value = '';
            if (prodEl) prodEl.value = '';
            if (lotEl) lotEl.value = '';
            if (statusEl) statusEl.value = 'in_progress';
            loadBlendingWorks();
        }

        async function deleteBlendingWork(workId, batchLot) {
            // 진행중인 배합 작업 삭제
            if (!confirm(`배합 LOT "${batchLot}"를 삭제하시겠습니까?\n\n이 작업과 관련된 모든 원재료 투입 데이터도 함께 삭제됩니다.`)) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/api/blending/work/${workId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    alert('배합 작업이 삭제되었습니다.');
                    loadBlendingWorks(); // 목록 새로고침
                } else {
                    alert('삭제 실패: ' + data.message);
                }
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        function continueBlendingWork(workId) {
            // 진행중인 배합 작업을 이어서 진행 (원재료 투입 페이지로 이동)
            if (!workId) {
                alert('유효한 작업 ID가 필요합니다.');
                return;
            }
            loadMaterialInputPage(workId);
        }

        // ============================================
        // 추적성 조회 (Traceability)
        // ============================================

        const traceabilityFormElement = document.getElementById('traceabilityForm');


        if (traceabilityFormElement) {


            traceabilityFormElement.addEventListener('submit', async (e) => {
            e.preventDefault();

            const lotNumber = document.getElementById('traceabilityLotNumber').value.trim();

            if (!lotNumber) {
                alert('LOT 번호를 입력하세요.');
                return;
            }

            try {
                // 1. 먼저 LOT 유형 확인
                const searchResponse = await fetch(`${API_BASE}/api/traceability/search?lot_number=${encodeURIComponent(lotNumber)}`);
                const searchData = await searchResponse.json();

                if (!searchData.success) {
                    document.getElementById('traceabilityResults').innerHTML = `
                        <div class="card">
                            <div class="empty-message">${searchData.message}</div>
                        </div>
                    `;
                    return;
                }

                // 2. LOT 유형에 따라 적절한 추적 수행
                const foundAs = searchData.found_as;

                if (foundAs.includes('batch_lot')) {
                    // 배합 LOT로 추적 (Backward Traceability)
                    await traceByBatchLot(lotNumber);
                } else if (foundAs.includes('material_lot')) {
                    // 원재료 LOT로 추적 (Forward Traceability)
                    await traceByMaterialLot(lotNumber);
                }

            } catch (error) {
                alert('오류: ' + error.message);
            }
        });
        }

        async function traceByBatchLot(batchLot) {
            try {
                const response = await fetch(`${API_BASE}/api/traceability/batch/${encodeURIComponent(batchLot)}`);
                const data = await response.json();

                if (!data.success) {
                    alert(data.message);
                    return;
                }

                renderBackwardTrace(data);
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        async function traceByMaterialLot(materialLot) {
            try {
                const response = await fetch(`${API_BASE}/api/traceability/material/${encodeURIComponent(materialLot)}`);
                const data = await response.json();

                if (!data.success) {
                    alert(data.message);
                    return;
                }

                renderForwardTrace(data);
            } catch (error) {
                alert('오류: ' + error.message);
            }
        }

        function renderBackwardTrace(data) {
            const container = document.getElementById('traceabilityResults');
            const work = data.blending_work;
            const materials = data.material_inputs;

            const statusBadge = work.status === 'completed'
                ? '<span class="badge pass">완료</span>'
                : '<span class="badge" style="background: #FF9800;">진행중</span>';

            let html = `
                <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-top: 20px;">
                    <h3 style="margin: 0 0 15px 0;">🔗 ${t('backwardTrace')}</h3>
                    <h2 style="margin: 0 0 20px 0;">${t('batchLotNumber')}: ${work.batch_lot}</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('productName')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${work.product_name}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('workOrderNumber')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${work.work_order}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('operator')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${work.operator}</p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px;">
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('targetTotalWeight')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${work.target_total_weight} kg</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('actualTotalWeight')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${work.actual_total_weight || '-'} kg</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">상태</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${statusBadge}</p>
                        </div>
                    </div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <h3 style="margin: 0 0 15px 0;">📦 ${t('materialInputHistory')}</h3>
                    <p style="color: #666; margin-bottom: 20px;">${t('materialInputHistoryDesc')}</p>
            `;

            materials.forEach((material, index) => {
                const inspection = material.incoming_inspection;
                const isValid = material.is_valid;
                const validationBadge = isValid
                    ? '<span class="badge pass">정상</span>'
                    : '<span class="badge fail">허용오차 초과</span>';

                html += `
                    <div style="border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #fafafa;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; font-size: 1.1em;">${index + 1}. ${material.powder_name}</h4>
                            ${validationBadge}
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px; background: white; padding: 15px; border-radius: 5px;">
                            <div>
                                <p style="color: #666; margin-bottom: 5px; font-size: 0.9em;">${t('materialLot')}</p>
                                <p style="font-weight: 600;">${material.material_lot}</p>
                            </div>
                            <div>
                                <p style="color: #666; margin-bottom: 5px; font-size: 0.9em;">${t('targetWeight')}</p>
                                <p style="font-weight: 600;">${material.target_weight} kg</p>
                            </div>
                            <div>
                                <p style="color: #666; margin-bottom: 5px; font-size: 0.9em;">${t('actualWeight')}</p>
                                <p style="font-weight: 600;">${material.actual_weight} kg</p>
                            </div>
                            <div>
                                <p style="color: #666; margin-bottom: 5px; font-size: 0.9em;">${t('weightDeviation')}</p>
                                <p style="font-weight: 600; ${isValid ? 'color: #4CAF50;' : 'color: #f44336;'}">${material.weight_deviation}%</p>
                            </div>
                        </div>

                        ${!isValid ? `<p style="color: #f44336; margin-bottom: 15px; font-weight: 600;">⚠️ ${material.validation_message}</p>` : ''}

                        ${inspection ? `
                            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3;">
                                <h5 style="margin: 0 0 10px 0; color: #1976D2;">✓ ${t('incomingInspection')}</h5>
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                                    <div>
                                        <p style="color: #666; margin-bottom: 3px; font-size: 0.85em;">${t('inspector')}</p>
                                        <p style="font-weight: 600; font-size: 0.95em;">${inspection.inspector}</p>
                                    </div>
                                    <div>
                                        <p style="color: #666; margin-bottom: 3px; font-size: 0.85em;">${t('inspectionTime')}</p>
                                        <p style="font-weight: 600; font-size: 0.95em;">${inspection.inspection_time}</p>
                                    </div>
                                    <div>
                                        <p style="color: #666; margin-bottom: 3px; font-size: 0.85em;">${t('finalResult')}</p>
                                        <p style="font-weight: 600; font-size: 0.95em;">
                                            <span class="badge ${inspection.final_result === 'PASS' ? 'pass' : 'fail'}">${inspection.final_result}</span>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ` : '<p style="color: #f44336;">⚠️ 수입검사 기록 없음</p>'}
                    </div>
                `;
            });

            html += '</div>';
            container.innerHTML = html;
        }

        function renderForwardTrace(data) {
            const container = document.getElementById('traceabilityResults');
            const inspection = data.incoming_inspection;
            const usages = data.used_in_batches;

            const inspectionBadge = inspection.final_result === 'PASS'
                ? '<span class="badge pass">합격</span>'
                : '<span class="badge fail">불합격</span>';

            let html = `
                <div class="card" style="background: linear-gradient(135deg, #2196F3 0%, #00BCD4 100%); color: white; margin-top: 20px;">
                    <h3 style="margin: 0 0 15px 0;">🔗 ${t('forwardTrace')}</h3>
                    <h2 style="margin: 0 0 20px 0;">${t('materialLot')}: ${inspection.lot_number}</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('powderName')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${inspection.powder_name}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('inspector')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${inspection.inspector}</p>
                        </div>
                        <div>
                            <p style="opacity: 0.9; margin-bottom: 5px;">${t('inspectionTime')}</p>
                            <p style="font-size: 1.2em; font-weight: 600;">${inspection.inspection_time}</p>
                        </div>
                    </div>
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
                        <p style="opacity: 0.9; margin-bottom: 5px;">${t('finalResult')}</p>
                        <p style="font-size: 1.3em; font-weight: 600;">${inspectionBadge}</p>
                    </div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <h3 style="margin: 0 0 15px 0;">🏭 ${t('usageHistory')}</h3>
                    <p style="color: #666; margin-bottom: 20px;">${t('usageHistoryDesc')}</p>
            `;

            if (usages.length === 0) {
                html += `<div class="empty-message">${t('noUsageHistory')}</div>`;
            } else {
                html += '<table style="width: 100%;"><tr><th>배합 LOT</th><th>제품명</th><th>작업지시</th><th>투입 중량</th><th>중량 편차</th><th>상태</th><th>작업일시</th></tr>';

                usages.forEach(usage => {
                    const statusBadge = usage.status === 'completed'
                        ? '<span class="badge pass">완료</span>'
                        : '<span class="badge" style="background: #FF9800;">진행중</span>';

                    const isValid = usage.is_valid;
                    const validationBadge = isValid
                        ? '<span class="badge pass">정상</span>'
                        : '<span class="badge fail">허용오차 초과</span>';

                    html += `
                        <tr>
                            <td><strong>${usage.batch_lot}</strong></td>
                            <td>${usage.product_name}</td>
                            <td>${usage.work_order}</td>
                            <td>${usage.actual_weight} kg</td>
                            <td>${usage.weight_deviation}% ${validationBadge}</td>
                            <td>${statusBadge}</td>
                            <td>${usage.start_time}</td>
                        </tr>
                    `;
                });

                html += '</table>';
            }

            html += '</div>';
            container.innerHTML = html;
        }

        // ============================================
        // 배합작업지시서 (Blending Orders)
        // ============================================

        function loadBlendingOrdersPage() {
            // 제품 목록 로드 (작업지시서 생성용)
            loadOrderProductList();
            // 작업지시서 목록 로드
            loadBlendingOrders();
        }

        async function loadOrderProductList() {
            try {
                const response = await fetch(`${API_BASE}/api/blending/products`);
                const data = await response.json();

                const select = document.getElementById('orderProductName');
                if (!select) return;

                select.innerHTML = '<option value="">제품 선택</option>';

                if (data.success && data.data && data.data.length > 0) {
                    data.data.forEach(product => {
                        select.innerHTML += `<option value="${product.product_name}">${product.product_name}</option>`;
                    });
                } else {
                    select.innerHTML += '<option value="" disabled>등록된 배합 레시피가 없습니다</option>';
                }
            } catch (error) {
                console.error('제품 목록 로딩 실패:', error);
            }
        }

        // 작업지시서 생성 폼 제출
        const orderFormElement = document.getElementById('blendingOrderForm');
        if (orderFormElement) {
            orderFormElement.addEventListener('submit', async (e) => {
                e.preventDefault();

                const productName = document.getElementById('orderProductName').value;
                const totalWeight = document.getElementById('orderTotalWeight').value;
                const createdBy = document.getElementById('orderCreatedBy').value;
                const notes = document.getElementById('orderNotes').value;
                const workDate = document.getElementById('orderDate') ? document.getElementById('orderDate').value : null;

                if (!productName || !totalWeight) {
                    alert('제품명과 총 목표중량을 입력하세요.');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE}/api/blending-orders`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            product_name: productName,
                            total_target_weight: parseFloat(totalWeight),
                            created_by: createdBy || '미지정',
                            notes: notes,
                            work_date: workDate || null
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        alert(`✓ ${data.message}`);
                        // 폼 초기화
                        e.target.reset();
                        // 목록 새로고침
                        loadBlendingOrders();
                    } else {
                        alert('작업지시서 생성 실패: ' + data.message);
                    }
                } catch (error) {
                    alert('오류: ' + error.message);
                }
            });
        }

        async function loadBlendingOrders() {
            try {
                const statusFilter = document.getElementById('orderStatusFilter')?.value || 'all';
                const response = await fetch(`${API_BASE}/api/blending-orders?status=${statusFilter}`);
                const data = await response.json();

                const container = document.getElementById('blendingOrdersList');
                if (!container) return;

                if (!data.success || !data.orders || data.orders.length === 0) {
                    container.innerHTML = '<div class="empty-message">작업지시서가 없습니다.</div>';
                    return;
                }

                let html = `
                    <table class="data-table" style="width: 100%;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                <th style="padding: 15px; text-align: center;">생성일</th>
                                <th style="padding: 15px; text-align: center;">작업지시번호</th>
                                <th style="padding: 15px; text-align: center;">제품명</th>
                                <th style="padding: 15px; text-align: center;">총중량 (kg)</th>
                                <th style="padding: 15px; text-align: center;">진도율</th>
                                <th style="padding: 15px; text-align: center;">상태/액션</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                data.orders.forEach(order => {
                    const progressPercent = order.progress_percent || 0;
                    const isCompleted = order.status === 'completed' || progressPercent >= 100;

                    // 진도율 프로그레스바
                    let progressBarColor = '#4CAF50';
                    if (progressPercent < 30) progressBarColor = '#f44336';
                    else if (progressPercent < 70) progressBarColor = '#FF9800';

                    const progressBar = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="flex: 1; background: #e0e0e0; height: 25px; border-radius: 12px; overflow: hidden;">
                                <div style="width: ${progressPercent}%; height: 100%; background: ${progressBarColor}; transition: width 0.3s;"></div>
                            </div>
                            <span style="font-weight: 600; font-size: 1.1em;">${progressPercent}%</span>
                        </div>
                    `;

                    const rowBg = isCompleted ? '#f0f8f0' : '#ffffff';

                    html += `
                        <tr style="background: ${rowBg}; border-bottom: 2px solid #eee;">
                            <td style="padding: 15px; text-align: center;">
                                ${order.created_date}
                            </td>
                            <td style="padding: 15px; text-align: center; font-weight: 600; font-size: 1.1em;">
                                ${order.work_order_number}
                            </td>
                            <td style="padding: 15px; text-align: center;">
                                ${order.product_name}
                            </td>
                            <td style="padding: 15px; text-align: center; font-size: 1.1em; font-weight: 600;">
                                ${formatNumber(order.total_target_weight)} kg
                            </td>
                            <td style="padding: 15px;">
                                ${progressBar}
                            </td>
                            <td style="padding: 15px; text-align: center;">
                                ${isCompleted
                                    ? '<span style="background: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px; font-weight: 600;">✓ 완료</span>'
                                    : `<button onclick="deleteBlendingOrder(${order.id})" class="btn danger" style="padding: 8px 12px; border-radius:4px;">삭제</button>`
                                }
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
                container.innerHTML = html;

            } catch (error) {
                console.error('작업지시서 목록 로딩 실패:', error);
                const container = document.getElementById('blendingOrdersList');
                if (container) {
                    container.innerHTML = '<div class="empty-message">작업지시서 목록을 불러올 수 없습니다.</div>';
                }
            }
        }

        // 배합 페이지에서 작업 시작을 위해 간단히 작업지시서 목록을 렌더링
        async function loadBlendingOrdersForBlending() {
            try {
                const response = await fetch(`${API_BASE}/api/blending-orders?status=in_progress`);
                const data = await response.json();

                const container = document.getElementById('blendingOrdersForBlending');
                if (!container) return;

                if (!data.success || !data.orders || data.orders.length === 0) {
                    container.innerHTML = '<div class="empty-message">진행중인 작업지시서가 없습니다.</div>';
                    return;
                }

                let html = '<table class="data-table" style="width:100%"><thead><tr><th>생성일</th><th>작업지시번호</th><th>제품명</th><th>총중량</th><th>진도</th><th>작업</th></tr></thead><tbody>';

                data.orders.forEach(order => {
                    const created = order.created_date || '-';
                    const workNo = order.work_order_number || '-';
                    const prod = order.product_name || '-';
                    const total = order.total_target_weight ? formatNumber(order.total_target_weight) + ' kg' : '-';
                    const prog = order.progress_percent || 0;

                    html += `
                        <tr>
                            <td>${created}</td>
                            <td>${workNo}</td>
                            <td>${prod}</td>
                            <td>${total}</td>
                            <td>${prog}%</td>
                            <td>
                                <button class="btn primary" onclick="startBlendingFromOrder(${order.id}, '${escapeHtml(order.product_name || '')}', '${escapeHtml(order.work_order_number || '')}')" style="padding:6px 10px;">
                                    작업시작하기
                                </button>
                            </td>
                        </tr>`;
                });

                html += '</tbody></table>';
                container.innerHTML = html;

            } catch (err) {
                console.error('blending orders for blending 로딩 실패:', err);
                const container = document.getElementById('blendingOrdersForBlending');
                if (container) container.innerHTML = '<div class="empty-message">작업지시서 목록을 불러올 수 없습니다.</div>';
            }
        }

        // 간단한 HTML 이스케이프 (문자열을 속성/텍스트로 안전하게 사용)
        function escapeHtml(str) {
            if (!str && str !== 0) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        // 작업지시서 삭제
        async function deleteBlendingOrder(orderId) {
            if (!confirm('정말 해당 작업지시서를 삭제하시겠습니까?')) return;
            try {
                const resp = await fetch(`${API_BASE}/api/blending-orders/${orderId}`, { method: 'DELETE' });
                const data = await resp.json();
                if (!data.success) {
                    alert('삭제 실패: ' + (data.message || '알 수 없는 오류'));
                    return;
                }
                // 삭제 성공 시 목록 새로고침
                loadBlendingOrdersPage();
            } catch (error) {
                console.error('작업지시서 삭제 실패:', error);
                alert('작업지시서 삭제 중 오류가 발생했습니다. 콘솔을 확인하세요.');
            }
        }

        async function startBlendingFromOrder(orderId, productName, workOrderNumber) {
            // 배합작업 페이지로 이동 후 폼 표시 및 채우기
            showPage('blending');

            try {
                const resp = await fetch(`${API_BASE}/api/blending-orders/${orderId}`);
                const data = await resp.json();
                if (!data.success) {
                    alert('작업지시서 정보를 불러오지 못했습니다: ' + (data.message || ''));
                    return;
                }

                const order = data.order;

                // 제품 선택
                const productSelect = document.getElementById('blendingProductName');
                if (productSelect) {
                    // 시도해서 옵션을 선택, 없으면 값으로 설정
                    let found = false;
                    for (let i = 0; i < productSelect.options.length; i++) {
                        if (productSelect.options[i].value === order.product_name) {
                            productSelect.selectedIndex = i;
                            found = true;
                            break;
                        }
                    }
                    if (!found) productSelect.value = order.product_name;
                    productSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }

                // 작업지시번호
                const workOrderInput = document.getElementById('blendingWorkOrder');
                if (workOrderInput) {
                    workOrderInput.value = order.work_order_number || '';
                    workOrderInput.setAttribute('readonly', 'readonly');
                    workOrderInput.style.background = '#f0f0f0';
                }

                // 목표중량 설정 (select에 없으면 임시 option 추가)
                const targetSelect = document.getElementById('blendingTargetWeight');
                if (targetSelect) {
                    const val = order.total_target_weight;
                    let optExists = false;
                    for (let opt of targetSelect.options) {
                        if (String(opt.value) === String(val)) { optExists = true; break; }
                    }
                    if (!optExists) {
                        const opt = document.createElement('option');
                        opt.value = val;
                        opt.text = formatNumber(val) + ' kg';
                        targetSelect.prepend(opt);
                    }
                    targetSelect.value = val;
                }

                // operator 비워두기 (사용자가 선택)
                const opSelect = document.getElementById('blendingOperator');
                if (opSelect) opSelect.value = '';

                // batch lot은 새로 생성
                await generateAndSetBatchLot();

                // 보이기
                showBlendingForm();
            } catch (err) {
                console.error(err);
                alert('작업지시서 불러오기 중 오류가 발생했습니다.');
            }
        }

        // 번역 헬퍼 함수
        function t(key) {
            return translations[currentLang][key] || key;
        }

        // 숫자 포맷팅 함수 (천단위 콤마)
        function formatNumber(num) {
            if (num === null || num === undefined || num === '') return '';
            return Number(num).toLocaleString('ko-KR');
        }

        // 소수 둘째 자리 포맷(예: 60 -> "60.00")
        function formatTwo(num) {
            if (num === null || num === undefined || num === '') return '';
            const n = parseFloat(num);
            if (isNaN(n)) return '';
            return n.toFixed(2);
        }

        // 초기 로드
        window.onload = () => {
            updateLanguage();
            loadIncompleteInspections();
        };
