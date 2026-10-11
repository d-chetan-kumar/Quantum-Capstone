import os
import re

IGNORE_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', '.pytest_cache'}

def scan_repo():
    patterns = [
        re.compile(r'30\s*[/:]\s*70'),
        re.compile(r'30%\s*(?:XGBoost|\+)\s*70%'),
        re.compile(r'30%\s*XGB'),
        re.compile(r'70%\s*VQC'),
        re.compile(r'0\.30?\s*\*\s*xgb|0\.70?\s*\*\s*vqc', re.IGNORECASE),
        re.compile(r'xgboost_weight\s*[:=]\s*0\.3', re.IGNORECASE),
        re.compile(r'vqc_weight\s*[:=]\s*0\.7', re.IGNORECASE),
    ]

    matches = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in ['.py', '.json', '.tsx', '.ts', '.jsx', '.js', '.md', '.html', '.css']:
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as handle:
                        for l_idx, line in enumerate(handle, 1):
                            for p in patterns:
                                if p.search(line):
                                    matches.append((path, l_idx, line.strip()))
                except Exception as e:
                    pass

    print(f'Total matches found: {len(matches)}')
    for path, l_idx, line in matches:
        print(f'{path}:{l_idx}: {line}')

if __name__ == '__main__':
    scan_repo()
