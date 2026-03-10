import os

for root, _, files in os.walk('e:/FitGuard/fitguard-api/app'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'from app.__init__ import db' in content:
                content = content.replace('from app.__init__ import db', 'from app import db')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {path}")
