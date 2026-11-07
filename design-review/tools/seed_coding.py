"""Add the agentic coding tools: Claude Code, Codex, Antigravity, DeepSeek Harness, etc.

Run after seed_tools.py and seed_tools_extra.py:
    venv\\Scripts\\python.exe design-review/tools/seed_coding.py
Idempotent: matches by name and updates in place.
"""
import datetime
import sys

sys.path.insert(0, "app")
import app as m  # noqa: E402

CHECKED = datetime.date(2026, 11, 7)

TOOLS = [
    dict(name="Claude Code", name_ar="كلود كود", category="coding",
         tagline_en="A terminal agent that edits and tests a real repo.",
         tagline_ar="وكيل طرفية يعدل مشروعك ويشغّل اختباراته.",
         description_en="Anthropic's command-line coding agent: it reads the repository, plans changes, edits files, runs tests and commits. Best for multi-file work where you want to review a diff, not chat about code; it needs a Claude plan or API key.",
         description_ar="وكيل برمجة من Anthropic في سطر الأوامر: يقرأ المستودع ويخطط ويعدل الملفات ويشغّل الاختبارات. الأفضل للأعمال متعددة الملفات حيث تراجع الفروق بدل محادثة عن الشيفرة، ويحتاج خطة Claude أو مفتاح API.",
         official_url="https://code.claude.com", pricing="paid", free_tier=False,
         arabic_support=False, platforms="macOS, Linux, Windows, Terminal, VS Code",
         best_for="Agentic work across many files", featured=True, sort_order=14),
    dict(name="OpenAI Codex", name_ar="أوبن إيه آي كوديكس", category="coding",
         tagline_en="A cloud and CLI agent for delegated coding tasks.",
         tagline_ar="وكيل سحابي وسطر أوامر لمهام برمجية مفوّضة.",
         description_en="Runs coding tasks in an isolated cloud environment or locally through the CLI, then returns a reviewable diff. Good for parallel tasks and small features; access is tied to paid ChatGPT plans.",
         description_ar="ينفّذ مهام برمجية في بيئة سحابية معزولة أو محليًا عبر CLI ثم يعيد فروقًا قابلة للمراجعة. جيد للمهام المتوازية والميزات الصغيرة، والوصول مرتبط بخطط ChatGPT المدفوعة.",
         official_url="https://openai.com/codex/", pricing="paid", free_tier=False,
         arabic_support=False, platforms="Web, CLI, IDE",
         best_for="Delegating small coding tasks", featured=True, sort_order=15),
    dict(name="Google Antigravity", name_ar="جوجل أنتيجرافيتي", category="coding",
         tagline_en="An agent-first IDE with an agent manager.",
         tagline_ar="بيئة تطوير تبدأ من الوكلاء مع مدير مهام.",
         description_en="Google's agent-first development environment: an IDE, a manager for several agents, browser control and artifacts for reviewing what each agent did. Available as a public preview.",
         description_ar="بيئة تطوير من جوجل تبدأ من الوكلاء: محرر ومدير لعدة وكلاء وتحكم في المتصفح ومخرجات لمراجعة ما فعله كل وكيل. متاحة كمعاينة عامة.",
         official_url="https://antigravity.google/", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Windows, macOS, Linux",
         best_for="Managing several coding agents", featured=True, sort_order=16),
    dict(name="DeepSeek Harness", name_ar="ديب سيك هارنس", category="coding",
         tagline_en="An open-source harness with plugins for everything.",
         tagline_ar="إطار مفتوح المصدر بإضافات لكل شيء.",
         description_en="DeepSeek's open-source desktop and web harness: coding, research, documents and background tasks, with a composable plugin architecture. A serious free option for learning how agent harnesses work.",
         description_ar="إطار ديب سيك المفتوح لسطح المكتب والويب: برمجة وبحث ومستندات ومهام خلفية، بمعمارية إضافات قابلة للتركيب. خيار مجاني جاد لتعلم كيفية عمل أُطر الوكلاء.",
         official_url="https://www.deepseek.com/en/harness/", pricing="free", free_tier=True,
         arabic_support=False, platforms="Windows, macOS, Linux, Web",
         best_for="An open, extensible agent harness", featured=True, sort_order=17),
    dict(name="Cline", name_ar="كلاين", category="coding",
         tagline_en="An open-source coding agent inside VS Code.",
         tagline_ar="وكيل برمجة مفتوح المصدر داخل VS Code.",
         description_en="Reads files, writes code, runs terminal commands and uses the browser, with explicit approval for each step. Open source and bring-your-own model key.",
         description_ar="يقرأ الملفات ويكتب الشيفرة ويشغّل أوامر الطرفية ويستخدم المتصفح، مع موافقة صريحة على كل خطوة. مفتوح المصدر ويستخدم مفتاح نموذجك.",
         official_url="https://cline.bot", pricing="free", free_tier=True,
         arabic_support=False, platforms="VS Code",
         best_for="A transparent VS Code agent", featured=False, sort_order=18),
    dict(name="Aider", name_ar="أيدر", category="coding",
         tagline_en="A terminal pair programmer that commits.",
         tagline_ar="مبرمج مساعد في الطرفية يحفظ التغييرات.",
         description_en="Edits files from the terminal, keeps a map of the repository and writes clean git commits. Lightweight, scriptable and open source; you supply the model API.",
         description_ar="يعدل الملفات من الطرفية ويحتفظ بخريطة للمستودع ويكتب commits نظيفة. خفيف وقابل للأتمتة ومفتوح المصدر، وأنت توفر واجهة النموذج.",
         official_url="https://aider.chat", pricing="free", free_tier=True,
         arabic_support=False, platforms="Terminal",
         best_for="Git-friendly terminal editing", featured=False, sort_order=19),
    dict(name="Continue", name_ar="كونتينيو", category="coding",
         tagline_en="An open-source assistant for VS Code and JetBrains.",
         tagline_ar="مساعد مفتوح المصدر لـVS Code وJetBrains.",
         description_en="Chat, autocomplete and edit across your editor with local or hosted models. Configurable and open source, a good fit when data must stay on your machine.",
         description_ar="محادثة وإكمال وتحرير داخل محررك مع نماذج محلية أو مستضافة. قابل للتهيئة ومفتوح المصدر، مناسب عندما يجب أن تبقى البيانات على جهازك.",
         official_url="https://www.continue.dev", pricing="free", free_tier=True,
         arabic_support=False, platforms="VS Code, JetBrains",
         best_for="Local and configurable IDE help", featured=False, sort_order=20),
    dict(name="OpenHands", name_ar="أوبن هاندز", category="coding",
         tagline_en="An open-source software engineering agent.",
         tagline_ar="وكيل هندسة برمجيات مفتوح المصدر.",
         description_en="Runs an agent in a sandbox with a shell, editor and browser, and can be self-hosted or used in the cloud. A research-friendly way to study autonomous coding.",
         description_ar="يشغّل وكيلًا في بيئة معزولة مع طرفية ومحرر ومتصفح، ويمكن استضافته ذاتيًا أو استخدامه سحابيًا. طريقة مناسبة للبحث في البرمجة الذاتية.",
         official_url="https://www.all-hands.dev", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, Docker, Self-hosted",
         best_for="Open autonomous coding experiments", featured=False, sort_order=21),
    dict(name="Devin", name_ar="ديفين", category="coding",
         tagline_en="A delegated autonomous software engineer.",
         tagline_ar="مهندس برمجيات مستقل تتولى المهمة.",
         description_en="A cloud agent that takes a task, works in its own environment and returns a pull request. Expensive and best for well-scoped chores, not open-ended architecture.",
         description_ar="وكيل سحابي يتولى مهمة ويعمل في بيئته ثم يعيد طلب دمج. مكلف والأفضل للمهام المحددة لا للمعمارية المفتوحة.",
         official_url="https://devin.ai", pricing="paid", free_tier=False,
         arabic_support=False, platforms="Web",
         best_for="Delegating well-scoped tickets", featured=False, sort_order=22),
    dict(name="Gemini CLI", name_ar="جيميناي CLI", category="coding",
         tagline_en="Google's free terminal agent.",
         tagline_ar="وكيل جوجل المجاني في الطرفية.",
         description_en="An open-source terminal agent with a generous free tier, file tools and MCP support. A practical first agent for a student who does not want another subscription.",
         description_ar="وكيل طرفية مفتوح المصدر بخطة مجانية سخية وأدوات ملفات ودعم MCP. وكيل أول عملي لطالب لا يريد اشتراكًا آخر.",
         official_url="https://github.com/google-gemini/gemini-cli", pricing="free", free_tier=True,
         arabic_support=False, platforms="Terminal",
         best_for="A free first terminal agent", featured=False, sort_order=23),
    dict(name="OpenCode", name_ar="أوبن كود", category="coding",
         tagline_en="An open-source terminal coding agent.",
         tagline_ar="وكيل برمجة مفتوح المصدر في الطرفية.",
         description_en="A provider-agnostic terminal agent with a TUI, sessions and local model support. Good for experimenting without locking into one vendor.",
         description_ar="وكيل طرفية مستقل عن المزود بواجهة TUI وجلسات ودعم نماذج محلية. جيد للتجريب دون الارتباط بمزود واحد.",
         official_url="https://opencode.ai", pricing="free", free_tier=True,
         arabic_support=False, platforms="Terminal, Desktop",
         best_for="Vendor-neutral terminal agent", featured=False, sort_order=24),
    dict(name="Amazon Q Developer", name_ar="أمازون كيو ديفيلوبر", category="coding",
         tagline_en="An AWS-aware coding and review assistant.",
         tagline_ar="مساعد برمجة ومراجعة يعرف AWS.",
         description_en="Completes code, explains AWS services, scans for security issues and can upgrade Java versions. Most valuable if your course or project already runs on AWS.",
         description_ar="يكمل الشيفرة ويشرح خدمات AWS ويفحص المشكلات الأمنية ويرقّي إصدارات Java. الأكثر قيمة إذا كان مقررك أو مشروعك على AWS.",
         official_url="https://aws.amazon.com/q/developer/", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="VS Code, JetBrains, CLI, AWS Console",
         best_for="AWS projects and code reviews", featured=False, sort_order=25),
    dict(name="Kiro", name_ar="كيرو", category="coding",
         tagline_en="A spec-driven agentic IDE.",
         tagline_ar="بيئة تطوير تبدأ من المواصفات.",
         description_en="Turns a request into a specification, then tasks and code, so the agent's plan is reviewable before it edits. Useful for teaching structured AI-assisted development.",
         description_ar="يحوّل الطلب إلى مواصفات ثم مهام ثم شيفرة، فتكون خطة الوكيل قابلة للمراجعة قبل التعديل. مفيد لتعليم التطوير المنظم بمساعدة الذكاء الاصطناعي.",
         official_url="https://kiro.dev", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Windows, macOS, Linux",
         best_for="Spec-first AI development", featured=False, sort_order=26),
    dict(name="Trae", name_ar="تراي", category="coding",
         tagline_en="A free AI IDE with builder mode.",
         tagline_ar="بيئة تطوير مجانية بوضع البناء.",
         description_en="ByteDance's AI editor with chat, agent and builder modes for turning a description into a working app. A low-friction option for students, though the ecosystem is younger.",
         description_ar="محرر ذكاء اصطناعي من بايت دانس بأوضاع محادثة ووكيل وبناء لتحويل الوصف إلى تطبيق. خيار منخفض العائق للطلبة، وإن كان نظامه البيئي أحدث.",
         official_url="https://www.trae.ai", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Windows, macOS, Linux",
         best_for="Building small apps quickly", featured=False, sort_order=27),
]


def main():
    with m.app.app_context():
        created = updated = 0
        for data in TOOLS:
            tool = m.AITool.query.filter_by(name=data["name"]).first()
            if tool is None:
                tool = m.AITool(name=data["name"])
                m.db.session.add(tool)
                created += 1
            else:
                updated += 1
            for key, value in data.items():
                setattr(tool, key, value)
            tool.is_published = True
            tool.last_checked = CHECKED
            tool.related_article_ids = tool.related_article_ids or "[]"
        m.db.session.commit()
        print(f"Coding tools: {created} created, {updated} updated, total {m.AITool.query.count()}")


if __name__ == "__main__":
    main()
