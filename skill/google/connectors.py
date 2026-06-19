import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[2]
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
]


def load_google_credentials() -> service_account.Credentials:
    json_text = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    json_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_PATH')

    if json_text:
        info = json.loads(json_text)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    if json_path:
        return service_account.Credentials.from_service_account_file(json_path, scopes=SCOPES)

    raise RuntimeError('Google service account credentials are missing. Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_JSON_PATH.')


def get_service(api_name: str, version: str):
    creds = load_google_credentials()
    return build(api_name, version, credentials=creds, cache_discovery=False)


def read_sheet(sheet_id: str, range_name: str = 'Sheet1!A1:C10') -> str:
    service = get_service('sheets', 'v4')
    sheet = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = sheet.get('values', [])
    if not values:
        return ''

    rows = [' | '.join(row) for row in values]
    text = '\n'.join(rows)

    out_path = ROOT / 'knowledge' / 'google_sheet.txt'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding='utf-8')
    return text


def read_sheet_rows(sheet_id: str, range_name: str = 'Sheet1!A1:Z100') -> list:
    """Return sheet rows as list of dicts (header -> value)."""
    service = get_service('sheets', 'v4')
    resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = resp.get('values', [])
    if not values:
        return []

    headers = [h.strip() for h in values[0]]
    rows = []
    for r in values[1:]:
        item = {}
        for i, h in enumerate(headers):
            item[h] = r[i] if i < len(r) else ''
        rows.append(item)

    return rows


def parse_structural_elements(elements: List[Dict]) -> str:
    text = []
    for value in elements:
        if 'paragraph' in value:
            for elem in value['paragraph'].get('elements', []):
                if 'textRun' in elem and 'content' in elem['textRun']:
                    text.append(elem['textRun']['content'])
        elif 'table' in value:
            for row in value['table'].get('tableRows', []):
                for cell in row.get('tableCells', []):
                    text.append(parse_structural_elements(cell.get('content', [])))
        elif 'sectionBreak' in value:
            text.append('\n')
    return ''.join(text)


def read_doc(doc_id: str) -> str:
    service = get_service('docs', 'v1')
    document = service.documents().get(documentId=doc_id).execute()
    body = document.get('body', {}).get('content', [])
    text = parse_structural_elements(body)

    out_path = ROOT / 'knowledge' / 'google_doc.txt'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding='utf-8')
    return text
