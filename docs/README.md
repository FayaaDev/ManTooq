# منطوق

حوّل النص العربي إلى صوت باستخدام ElevenLabs، سواء بصوت تستنسخه أو بصوت من [مكتبة أصوات ElevenLabs](https://elevenlabs.io/app/voice-library). استخدم الواجهة في المتصفح أو سطر الأوامر. تحتاج إلى Python 3.13 أو أحدث، وحساب ElevenLabs، ومفتاح API، واتصال بالإنترنت. قد يترتب على استخدام ElevenLabs رسوم.

## الموقع العام

توجد نسخة في `web/` قابلة للنشر على Cloudflare Pages (`wrangler pages deploy web --project-name mantooq`). كل زائر يمكنه إدخال مفتاح ElevenLabs الخاص به؛ يُحفظ في متصفحه ويُرسل مباشرةً إلى ElevenLabs عند توليد الصوت أو استنساخه، ولا يصل إلى خادم منطوق. زر «جرّب» يستخدم Pages Function في `functions/api/demo.js` للتوليد بمفتاح تجريبي محفوظ على الخادم؛ لا يُرسل المفتاح للمتصفح. تُحفظ معرّفات الأصوات والنبرات محليًا في المتصفح، والتسجيلات في IndexedDB؛ لا تنتقل بيانات تطبيق سطح المكتب تلقائيًا إلى الموقع. تجنّب إدخال مفتاحك على جهاز مشترك. الموقع مجاني للزيارة، لكن يخضع استخدام ElevenLabs لرصيد الحساب. لا يحتاج الموقع إلى Python أو `.env`.

لتفعيل «جرّب» في مشروع Pages:

1. أنشئ قاعدة D1 وشغّل `demo-schema.sql` عليها (`wrangler d1 create mantooq-demo` ثم `wrangler d1 execute mantooq-demo --remote --file=demo-schema.sql`).
2. أضف ربط D1 باسم `DEMO_DB` إلى مشروع Pages من **Settings → Bindings**؛ أعد النشر بعد إضافة الربط.
3. أضف أسرار Pages من جذر المستودع باستخدام `wrangler pages secret put DEMO_ELEVENLABS_API_KEY --project-name mantooq` و`wrangler pages secret put DEMO_SECRET --project-name mantooq`. أدخل القيم عند مطالبة Wrangler بها؛ الأولى مفتاح ElevenLabs التجريبي، والثانية قيمة عشوائية طويلة للتوقيع وبصمة IP. لا تضعهما في الملفات أو في المتصفح. أعد النشر بعد إضافتهما.
4. انشر الموقع من جذر المستودع بـ `wrangler pages deploy web --project-name mantooq`؛ يجب أن يبقى مجلد `functions/` في جذر المشروع، خارج `web/`.

تتيح التجربة طلب توليد ناجحًا واحدًا لكل متصفح وعنوان IP خلال 24 ساعة، لصوت مختار ونص لا يزيد عن 250 حرفًا. يتشارك مستخدمو الشبكة الواحدة هذا الحد؛ يمكن تجاوزه بتغيير IP. يُستخدم المفتاح الشخصي للتوليد بلا هذا الحد وللاستنساخ. اضبط سقف إنفاق ElevenLabs للمفتاح التجريبي.

## البدء

لتثبيت التطبيق دون Python أو `uv`، راجع [دليل macOS](MACOS.md) أو [دليل Windows x64](WINDOWS.md).

1. ثبّت [uv](https://docs.astral.sh/uv/) ثم شغّل `uv sync` داخل هذا المجلد.
2. انسخ `.env.example` إلى `.env` واستبدل القيمة الافتراضية بمفتاح ElevenLabs API الخاص بك. يمكنك أيضًا إدخال المفتاح في الواجهة.
3. شغّل التطبيق محليًا:

   ```bash
   uv run streamlit run app/app.py
   ```

في تبويب **استنساخ صوت**، ارفع تسجيلًا تملك حق استنساخ صوته، ثم سمّه. سيصبح الصوت الجديد خيارك المحفوظ. في تبويب **توليد الصوت**، أدخل نصًا عربيًا، واختر صوتك المستنسخ أو أدخل معرّف صوت من [مكتبة الأصوات](https://elevenlabs.io/app/voice-library). يمكنك تشغيل النتيجة أو تحميلها بصيغة MP3.

الاستنساخ اختياري. لاستخدام صوت موجود، افتحه في مكتبة الأصوات وانسخ معرّفه من ElevenLabs. يجب أن يتيح مفتاح API الخاص بك الوصول إلى الصوت الذي تختاره.

## سطر الأوامر

أضف `ELEVENLABS_API_KEY` إلى `.env` أو متغيرات بيئة النظام، ثم شغّل:

```bash
uv run python -m app.arabic_tts clone --sample my-voice.wav --name "صوتي العربي"
uv run python -m app.arabic_tts speak "هلا والله، وش الأخبار؟"
uv run python -m app.arabic_tts speak "مرحبا" --voice-id YOUR_VOICE_ID --output output/hello.mp3
```

يحفظ أمر `clone` معرّف الصوت في `.local/voice_id`. يستخدمه أمر `speak` تلقائيًا، ويمكنك اختيار صوت آخر عبر `--voice-id`. يُحفظ الملف الناتج افتراضيًا في `output/speech.mp3`، ويمكنك تغيير قيمة البذرة عبر `--seed`. إذا استخدمت السكربتات القديمة، فسيُنقل معرّف الصوت من `cloned_voice_id.txt` تلقائيًا عند أول تشغيل.

## الاختبارات

```bash
uv sync
uv run python -m playwright install chromium
uv run python -m unittest -v
node --test tests/unit/test_demo.mjs
```

تشمل الاختبارات دورة استنساخ الصوت وتوليده وتحميله عبر المتصفح، مع عميل ElevenLabs وهمي وتخزين مؤقت؛ لا تحتاج إلى مفتاح API حقيقي.

يتجاهل Git ملفات `.env`، ومعرّفات الأصوات المحفوظة، والتسجيلات، وملفات MP3 الناتجة. صُمّمت نسخة Streamlit للاستخدام المحلي؛ ففي استضافتها العامة سيشترك الزوار في الصوت الافتراضي المحفوظ. استخدم النسخة الثابتة للاستخدام الجماعي بمفاتيح مستقلة لكل زائر. المشروع غير تابع لـ ElevenLabs.
