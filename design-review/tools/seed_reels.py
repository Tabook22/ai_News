"""Seed the Worth Watching page with a first set of curated YouTube videos.

Run from the repository root:
    venv\\Scripts\\python.exe design-review/tools/seed_reels.py
Idempotent: matches by source_url and updates the card text.
"""
import datetime
import sys

sys.path.insert(0, "app")
import app as m  # noqa: E402

VIDEOS = [
    dict(
        title="OpenAI's Astra Just Opened The Black Box Of AI",
        title_ar="أسترا من OpenAI تفتح الصندوق الأسود للذكاء الاصطناعي",
        creator_name="Two Minute Papers",
        creator_handle="",
        source_url="https://www.youtube.com/watch?v=GJ6PMUm5oTA",
        thumbnail="https://img.youtube.com/vi/GJ6PMUm5oTA/hqdefault.jpg",
        summary_en="A short, visual walk through OpenAI's Astra interpretability work — what the model was doing and why researchers can now see inside it. Worth it if you want the research idea without reading the paper first.",
        summary_ar="جولة قصيرة ومرئية في عمل أسترا من OpenAI لفهم داخل النموذج — ماذا كان يفعل ولماذا يستطيع الباحثون رؤية داخله الآن. تستحق المشاهدة إذا أردت الفكرة البحثية دون قراءة الورقة أولًا.",
        display_order=1,
    ),
    dict(
        title="Trillions lost as investors question the AI boom",
        title_ar="تريليونات تُفقد بينما يشكك المستثمرون في طفرة الذكاء الاصطناعي",
        creator_name="DW News",
        creator_handle="",
        source_url="https://www.youtube.com/watch?v=I8LXJeDXeIU",
        thumbnail="https://img.youtube.com/vi/I8LXJeDXeIU/hqdefault.jpg",
        summary_en="A clear news explainer on the market wobble around AI spending: what changed, who is exposed, and why the AI economy is being questioned. Useful context for a CS student entering the job market.",
        summary_ar="شرح إخباري واضح لتذبذب السوق حول الإنفاق على الذكاء الاصطناعي: ما الذي تغير، ومن المتأثر، ولماذا يُشكك في اقتصاد الذكاء الاصطناعي. سياق مفيد لطالب علوم الحاسوب الداخل إلى سوق العمل.",
        display_order=2,
    ),
    dict(
        title="The one thing holding theoretical CS together just broke... kinda",
        title_ar="الشيء الذي يجمع علوم الحاسوب النظرية انكسر... نوعًا ما",
        creator_name="Fireship",
        creator_handle="",
        source_url="https://www.youtube.com/watch?v=iw9SZgyahqg",
        thumbnail="https://img.youtube.com/vi/iw9SZgyahqg/hqdefault.jpg",
        summary_en="A fast explainer of a theoretical computer science result and what it might mean for complexity theory. Opinionated and quick — a good starting point for a seminar discussion, not the final word.",
        summary_ar="شرح سريع لنتيجة في علوم الحاسوب النظرية وما قد تعنيه لنظرية التعقيد. سريع وذو رأي — نقطة بداية جيدة لنقاش في الندوة، لا الكلمة الأخيرة.",
        display_order=3,
    ),
    dict(
        title="AI NEWS: OpenAI & Google Released NEW AI Models (+ 5 More Updates)",
        title_ar="أخبار الذكاء الاصطناعي: OpenAI وGoogle يطلقان نماذج جديدة (+ 5 تحديثات)",
        creator_name="The Next Signal",
        creator_handle="",
        source_url="https://www.youtube.com/watch?v=yNRdKqBBA5A",
        thumbnail="https://img.youtube.com/vi/yNRdKqBBA5A/hqdefault.jpg",
        summary_en="A weekly roundup of new models and tools. Use it as a map of what launched this week, then check the primary source before quoting a benchmark or a price.",
        summary_ar="ملخص أسبوعي للنماذج والأدوات الجديدة. استخدمه كخريطة لما أُطلق هذا الأسبوع، ثم تحقق من المصدر الأصلي قبل اقتباس أي مقياس أو سعر.",
        display_order=4,
    ),
    dict(
        title="Latest AI News (7th November) — ChatGPT GIFs, Gemini Updates, Canva Brush",
        title_ar="آخر أخبار الذكاء الاصطناعي (7 نوفمبر) — صور ChatGPT المتحركة وتحديثات Gemini وفرشاة Canva",
        creator_name="UpskillAI",
        creator_handle="",
        source_url="https://www.youtube.com/watch?v=EMgSvQBuUTs",
        thumbnail="https://img.youtube.com/vi/EMgSvQBuUTs/hqdefault.jpg",
        summary_en="Practical, tool-focused updates a student can try: GIF generation, Gemini changes and Canva's new brush. A quick way to spot something useful for a course project or a society poster.",
        summary_ar="تحديثات عملية تركز على الأدوات يمكن للطالب تجربتها: توليد الصور المتحركة وتغييرات Gemini وفرشاة Canva الجديدة. طريقة سريعة لالتقاط شيء مفيد لمشروع مقرر أو ملصق نشاط.",
        display_order=5,
    ),
]


def main():
    with m.app.app_context():
        created = updated = 0
        for data in VIDEOS:
            reel = m.CuratedReel.query.filter_by(source_url=data["source_url"]).first()
            if reel is None:
                reel = m.CuratedReel(source_url=data["source_url"])
                m.db.session.add(reel)
                created += 1
            else:
                updated += 1
            for key, value in data.items():
                setattr(reel, key, value)
            reel.platform = "youtube"
            reel.status = "published"
            reel.is_published = True
            reel.created_at = datetime.datetime(2026, 11, 7, 12, 0)
        m.db.session.commit()
        print(f"Reels: {created} created, {updated} updated, total {m.CuratedReel.query.count()}")


if __name__ == "__main__":
    main()
