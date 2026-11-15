from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")
s = s.replace("__import__('re').match", "re.match")
p.write_text(s, encoding="utf-8")
print("re cleaned:", "__import__('re')" not in s)
