"""Load the top-downloaded text-generation models from Hugging Face.

Run after the tools seeds:
    venv\\Scripts\\python.exe design-review/tools/seed_models.py

Downloads and likes are a dated snapshot from the Hugging Face API
(2026-11-07). The script is idempotent: it matches by model name.
"""
import datetime
import sys

sys.path.insert(0, "app")
import app as m  # noqa: E402

CHECKED = datetime.date(2026, 11, 7)

MODELS = [
    dict(name="Qwen3-0.6B", org="Qwen", params="0.6B", licence="Apache-2.0",
         downloads=21357034, likes=1883, url="https://huggingface.co/Qwen/Qwen3-0.6B",
         note_en="Tiny and easy to run; often the first model someone downloads.",
         note_ar="صغير وسهل التشغيل، وغالبًا أول نموذج يحمّله المستخدم."),
    dict(name="Qwen3-14B", org="Qwen", params="14B", licence="Apache-2.0",
         downloads=12952853, likes=533, url="https://huggingface.co/Qwen/Qwen3-14B",
         note_en="A strong mid-size Qwen3 for local inference on a serious GPU.",
         note_ar="حجم متوسط قوي من Qwen3 للاستدلال المحلي على GPU قوية."),
    dict(name="DeepSeek-V3.2", org="DeepSeek", params="MoE", licence="DeepSeek licence",
         downloads=7460151, likes=1595, url="https://huggingface.co/deepseek-ai/DeepSeek-V3.2",
         note_en="A flagship reasoning model; large enough to need a hosted endpoint.",
         note_ar="نموذج استدلال رائد، وحجمه يستلزم نقطة نهاية مستضافة."),
    dict(name="Qwen3-8B", org="Qwen", params="8B", licence="Apache-2.0",
         downloads=6976036, likes=2175, url="https://huggingface.co/Qwen/Qwen3-8B",
         note_en="The practical local size for a single 24GB GPU.",
         note_ar="الحجم المحلي العملي لبطاقة واحدة بسعة 24GB."),
    dict(name="Qwen3-4B", org="Qwen", params="4B", licence="Apache-2.0",
         downloads=6379202, likes=790, url="https://huggingface.co/Qwen/Qwen3-4B",
         note_en="A good balance of quality and laptop-class memory.",
         note_ar="توازن جيد بين الجودة وذاكرة جهاز محمول."),
    dict(name="Qwen2.5-7B-Instruct", org="Qwen", params="7B", licence="Apache-2.0",
         downloads=6165908, likes=2487, url="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct",
         note_en="A mature, widely supported instruct model with many fine-tunes.",
         note_ar="نموذج تعليمات ناضج ومدعوم على نطاق واسع بنسخ مضبوطة كثيرة."),
    dict(name="gpt-oss-20b", org="OpenAI", params="20B MoE", licence="Apache-2.0",
         downloads=5927863, likes=5284, url="https://huggingface.co/openai/gpt-oss-20b",
         note_en="OpenAI's open-weight model, designed to run on a single GPU.",
         note_ar="نموذج OpenAI المفتوح الأوزان، مصمم للتشغيل على GPU واحدة."),
    dict(name="Qwen2.5-1.5B-Instruct", org="Qwen", params="1.5B", licence="Apache-2.0",
         downloads=4918196, likes=932, url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct",
         note_en="Small enough for a laptop; useful for tests and edge demos.",
         note_ar="صغير بما يكفي لجهاز محمول، مفيد للاختبارات والعروض الطرفية."),
    dict(name="Llama-3.1-8B-Instruct", org="Meta", params="8B", licence="Llama 3.1 Community",
         downloads=4346354, likes=8829, url="https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct",
         note_en="The most-liked model here; a large ecosystem of fine-tunes.",
         note_ar="الأكثر إعجابًا في القائمة، مع نظام بيئي كبير من النسخ المضبوطة."),
    dict(name="Qwen3-1.7B", org="Qwen", params="1.7B", licence="Apache-2.0",
         downloads=4120041, likes=614, url="https://huggingface.co/Qwen/Qwen3-1.7B",
         note_en="A small Qwen3 for quick local experiments.",
         note_ar="نموذج Qwen3 صغير للتجارب المحلية السريعة."),
    dict(name="Qwen3-32B", org="Qwen", params="32B", licence="Apache-2.0",
         downloads=2980956, likes=791, url="https://huggingface.co/Qwen/Qwen3-32B",
         note_en="A larger open model for quality-sensitive work.",
         note_ar="نموذج مفتوح أكبر للأعمال الحساسة للجودة."),
    dict(name="DeepSeek-V4-Flash-0731", org="DeepSeek", params="MoE", licence="DeepSeek licence",
         downloads=2744544, likes=4096, url="https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731",
         note_en="A faster DeepSeek variant with strong community interest.",
         note_ar="نسخة أسرع من DeepSeek باهتمام مجتمعي قوي."),
    dict(name="Qwen3-4B-Instruct-2507", org="Qwen", params="4B", licence="Apache-2.0",
         downloads=2595158, likes=1046, url="https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507",
         note_en="A newer 4B instruct build with improved following of instructions.",
         note_ar="إصدار تعليمات 4B أحدث بتحسن في اتباع التعليمات."),
    dict(name="SmolLM2-135M", org="HuggingFaceTB", params="135M", licence="Apache-2.0",
         downloads=2523492, likes=267, url="https://huggingface.co/HuggingFaceTB/SmolLM2-135M",
         note_en="Tiny enough to run in a browser or on a phone.",
         note_ar="صغير بما يكفي للعمل في متصفح أو هاتف."),
    dict(name="gpt-oss-120b", org="OpenAI", params="120B MoE", licence="Apache-2.0",
         downloads=2446904, likes=5496, url="https://huggingface.co/openai/gpt-oss-120b",
         note_en="The larger gpt-oss build; needs a multi-GPU host or an API.",
         note_ar="إصدار gpt-oss الأكبر، يحتاج مضيفًا متعدد البطاقات أو واجهة."),
    dict(name="Qwen2.5-3B-Instruct", org="Qwen", params="3B", licence="Apache-2.0",
         downloads=2753247, likes=637, url="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct",
         note_en="A compact instruct model that fits modest hardware.",
         note_ar="نموذج تعليمات مدمج يناسب العتاد المتواضع."),
]


def main():
    with m.app.app_context():
        created = updated = 0
        for data in MODELS:
            row = m.LLMModel.query.filter_by(name=data["name"]).first()
            if row is None:
                row = m.LLMModel(name=data["name"])
                m.db.session.add(row)
                created += 1
            else:
                updated += 1
            for key, value in data.items():
                setattr(row, key, value)
            row.pipeline = "text-generation"
            row.checked_at = CHECKED
        m.db.session.commit()
        print(f"Models: {created} created, {updated} updated, total {m.LLMModel.query.count()}")


if __name__ == "__main__":
    main()
