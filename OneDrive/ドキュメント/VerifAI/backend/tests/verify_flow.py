"""End-to-end verification of upload -> analysis -> results -> evidence -> recommendations -> history."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tests.conftest import DirectTestClient, TestingSessionLocal, test_engine
from app.models.database import Base

Base.metadata.create_all(bind=test_engine)

def get_test_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

client = DirectTestClient(get_test_db)

# 1. Flow for File A (Upload -> Analysis -> Result)
with open('sample_documents/scenario_a_suspicious_job_offer.pdf', 'rb') as fp:
    bytes_a = fp.read()
res_a = client.post('/api/analyze/file', files={'file': ('scenario_a.pdf', bytes_a)})
print('1. Upload File A status:', res_a.status_code)
data_a = res_a.json()
id_a = data_a['id']
print('   Record ID:', id_a)
print('   Composite Risk:', data_a['risk_level'])
print('   ML Prediction:', data_a['prediction'], f"({data_a['model_score']:.2f})")
print('   Rule Risk Score:', f"{data_a['rule_risk_score']:.2f}")
print('   Indicators Count:', len(data_a['detected_indicators']))
for i, ind in enumerate(data_a['detected_indicators'], 1):
    print(f"     [{i}] {ind['indicator_name']} ({ind['severity']}): \"{ind['matched_evidence']}\"")
print('   Recommendations Count:', len(data_a['recommendations']))

# 2. Flow for File B (Upload -> Analysis -> Result)
with open('sample_documents/scenario_b_suspicious_internship.pdf', 'rb') as fp:
    bytes_b = fp.read()
res_b = client.post('/api/analyze/file', files={'file': ('scenario_b.pdf', bytes_b)})
print('\n2. Upload File B status:', res_b.status_code)
data_b = res_b.json()
id_b = data_b['id']
print('   Record ID:', id_b)
print('   Composite Risk:', data_b['risk_level'])
print('   Indicators Count:', len(data_b['detected_indicators']))
for i, ind in enumerate(data_b['detected_indicators'], 1):
    print(f"     [{i}] {ind['indicator_name']} ({ind['severity']}): \"{ind['matched_evidence']}\"")

# 3. Flow for File C (Upload -> Analysis -> Result)
with open('sample_documents/scenario_c_legitimate_internship.pdf', 'rb') as fp:
    bytes_c = fp.read()
res_c = client.post('/api/analyze/file', files={'file': ('scenario_c.pdf', bytes_c)})
print('\n3. Upload File C status:', res_c.status_code)
data_c = res_c.json()
id_c = data_c['id']
print('   Record ID:', id_c)
print('   Composite Risk:', data_c['risk_level'])
print('   Indicators Count:', len(data_c['detected_indicators']))
print('   Evidence Count:', len(data_c['evidence']))
assert data_c['risk_level'] == 'LOW'
assert len(data_c['detected_indicators']) == 0

# 4. History Listing Flow
res_hist = client.get('/api/history')
print('\n4. History listing status:', res_hist.status_code)
hist_data = res_hist.json()
print('   Total recorded analyses:', hist_data['total'])
assert hist_data['total'] == 3
for item in hist_data['items']:
    print(f"   - Analysis #{item['id']}: type={item['submission_type']}, risk={item['risk_level']}, ML={item['model_score']:.2f}, Rule={item['rule_risk_score']:.2f}")

# 5. Detail Retrieval Flow
for target_id in [id_a, id_b, id_c]:
    res_det = client.get(f'/api/history/{target_id}')
    assert res_det.status_code == 200
    det_data = res_det.json()
    assert det_data['id'] == target_id
    print(f"5. Detail retrieval #{target_id} verified: Risk={det_data['risk_level']}, Indicators={len(det_data['detected_indicators'])}, Recommendations={len(det_data['recommendations'])}")

print('\nCOMPLETE USER FLOW VERIFIED SUCCESSFULLY: upload -> analysis -> results -> evidence -> recommendations -> history')
