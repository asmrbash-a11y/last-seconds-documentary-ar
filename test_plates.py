#!/usr/bin/env python3
import sys, traceback
from PIL import Image, ImageOps, ImageDraw
sys.path.insert(0, "/home/user/work/project")
import visuals as V

CASES = [
 ("hero",      lambda: V.b_hero(V.Plate(), title="الثواني\nالأخيرة")),
 ("chapter",   lambda: V.b_chapter(V.Plate(), num="01", title="بداية الرحلة", sub="من أوستن إلى البهاما")),
 ("clips",     lambda: V.b_clips(V.Plate(), [dict(photo="plane_storm.jpg", x=45, y=250, w=270, h=320, rot=-7, caption="السماء تتحول إلى مسرح لكارثة", label="عاجل"), dict(photo="recorder.jpg", x=360, y=340, w=260, h=300, rot=6, caption="التسجيل الصوتي", label="دليل")], title="ملف الحادث", kicker="قصاصات")),
 ("dossier",   lambda: V.b_dossier(V.Plate(), title="بيانات الرحلة", fields=[("التاريخ","1 نوفمبر 2026"),("الطراز","ليرجيت 60"),("الوجهة","نورث إليوثيرا")], photo="chart.jpg", num="01")),
 ("radio",     lambda: V.b_radio(V.Plate(), speaker="الطيار", text="لدينا تراكم للجليد واضطرابات جوية متوسطة.", index="1")),
 ("stat",      lambda: V.b_stat(V.Plate(), value="35,000", unit="قدم", caption="ارتفاع الطائرة قبل التدهور")),
 ("question",  lambda: V.b_question(V.Plate(), text="فماذا حدث في تلك الرحلة؟", sub="ولماذا فقد الطيار السيطرة؟")),
 ("map",       lambda: V.b_map(V.Plate(), highlight="مسار الرحلة")),
 ("evidence",  lambda: V.b_evidence(V.Plate(), title="ما السبب؟", items=[dict(n="01",t="الجليد",d="تراكم على أجزاء من الطائرة"),dict(n="02",t="الاضطرابات",d="جوية متوسطة"),dict(n="03",t="الأمطار",d="منطقة هطول")], note="لا نتيجة نهائية حتى الآن")),
 ("clock",     lambda: V.b_clock(V.Plate(), caption="سقطت الطائرة في منطقة سكنية")),
 ("note",      lambda: V.b_note(V.Plate(), text="الحوار التالي مقتطفات مترجمة من التسجيلات المنشورة، وليس تفريغاً حرفياً كاملاً.")),
 ("signal",    lambda: V.b_signal(V.Plate())),
 ("end",       lambda: V.b_end(V.Plate(), sub="قد تفصل دقائق قليلة بين رحلة طبيعية وكارثة")),
]
imgs=[]
for name, fn in CASES:
    try:
        im = fn()
        print(name, "OK", im.size)
        imgs.append((name, im))
    except Exception as e:
        print(name, "FAIL", e); traceback.print_exc()
cols=4; tw=252; th=448
rows=(len(imgs)+cols-1)//cols
sheet=Image.new("RGB",(cols*tw, rows*(th+26)), (16,17,19)); d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(imgs):
    t=im.resize((tw,th), Image.LANCZOS)
    x=(i%cols)*tw; y=(i//cols)*(th+26)
    sheet.paste(t,(x,y)); d.text((x+6,y+th+5),name,fill=(230,225,210))
sheet.save("/home/user/work/project/assets/plates_test.jpg",quality=90)
print("sheet saved")
