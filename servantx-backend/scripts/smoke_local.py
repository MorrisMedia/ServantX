import json
import uuid
from pathlib import Path
import httpx

BASE='http://127.0.0.1:8000'
email=f'smoke-{uuid.uuid4().hex[:8]}@example.com'
password='TestPass123!'
sample=Path('/home/node/.openclaw/workspace-tech-support-2/ServantX/servantx-backend/smoke_sample.835')

with httpx.Client(base_url=BASE, timeout=60.0) as client:
    reg = client.post('/auth/register', json={
        'email': email,
        'name': 'Smoke Tester',
        'hospital_name': 'Smoke Hospital',
        'phone': '555-0100',
        'password': password,
        'confirm_password': password,
    })
    reg.raise_for_status()
    auth = reg.json()
    token = auth['access_token']
    headers={'Authorization': f'Bearer {token}'}

    contract = client.post('/contracts/seed', headers=headers)
    contract.raise_for_status()

    project = client.post('/projects/ensure-default', headers=headers)
    project.raise_for_status()
    project_id = project.json()['id']

    files={'files': (sample.name, sample.read_bytes(), 'text/plain')}
    batch = client.post('/batches/upload-835', headers=headers, files=files, data={'project_id': project_id})
    batch.raise_for_status()
    batch_json = batch.json()
    batch_id = batch_json['batch']['id']

    batch_status = client.get(f'/batches/{batch_id}/status', headers=headers)
    batch_status.raise_for_status()
    batch_documents = client.get(f'/batches/{batch_id}/documents', headers=headers)
    batch_documents.raise_for_status()
    docs_json = batch_documents.json()

    verify = client.post(f'/projects/{project_id}/verify', headers=headers, json={'batchRunId': batch_id})
    verify.raise_for_status()
    verify_json = verify.json()

    audit = client.post(f'/projects/{project_id}/audit-runs', headers=headers, json={'batchRunId': batch_id, 'verificationRunId': verify_json['id']})
    audit.raise_for_status()
    audit_json = audit.json()

    print(json.dumps({
        'email': email,
        'project': project.json(),
        'contract': contract.json(),
        'batch': batch_json,
        'batch_status': batch_status.json(),
        'documents': docs_json,
        'verification': verify_json,
        'audit': audit_json,
    }, indent=2, default=str))
