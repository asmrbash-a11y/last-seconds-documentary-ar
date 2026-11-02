#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scene recipe: 15 scenes / 46 designed plates, all facts taken from the script."""
import json
from pathlib import Path
import visuals as V

ROOT = Path(__file__).resolve().parent
T = json.loads((ROOT / "assets" / "timeline.json").read_text(encoding="utf-8"))
LINES = T["lines"]

BUILDERS = {
    "hero": V.b_hero, "chapter": V.b_chapter, "clips": V.b_clips,
    "dossier": V.b_dossier, "radio": V.b_radio, "stat": V.b_stat,
    "question": V.b_question, "map": V.b_map, "evidence": V.b_evidence,
    "clock": V.b_clock, "note": V.b_note, "signal": V.b_signal, "end": V.b_end,
}

# -----------------------------------------------------------------------------
# Each beat: at = fraction of scene duration, b = builder, kw = builder kwargs
# -----------------------------------------------------------------------------
SCENES = [
 dict(id="s01", lines=(1, 2), tr="flash", fx="storm", beats=[
   dict(at=.00, b="hero", kw=dict(title="الثواني\nالأخيرة",
        sub="الرحلة التي سقطت قبل الوصول إلى البهاما", stamp_txt="سري",
        kicker="ملف رقم 01 / وثائقي")),
   dict(at=.42, b="clips", kw=dict(kicker="قصاصات من الملف", title="السماء تتحول فجأة",
        items=[
          dict(photo="plane_storm.jpg", x=32, y=250, w=300, h=360, rot=-7, seed=3,
               caption="تحولت السماء فجأة إلى مسرح لكارثة مروعة", label="عاجل", stamp="عاجل"),
          dict(photo="smoke_suburb.jpg", x=375, y=330, w=285, h=340, rot=6, seed=8,
               caption="رحلة كان يفترض أن تنتهي بهبوط آمن", label="جزر البهاما"),
        ])),
   dict(at=.78, b="stat", kw=dict(value="9", unit="أشخاص",
        caption="على متن طائرة خاصة، لم يعلموا أنها رحلتهم الأخيرة",
        photo="plane_storm.jpg", kicker="تسعة أشخاص", red=True,
        small="واحدة من أكثر اللحظات رعباً في تاريخ الطيران الحديث")),
 ]),
 dict(id="s02", lines=(3, 4), tr="wipe", fx="dust", beats=[
   dict(at=.00, b="clips", kw=dict(kicker="الدليل", title="التسجيل الصوتي",
        bg_photo="radar.jpg", darkness=.30, items=[
          dict(photo="recorder.jpg", x=55, y=250, w=290, h=340, rot=-5, seed=11,
               caption="كشف الدقائق والثواني الأخيرة", label="تسجيل"),
          dict(photo="radar.jpg", x=380, y=330, w=270, h=320, rot=7, seed=13,
               caption="بين قائد الطائرة وبرج المراقبة", label="برج"),
        ])),
   dict(at=.48, b="question", kw=dict(text="فماذا حدث في تلك الرحلة؟",
        sub="ولماذا فقد الطيار السيطرة على الطائرة؟")),
 ]),
 dict(id="s03", lines=(5, 8), tr="scan", fx="plane", beats=[
   dict(at=.00, b="chapter", kw=dict(num="01", title="بداية الرحلة",
        sub="الأول من نوفمبر عام 2026", quote="مطار أوستن بيرغستروم الدولي، تكساس")),
   dict(at=.16, b="map", kw=dict(highlight="من أوستن إلى نورث إليوثيرا")),
   dict(at=.44, b="dossier", kw=dict(title="بيانات الرحلة", num="01",
        fields=[("التاريخ", "1 نوفمبر 2026"), ("الطراز", "ليرجيت 60"),
                ("المغادرة", "مطار أوستن بيرغستروم الدولي"),
                ("الوجهة", "مطار نورث إليوثيرا")],
        photo="chart.jpg", note="طائرة خاصة · تسعة أشخاص على متنها")),
   dict(at=.76, b="stat", kw=dict(value="35,000", unit="قدم",
        caption="ارتفاع الطائرة، وسط ظروف جوية بدأت تتدهور تدريجياً",
        photo="cockpit_instruments.jpg", kicker="ارتفاع التحليق")),
 ]),
 dict(id="s04", lines=(9, 11), tr="fade", fx="rain", beats=[
   dict(at=.00, b="clips", kw=dict(kicker="إبلاغ الطيار", title="الجليد والاضطرابات",
        items=[
          dict(photo="ice_wing.jpg", x=35, y=250, w=300, h=360, rot=-6, seed=21,
               caption="تراكم للجليد على أجزاء من الطائرة", label="جليد"),
          dict(photo="radar.jpg", x=375, y=320, w=285, h=340, rot=6, seed=23,
               caption="اضطرابات جوية متوسطة", label="طقس"),
        ])),
   dict(at=.48, b="radio", kw=dict(speaker="الطيار", index="4",
        text="اضطرابات جوية متوسطة وتراكم للجليد.", temp="—")),
   dict(at=.80, b="note", kw=dict(title="تحت السيطرة",
        text="كان الوضع يبدو تحت السيطرة في البداية. لكن الأمور لم تستمر طويلاً.")),
 ]),
 dict(id="s05", lines=(12, 15), tr="dip", fx="rain", beats=[
   dict(at=.00, b="chapter", kw=dict(num="02", title="بداية الكارثة",
        sub="مع دخول الطائرة منطقة هطول الأمطار",
        quote="طلب الطيار الصعود إلى مستوى أعلى", photo="plane_storm.jpg")),
   dict(at=.20, b="clips", kw=dict(kicker="بحثاً عن استقرار", title="تغيير الارتفاع",
        bg_photo="plane_storm.jpg", darkness=.34, items=[
          dict(photo="plane_storm.jpg", x=40, y=260, w=290, h=350, rot=-8, seed=31,
               caption="منطقة هطول الأمطار", label="مطر"),
          dict(photo="cockpit_instruments.jpg", x=380, y=330, w=280, h=330, rot=7, seed=33,
               caption="بدأت الطائرة تفقد ارتفاعها فجأة", label="هبوط"),
        ])),
   dict(at=.60, b="note", kw=dict(title="فقدان الارتفاع",
        text="بدأت الطائرة تفقد ارتفاعها بصورة مفاجئة وخطيرة.")),
   dict(at=.80, b="radio", kw=dict(speaker="الطيار", index="5",
        text="هنا تحولت الرحلة إلى حالة طوارئ حقيقية.", temp="—")),
 ]),
 dict(id="s06", lines=(16, 21), tr="scan", fx="radiofx", beats=[
   dict(at=.00, b="chapter", kw=dict(num="03", title="التسجيل الصوتي",
        sub="بين الطيار وبرج المراقبة", quote="مقتطفات مترجمة", photo="radar.jpg")),
   dict(at=.14, b="note", kw=dict(title="ملاحظة",
        text="الحوار التالي مقتطفات مترجمة من التسجيلات المنشورة، وليس تفريغاً حرفياً كاملاً.")),
   dict(at=.34, b="radio", kw=dict(speaker="الطيار", index="6",
        text="لدينا تراكم للجليد واضطرابات جوية متوسطة.", temp="—")),
   dict(at=.58, b="radio", kw=dict(speaker="برج المراقبة", index="7",
        text="ما درجة الحرارة الخارجية لديكم؟", temp="—")),
   dict(at=.76, b="radio", kw=dict(speaker="الطيار", index="8",
        text="ناقص 47 درجة مئوية. نحن نتعامل مع الجليد، لكن الاضطرابات متوسطة.",
        temp="-47°C")),
 ]),
 dict(id="s07", lines=(22, 25), tr="glitch", fx="alarm", beats=[
   dict(at=.00, b="radio", kw=dict(speaker="الطيار", index="9", alert=True,
        text="نحن نفقد الارتفاع... نعلن حالة الطوارئ! نداء استغاثة!")),
   dict(at=.32, b="stat", kw=dict(value="10,000", unit="قدم / دقيقة",
        caption="نهبط بمعدل عشرة آلاف قدم في الدقيقة!", red=True,
        photo="cockpit_instruments.jpg", kicker="معدل الهبوط")),
   dict(at=.60, b="radio", kw=dict(speaker="برج المراقبة", index="10",
        text="أخبرني بما تحتاج إليه، نحن معك.", temp="—")),
   dict(at=.82, b="stat", kw=dict(value="20,000", unit="قدم / دقيقة",
        caption="نحن في حالة هبوط متسارع... عشرون ألف قدم في الدقيقة!", red=True,
        photo="cockpit_instruments.jpg", kicker="هبوط متسارع")),
 ]),
 dict(id="s08", lines=(26, 29), tr="flash", fx="alarm", beats=[
   dict(at=.00, b="question", kw=dict(text="سوف نصطدم بالأرض!",
        sub="ثم جاءت العبارة الأكثر رعباً في التسجيل")),
   dict(at=.30, b="radio", kw=dict(speaker="برج المراقبة", index="11",
        text="أنا معك... تحدث إليّ!", temp="—")),
   dict(at=.56, b="stat", kw=dict(value="22,000", unit="قدم / دقيقة",
        caption="والطائرة تميل بزاوية ستين درجة!", red=True,
        photo="cockpit_instruments.jpg", kicker="اللحظات الأخيرة",
        small="60°  ·  اثنان وعشرون ألف قدم في الدقيقة")),
 ]),
 dict(id="s09", lines=(30, 32), tr="glitch", fx="static", beats=[
   dict(at=.00, b="note", kw=dict(title="قمرة القيادة",
        text="«لم يعد لدينا وقت!»")),
   dict(at=.48, b="signal", kw=dict()),
 ]),
 dict(id="s10", lines=(33, 36), tr="dip", fx="smoke", beats=[
   dict(at=.00, b="chapter", kw=dict(num="04", title="لحظة الاصطدام",
        sub="12:50 ظهراً بالتوقيت المحلي", photo="smoke_suburb.jpg",
        quote="منطقة سكنية بمقاطعة بالم بيتش في فلوريدا")),
   dict(at=.18, b="clock", kw=dict(time="12:50",
        caption="سقطت الطائرة في منطقة سكنية")),
   dict(at=.45, b="clips", kw=dict(kicker="موقع الحادث", title="مشهد من الدمار",
        bg_photo="smoke_suburb.jpg", darkness=.30, items=[
          dict(photo="smoke_suburb.jpg", x=35, y=250, w=300, h=360, rot=-6, seed=41,
               caption="ارتطمت بالأرض بقوة هائلة", label="انفجار"),
          dict(photo="plane_storm.jpg", x=380, y=330, w=280, h=330, rot=7, seed=43,
               caption="تصاعدت أعمدة الدخان الأسود في السماء", label="دخان"),
        ])),
   dict(at=.78, b="stat", kw=dict(value="600", unit="شخص",
        caption="أُخلي نحو 600 شخص من منطقة سكنية قريبة كإجراء احترازي",
        photo="smoke_suburb.jpg", kicker="إخلاء احترازي")),
 ]),
 dict(id="s11", lines=(37, 39), tr="wipe", fx="dust", beats=[
   dict(at=.00, b="stat", kw=dict(value="9", unit="أشخاص",
        caption="أكدت السلطات وفاة الأشخاص التسعة الذين كانوا على متن الطائرة",
        photo="plane_storm.jpg", red=True, kicker="الحصيلة")),
   dict(at=.45, b="clips", kw=dict(kicker="شهادة", title="كارثة مروعة",
        items=[
          dict(photo="newspaper_blank.jpg", x=60, y=260, w=280, h=340, rot=-5, seed=51,
               caption="وصف حاكم فلوريدا رون ديسانتيس الحادث بأنه كارثة مروعة",
               label="تصريح", ht=False),
          dict(photo="smoke_suburb.jpg", x=370, y=330, w=285, h=330, rot=6, seed=53,
               caption="موقع الحادث تحول إلى مشهد من الدمار", label="موقع"),
        ])),
 ]),
 dict(id="s12", lines=(40, 41), tr="iris", fx="dust", beats=[
   dict(at=.00, b="question", kw=dict(text="ما السبب الحقيقي وراء سقوط الطائرة؟",
        sub="هنا يبرز السؤال الأهم.")),
 ]),
 dict(id="s13", lines=(42, 45), tr="scan", fx="dust", beats=[
   dict(at=.00, b="evidence", kw=dict(title="ثلاثة عوامل أولية", items=[
          dict(n="01", t="تراكم الجليد", d="واجهه الطاقم قبل الهبوط الحاد"),
          dict(n="02", t="الاضطرابات", d="جوية متوسطة بحسب التسجيلات"),
          dict(n="03", t="الأمطار", d="منطقة هطول الأمطار"),
        ], note="لا يمكن الجزم بأن الجليد أو الطقس وحدهما تسببا في الحادث.")),
   dict(at=.42, b="note", kw=dict(title="بلا نتيجة نهائية",
        text="حتى الآن، لم يصدر المحققون نتيجة نهائية تحدد السبب المباشر.")),
   dict(at=.68, b="dossier", kw=dict(title="التحقيق", num="NTSB",
        fields=[("الجهة", "المجلس الوطني لسلامة النقل الأمريكي"),
                ("بالتعاون مع", "إدارة الطيران الفيدرالية"),
                ("الهدف", "معرفة ما حدث داخل الطائرة")],
        photo="radar.jpg", note="خلال لحظاتها الأخيرة")),
 ]),
 dict(id="s14", lines=(46, 48), tr="fade", fx="dust", beats=[
   dict(at=.00, b="chapter", kw=dict(num="05", title="الخاتمة",
        sub="تسعة أشخاص صعدوا إلى الطائرة", quote="وهم يعتقدون أنهم في رحلة عادية",
        photo="chart.jpg")),
   dict(at=.28, b="clips", kw=dict(kicker="ثوانٍ معدودة", title="انتهت قبل الوصول",
        items=[
          dict(photo="plane_storm.jpg", x=45, y=260, w=290, h=350, rot=-6, seed=61,
               caption="خلال ثوانٍ معدودة تحولت الرحلة إلى مأساة", label="رحلة"),
          dict(photo="recorder.jpg", x=375, y=330, w=280, h=330, rot=7, seed=63,
               caption="المحاولات اليائسة لإنقاذ الطائرة", label="شاهد"),
        ])),
   dict(at=.70, b="hero", kw=dict(title="انتهت\nقبل الوصول",
        sub="تسعة أشخاص صعدوا وهم يعتقدون أنهم في رحلة عادية نحو وجهتهم",
        kicker="الخاتمة", stamp_txt="وداعاً", darkness=.40)),
 ]),
 dict(id="s15", lines=(49, 50), tr="dip", fx="dust", beats=[
   dict(at=.00, b="clips", kw=dict(kicker="شاهد", title="التسجيل الصوتي",
        items=[
          dict(photo="recorder.jpg", x=55, y=250, w=290, h=350, rot=-5, seed=71,
               caption="يبقى شاهداً على اللحظات الأخيرة", label="تسجيل"),
          dict(photo="cockpit_instruments.jpg", x=380, y=330, w=275, h=330, rot=7, seed=73,
               caption="المحاولات اليائسة لإنقاذ الطائرة", label="قمرة"),
        ])),
   dict(at=.48, b="end", kw=dict(title="الثواني الأخيرة",
        sub="قد تفصل دقائق قليلة بين رحلة طبيعية وكارثة لا يمكن التراجع عنها.")),
 ]),
]

# -----------------------------------------------------------------------------
def build():
    """Compute absolute scene times and render every plate once."""
    spoken = [L for L in LINES if L["kind"] == "spoken" and L["words"]]
    def boundary_before(i):
        j = spoken.index(LINES[i - 1])
        if j == 0: return 0.0
        a = spoken[j - 1]["end"]; b = spoken[j]["start"]
        return (a + b) / 2
    def boundary_after(i):
        j = spoken.index(LINES[i - 1])
        if j == len(spoken) - 1: return T["duration"]
        a = spoken[j]["end"]; b = spoken[j + 1]["start"]
        return (a + b) / 2
    out = []
    for sd in SCENES:
        first = next(l for l in range(sd["lines"][0], sd["lines"][1] + 1)
                     if LINES[l - 1]["kind"] == "spoken")
        last = next(l for l in range(sd["lines"][1], sd["lines"][0] - 1, -1)
                    if LINES[l - 1]["kind"] == "spoken")
        st, en = boundary_before(first), boundary_after(last)
        plates = []
        for k, beat in enumerate(sd["beats"]):
            at = st + (en - st) * beat["at"]
            im = BUILDERS[beat["b"]](V.Plate(), **beat["kw"])
            plates.append({"at": at, "im": im, "seed": 100 + k})
        out.append({**sd, "start": st, "end": en, "dur": en - st, "plates": plates})
        print(f"{sd['id']}  {st:7.2f} -> {en:7.2f}  ({en-st:5.1f}s)  "
              f"{len(plates)} plates  fx={sd['fx']}  tr={sd['tr']}")
    return out

if __name__ == "__main__":
    s = build()
    print("total", len(s), "scenes", sum(len(x["plates"]) for x in s), "plates")
