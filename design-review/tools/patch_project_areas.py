from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")
anchor = "LLMWARE_PICKS = ["
block = '''PROJECT_AREAS = {
    'agents': ('Agents & automation', 'الوكلاء والأتمتة'),
    'rag': ('Search & RAG', 'البحث وRAG'),
    'arabic': ('Arabic AI', 'الذكاء الاصطناعي العربي'),
    'education': ('Learning & teaching', 'التعلم والتعليم'),
    'vision': ('Vision & imaging', 'الرؤية والصور'),
    'audio': ('Speech & audio', 'الصوت والكلام'),
    'security': ('Safety & security', 'الأمان والحماية'),
    'sustainability': ('Sustainability', 'الاستدامة'),
    'data': ('Data & recommendation', 'البيانات والتوصية'),
    'accessibility': ('Accessibility', 'الوصول'),
}

'''
if "PROJECT_AREAS =" not in s:
    s = s.replace(anchor, block + anchor, 1)
    p.write_text(s, encoding="utf-8")
    print("inserted PROJECT_AREAS")
else:
    print("PROJECT_AREAS already exists")
