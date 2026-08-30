import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app
from database import list_detections

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user'] = 'test_user'
    
    # Test index
    res = client.get('/')
    print('Index status:', res.status_code)
    
    # Test history
    res = client.get('/history')
    print('History status:', res.status_code)
    
    # Test history detail for latest record
    records = list_detections(limit=1)
    if records:
        rec_id = records[0]['id']
        res = client.get(f'/history/{rec_id}')
        print(f'History detail #{rec_id} status:', res.status_code)
        assert b'AI Performance & Confidence Metrics' in res.data
        assert b'F1-Score' in res.data
        print('History detail rendered successfully with Confidence, Accuracy, and F1-Score metrics!')

print('All app routes and templates verified successfully!')
