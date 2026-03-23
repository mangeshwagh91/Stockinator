path = r'c:\Users\wmang\OneDrive\Desktop\Stockinator\backend\app\services\indicator_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace emoji warning prints with ASCII-safe versions
old1 = 'print("\u26a0\ufe0f  TA-Lib not installed. Indicator calculations will be limited.")'
new1 = 'print("[WARNING] TA-Lib not installed. Indicator calculations will be limited.")'
old2 = 'print("\u26a0\ufe0f  TA-Lib not installed. Using pandas fallback indicators")'
new2 = 'print("[WARNING] TA-Lib not installed. Using pandas fallback indicators")'

content = content.replace(old1, new1)
content = content.replace(old2, new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indicator_service.py successfully')
