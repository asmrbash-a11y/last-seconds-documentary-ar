# الوثائقي: «الثواني الأخيرة» — الرحلة التي سقطت قبل الوصول إلى البهاما

فيديو موشن جرافيك عمودي (9:16) من صور وقصاصات ورقية، بكابشن عربي متزامن مع الصوت
كلمة بكلمة. الناتج: `final.mp4` — أقل من 20 ميجابايت.

## النتيجة
| | |
|---|---|
| الأبعاد | 720 × 1280 (9:16) |
| المدة | 295.30 ثانية |
| الإطارات | 25 fps |
| الفيديو | H.264 / yuv420p / CRF + سقف بت ريت |
| الصوت | AAC 96 kb/s mono (التعليق + مؤثرات) |
| المشاهد | 15 مشهداً / 45 لوحة مرسومة بالكود |

## المهارة المُثبّتة
`https://github.com/majedphotos/video-ad-editor` — استُخدمت سكل **motion-video** مع
محرّك **video-ad-editor**: `references/start.md` (الأدوات والهوية)،
`motion-mode.md` (جملة ≈ مشهد، لا قوالب)، `motion-rules.md` (قائمة الحقائق،
ممنوعات الحركة، المنطقة الآمنة)، `styles.md` (archive + newsprint)،
`moves.md` (لوحة الحركات عبر `35_moves.py plan`)، وخطوط OFL المرفقة بالمستودع.
بيئة الساندبوكس بلا Chrome/Remotion، فطُبّق بديل `any-environment.md`: محرّك رسم
Python/PIL + ffmpeg بنفس القواعد وبنفس ملف `theme.json`.

## إعادة التوليد
```bash
python3 transcribe.py        # Whisper small: كلمات بتوقيتها
python3 align.py             # مطابقة نص المستخدم بالكلمات المنطوقة
python3 render.py preview    # لوحة مصغّرات للمعاينة
python3 audio.py             # التعليق + المؤثرات
python3 render.py full --crf 24 --maxrate 400k
ffmpeg -i renders/video.mp4 -i assets/soundtrack.m4a -c copy -movflags +faststart final.mp4
```

## الملفات
- `script.txt` — النص الأصلي كما ورد (50 سطراً).
- `assets/timeline.json` — توقيت كل سطر وكل كلمة + بطاقات الفصول.
- `theme.json` · `facts.md` · `storyboard.md` · `subtitles.srt`.
- `visuals.py` — مكتبة الرسم (ورق ممزّق، هافتون، أختام، شريط لاصق، خطوط عربية).
- `scenes.py` — وصفات المشاهد واللوحات.
- `engine.py` — الكاميرا، المؤثرات، الانتقالات، الكابشن، شريط التقدّم.
- `render.py` · `audio.py` · `align.py` · `transcribe.py`.

> الصور الثمانية مولّدة بالذكاء الاصطناعي خصيصاً للمشروع (بلا نصوص أو شعارات جاهزة)،
> ثم عولجت برمجياً إلى قصاصات صحف بنصف نغمة. لا توجد صور من الحدث الحقيقي.
