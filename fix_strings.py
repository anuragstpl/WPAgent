#!/usr/bin/env python3
import re

# Read the file
with open('chat_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix broken strings that end with unfinished quotes
# Pattern 1: Lines ending with just a quote
content = re.sub(r'return f"([^"]*)\n"', r'return f"\1"', content, flags=re.MULTILINE)

# Pattern 2: Success messages with broken multiline format
patterns = [
    (r'return f"✅ ([^"]*) successfully!\n\n"', r'return f"✅ \1 successfully!\\n\\n"'),
    (r'return f"❌ ([^"]*)\n"', r'return f"❌ \1"'),
    (r'return f"([^"]*)\n\n"', r'return f"\1\\n\\n"'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Fix newline characters that aren't escaped
content = re.sub(r'\\n([^"]*)"([^"]*)\\n', r'\\n\1\\n\2\\n', content)

# Write the fixed content back
with open('chat_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed string literals in chat_app.py")