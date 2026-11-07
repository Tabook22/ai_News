"""Add model hubs and GPU platforms to the AI tools directory.

Run after the other seeds:
    venv\\Scripts\\python.exe design-review/tools/seed_platforms.py
Idempotent: matches by name and updates in place.
"""
import datetime
import sys

sys.path.insert(0, "app")
import app as m  # noqa: E402

CHECKED = datetime.date(2026, 11, 7)

TOOLS = [
    dict(name="Hugging Face", name_ar="هاجينغ فيس", category="platforms",
         tagline_en="The home of open models, datasets and demos.",
         tagline_ar="بيت النماذج والبيانات والعروض المفتوحة.",
         description_en="Download open LLMs and datasets, try community demos in Spaces, and serve models through Inference Endpoints. The first place to check before renting a GPU or picking a model.",
         description_ar="حمّل نماذج اللغة والبيانات المفتوحة، وجرّب عروض المجتمع في Spaces، وقدّم النماذج عبر Inference Endpoints. أول مكان تتحقق منه قبل استئجار GPU أو اختيار نموذج.",
         official_url="https://huggingface.co", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, API, CLI",
         best_for="Downloading models and datasets", featured=True, sort_order=110),
    dict(name="RunPod", name_ar="ران بود", category="platforms",
         tagline_en="Rent a GPU by the second.",
         tagline_ar="استأجر GPU بالثانية.",
         description_en="On-demand GPU pods for training and inference, with templates for PyTorch, ComfyUI and vLLM. Pay by the minute; good for a short fine-tune or a demo that needs a real GPU.",
         description_ar="حاويات GPU عند الطلب للتدريب والاستدلال، مع قوالب لـPyTorch وComfyUI وvLLM. الدفع بالدقيقة، جيد لضبط نموذج قصير أو عرض يحتاج GPU حقيقيًا.",
         official_url="https://www.runpod.io", pricing="paid", free_tier=False,
         arabic_support=False, platforms="Web, CLI, API",
         best_for="Renting a GPU for a few hours", featured=True, sort_order=111),
    dict(name="Google Colab", name_ar="جوجل كولاب", category="platforms",
         tagline_en="Free notebook GPUs for learning and demos.",
         tagline_ar="GPU مجانية في دفاتر الملاحظات للتعلم والعروض.",
         description_en="Runs Jupyter notebooks in the browser with a free GPU tier and optional paid compute. The easiest zero-setup way to follow a tutorial or fine-tune a small model.",
         description_ar="يشغّل دفاتر Jupyter في المتصفح بخطة GPU مجانية وحوسبة مدفوعة اختيارية. أسهل طريقة بلا إعداد لمتابعة درس أو ضبط نموذج صغير.",
         official_url="https://colab.research.google.com", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web",
         best_for="Free GPU notebooks", featured=False, sort_order=112),
    dict(name="Kaggle", name_ar="كاجل", category="platforms",
         tagline_en="Datasets, notebooks and a free GPU quota.",
         tagline_ar="بيانات ودفاتر وحصة GPU مجانية.",
         description_en="A data-science community with public datasets, competitions and notebook GPUs. Useful when the dataset matters as much as the model.",
         description_ar="مجتمع علوم بيانات ببيانات عامة ومسابقات وGPU للدفاتر. مفيد عندما تكون البيانات مهمة بقدر النموذج.",
         official_url="https://www.kaggle.com", pricing="free", free_tier=True,
         arabic_support=False, platforms="Web, API, CLI",
         best_for="Datasets and notebook GPUs", featured=False, sort_order=113),
    dict(name="Replicate", name_ar="ريبليكيت", category="platforms",
         tagline_en="Run hosted models through one API.",
         tagline_ar="شغّل نماذج مستضافة عبر واجهة واحدة.",
         description_en="A catalogue of ready-to-run image, video and language models with a simple API and pay-per-use pricing. Good for prototypes without managing a server.",
         description_ar="كتالوج نماذج صور وفيديو ولغة جاهزة للتشغيل بواجهة بسيطة ودفع حسب الاستخدام. جيد للنماذج الأولية دون إدارة خادم.",
         official_url="https://replicate.com", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, API",
         best_for="Hosted model APIs", featured=False, sort_order=114),
    dict(name="Modal", name_ar="مودال", category="platforms",
         tagline_en="Serverless GPUs for Python functions.",
         tagline_ar="GPU بلا خادم لدوال بايثون.",
         description_en="Turn a Python function into a serverless GPU job with a decorator, and pay only while it runs. A clean fit for batch inference and small training jobs.",
         description_ar="حوّل دالة بايثون إلى مهمة GPU بلا خادم باستخدام مزخرف، وادفع فقط أثناء التشغيل. مناسب للاستدلال بالدفعات ومهام التدريب الصغيرة.",
         official_url="https://modal.com", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, CLI, Python",
         best_for="Serverless GPU jobs", featured=False, sort_order=115),
    dict(name="Vast.ai", name_ar="فاست إيه آي", category="platforms",
         tagline_en="A marketplace of rented GPUs.",
         tagline_ar="سوق لتأجير وحدات GPU.",
         description_en="Compare consumer and datacentre GPUs from many hosts, with per-hour pricing and filters for VRAM and bandwidth. Cheaper and less managed than a cloud provider.",
         description_ar="قارن وحدات GPU للمستهلكين ومراكز البيانات من مضيفين كثيرين بأسعار بالساعة ومرشحات للذاكرة والنطاق. أرخص وأقل إدارة من مزود سحابي.",
         official_url="https://vast.ai", pricing="paid", free_tier=False,
         arabic_support=False, platforms="Web, CLI",
         best_for="Cheap GPU hours", featured=False, sort_order=116),
    dict(name="Lambda", name_ar="لامبدا", category="platforms",
         tagline_en="GPU cloud built for training.",
         tagline_ar="سحابة GPU مبنية للتدريب.",
         description_en="On-demand and reserved GPU instances with fast interconnects, aimed at training and inference rather than general cloud hosting. A straightforward alternative to the big clouds.",
         description_ar="وحدات GPU عند الطلب ومحجوزة بترابط سريع، موجهة للتدريب والاستدلال لا للاستضافة العامة. بديل مباشر للسحابات الكبرى.",
         official_url="https://lambda.ai", pricing="paid", free_tier=False,
         arabic_support=False, platforms="Web, API",
         best_for="Training on rented GPUs", featured=False, sort_order=117),
    dict(name="Together AI", name_ar="توغيدر إيه آي", category="platforms",
         tagline_en="Open-model inference and fine-tuning.",
         tagline_ar="استدلال وضبط للنماذج المفتوحة.",
         description_en="Hosts popular open models behind an OpenAI-compatible API, with fine-tuning and dedicated endpoints. A practical way to ship an open model without owning GPUs.",
         description_ar="يستضيف نماذج مفتوحة شائعة خلف واجهة متوافقة مع OpenAI، مع ضبط ونقاط نهاية مخصصة. طريقة عملية لنشر نموذج مفتوح دون امتلاك GPU.",
         official_url="https://www.together.ai", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, API",
         best_for="Hosted open-model inference", featured=False, sort_order=118),
    dict(name="Groq", name_ar="جروك", category="platforms",
         tagline_en="Very fast inference on open models.",
         tagline_ar="استدلال سريع جدًا على النماذج المفتوحة.",
         description_en="Serves open models on custom LPU hardware, with noticeably low latency for chat and agents. The model catalogue is narrower than a general GPU cloud.",
         description_ar="يقدم نماذج مفتوحة على عتاد LPU مخصص بزمن استجابة منخفض للمحادثة والوكلاء. كتالوج النماذج أضيق من سحابة GPU عامة.",
         official_url="https://groq.com", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, API",
         best_for="Low-latency inference", featured=False, sort_order=119),
    dict(name="OpenRouter", name_ar="أوبن راوتر", category="platforms",
         tagline_en="One API for many models.",
         tagline_ar="واجهة واحدة لنماذج كثيرة.",
         description_en="Routes requests to dozens of hosted models with one key, and shows per-model pricing and availability. Useful for comparing models without separate accounts.",
         description_ar="يوجّه الطلبات إلى عشرات النماذج المستضافة بمفتاح واحد، ويعرض أسعار كل نموذج وتوفره. مفيد لمقارنة النماذج دون حسابات منفصلة.",
         official_url="https://openrouter.ai", pricing="freemium", free_tier=True,
         arabic_support=False, platforms="Web, API",
         best_for="Switching between models", featured=False, sort_order=120),
    dict(name="Ollama", name_ar="أولاما", category="platforms",
         tagline_en="Run open LLMs locally with one command.",
         tagline_ar="شغّل النماذج المفتوحة محليًا بأمر واحد.",
         description_en="Downloads and runs quantised models on your own machine with a simple CLI and local API. The fastest way to try an open model offline, if your laptop has enough memory.",
         description_ar="يحمل ويشغّل نماذج مكمّمة على جهازك بواجهة سطر أوامر وواجهة محلية. أسرع طريقة لتجربة نموذج مفتوح بلا إنترنت إذا كان جهازك يملك ذاكرة كافية.",
         official_url="https://ollama.com", pricing="free", free_tier=True,
         arabic_support=False, platforms="macOS, Windows, Linux",
         best_for="Local models with no setup", featured=False, sort_order=121),
    dict(name="LM Studio", name_ar="إل إم ستوديو", category="platforms",
         tagline_en="A desktop app for local models.",
         tagline_ar="تطبيق سطح مكتب للنماذج المحلية.",
         description_en="Browse, download and chat with local models through a graphical interface, with a local server for your own apps. Friendlier than a terminal for a first local model.",
         description_ar="تصفح وحمّل وتحدث مع النماذج المحلية عبر واجهة رسومية، مع خادم محلي لتطبيقاتك. أسهل من الطرفية لأول نموذج محلي.",
         official_url="https://lmstudio.ai", pricing="free", free_tier=True,
         arabic_support=False, platforms="Windows, macOS, Linux",
         best_for="A first local model", featured=False, sort_order=122),
    dict(name="vLLM", name_ar="في إل إل إم", category="platforms",
         tagline_en="High-throughput self-hosted inference.",
         tagline_ar="استدلال ذاتي عالي الإنتاجية.",
         description_en="An open-source serving engine with paged attention and an OpenAI-compatible API. The standard choice when you need to serve a model to many users on your own GPU.",
         description_ar="محرك خدمة مفتوح المصدر باهتمام مُصفّح وواجهة متوافقة مع OpenAI. الخيار المعتاد لخدمة نموذج لكثير من المستخدمين على GPU خاص.",
         official_url="https://github.com/vllm-project/vllm", pricing="free", free_tier=True,
         arabic_support=False, platforms="Linux, Python",
         best_for="Serving models at scale", featured=False, sort_order=123),
    dict(name="models.dev", name_ar="موديلز ديف", category="platforms",
         tagline_en="An open database of model specs and pricing.",
         tagline_ar="قاعدة بيانات مفتوحة لمواصفات النماذج وأسعارها.",
         description_en="A community-maintained catalogue of model providers, context windows, capabilities and prices. Use it to check what a model actually supports before choosing a provider or writing an integration.",
         description_ar="كتالوج يحتفظ به المجتمع لمزودي النماذج ونوافذ السياق والقدرات والأسعار. استخدمه للتحقق مما يدعمه النموذج فعلًا قبل اختيار مزود أو كتابة تكامل.",
         official_url="https://models.dev", pricing="free", free_tier=True,
         arabic_support=False, platforms="Web, API",
         best_for="Comparing model specs and prices", featured=False, sort_order=124),
    dict(name="LLMWare", name_ar="إل إل إم وير", category="platforms",
         tagline_en="Small RAG-optimised models and an open framework.",
         tagline_ar="نماذج صغيرة محسّنة لـRAG وإطار مفتوح.",
         description_en="An open-source framework and model catalog focused on small, specialised models for document Q&A, summarisation, SQL and function calling. A good fit when a 7B general model is more than the task needs.",
         description_ar="إطار مفتوح المصدر وكتالوج نماذج يركز على نماذج صغيرة متخصصة لأسئلة المستندات والتلخيص وSQL واستدعاء الدوال. مناسب عندما يكون نموذج عام بحجم 7B أكبر من حاجة المهمة.",
         official_url="https://llmware.ai", pricing="free", free_tier=True,
         arabic_support=False, platforms="Python, Web",
         best_for="Small models for RAG", featured=False, sort_order=125),
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
        print(f"Platforms: {created} created, {updated} updated, total {m.AITool.query.count()}")


if __name__ == "__main__":
    main()
