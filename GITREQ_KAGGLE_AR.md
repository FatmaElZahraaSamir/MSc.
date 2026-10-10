# تشغيل GitReq على كاجل — خطوة بخطوة

كل اللي محتاجاه في الفولدر ده. **مش محتاجة تعدّلي ولا سطر كود** — كل notebook بتلاقي مدخلاتها لوحدها.

```
notebooks/         ← السبع notebooks
kaggle_datasets/   ← خمس داتاسِتس ترفعيهم على كاجل مرة واحدة
```

---

## أولًا: ارفعي الخمس داتاسِتس (مرة واحدة)

على كاجل: **Create → New Dataset** → ارفعي محتوى كل فولدر كداتاسِت لوحده. الاسم مش مهم.

| الفولدر | اسم مقترح | فيه إيه | ليه |
|---|---|---|---|
| `1_gitreq` | `gitreq` | أرشيف GitReq (٦,٣٠٢ requirement) | الـ corpus التالت |
| `2_stage1-frozen-splits` | `stage1-frozen-splits` | `splits.json` القديم | الـ ١٠٧ فولد القديمة **متتغيّرش** |
| `3_resume-stage2` | `resume-stage2` | نتايج الإنكودرز القديمة (٢٤,٢٨٠ صف) | الـ ٢٢٨ تدريب القديم **ميتعادوش** |
| `4_resume-stage3` | `resume-stage3` | إجابات الـ LLMs القديمة (٣٥,٠٤٩) | ميتعادوش |
| `5_resume-stage3b` | `resume-stage3b` | إجابات الـ sub-types القديمة (١٦,٧٨٦) | ميتعادوش |

> مصدر GitReq: Kamal, Kabir & Islam (2026), arXiv:2606.21810 —
> https://doi.org/10.6084/m9.figshare.31669477 — رخصة CC BY 4.0 (مسموح نشره مع ذكر المصدر).

---

## إنتي فين دلوقتي؟

| المرحلة | الحالة | طلع منها إيه |
|---|---|---|
| ١ `stage1-data-pipeline` | ✅ **خلصت** | `data_processed/` — `unified.parquet` (٧,٧١٢ صف) + `splits.json` (٢٢ عيلة، ١٥٥ فولد) |
| ٢ `stage2-finetuned-baselines` | 🔵 **الجلسة ٢ شغالة** (٦ أكتوبر) | الجلسة ١ حفظت ١٤٦,٣٢٩ صف — بتخلص عند **٢٠٨,٣٣٦** |
| ٣ `stage3-llm-harnes` | ▶️ **ابدئيها دلوقتي، مع Stage 2** | — |
| ٣b `stage3b-subtype-harness` | ⏳ أول ما Stage 2 (أو Stage 3) تخلص | — |
| repair و ٤ و ٥ | ⬜ لسه | — |

الجلسة ٢ من Stage 2 بتكمّل آخر **٢٧ رن** = حوالي **٣.٢ ساعة** (محسوبة من أوقات رنك نفسه).

## إيه اللي ينفع يرن مع بعض؟

**Stage 2 و Stage 3 و Stage 3b مستقلين تمامًا عن بعض — ينفع تشغّليهم في أي ترتيب
أو مع بعض.** ده مش تخمين: كل واحدة بتقرا `unified.parquet` من Stage 1 + الـ store
بتاعها هي بس، ومحدش فيهم بيقرا ناتج التانية.

```
Stage 1  ──→  Stage 2   (+ resume بتاعها)   ┐
         ──→  Stage 3   (+ resume بتاعها)   ├─ أي ترتيب / مع بعض
         ──→  Stage 3b  (+ resume بتاعها)   ┘
                          │
          Stage 3 + 3b ──→ repair
                             │
   Stage 1 + Stage 2 النهائي + repair ──→ Stage 4 ──→ Stage 5
```

**اللي ممنوع يتغيّر:** repair لازم تستنى **٣ و ٣b الاتنين**، و Stage 4 لازم تستنى
**Stage 2 لما تخلص خلاص** + repair، و Stage 5 لازم تستنى `tab9` من Stage 4.
repair و ٤ و ٥ **مش محتاجين GPU خالص**.

> 🖥️ **كاجل بيسمح بـ ٢ رن GPU بس في نفس الوقت.** Stage 2 واخدة واحد دلوقتي،
> فـ **Stage 3 تبدأ معاها حالًا**، و **Stage 3b أول ما واحدة فيهم تخلص**.
> لو جرّبتي تشغّلي تالت، كاجل هيرفض أو هيخليه يستنى — ده من كاجل، مش عطل في الكود.
> وبعد Save Version ممكن تقفلي جلسة الصفحة (Stop Session): الـ Version بتكمّل
> لوحدها في الخلفية، والجلسة المفتوحة بتاكل من حصة الـ GPU على الفاضي.

الباقي من الـ GPU: ٣.٢ (Stage 2) + ٥–٧ (Stage 3) + ٣–٥ (Stage 3b) = **١١–١٥ ساعة**،
داخلين في أسبوع واحد من حصّة كاجل (~٣٠ ساعة). Stage 3 أطول من الأول لأن نصوص
GitReq أطول **٣ مرات** من PROMISE (متوسط ٣٤٣ حرف مقابل ١٠٩)، والرن الأصلي
(من غير GitReq) كان أخد ٦.٤ ساعة.

## ثانيًا: شغّلي بالترتيب

لكل notebook: **Create → New Notebook → File → Import Notebook** ← اختاري الملف.
بعدين **Settings** (على اليمين) و **Add Input**، وفي الآخر **Save Version → Save & Run All (Commit)**.

"Output بتاع Stage X" = **Add Input → Your Work → Notebooks** ← اختاري الـ notebook دي.

### ١) `stage1-data-pipeline`
| | |
|---|---|
| **Settings** | Accelerator: **None** · Internet: **On** |
| **Add Input** | داتاسِت `gitreq` + داتاسِت `stage1-frozen-splits` |
| **الوقت** | دقيقة تقريبًا |
| **نجحت لو اللوج فيه** | `Unified: 7712 rows` · `107 fold(s) frozen ... 48 newly generated` · `15 of 18 cells covered` |

### ٢) `stage2-finetuned-baselines`  ← الأطول، **جلستين**
| | |
|---|---|
| **Settings** | Accelerator: **GPU T4 ×2** (ده اسمه في كاجل؛ Stage 2 بتستخدم كارت واحد بس والتاني بيفضل فاضي — مفيش أي رقم بيتغيّر) · Internet: **On** |
| **Add Input (الجلسة ١)** | Output بتاع Stage 1 + داتاسِت `resume-stage2` |
| **الوقت** | ~١٤ ساعة (محسوبة من أوقات تدريبك الفعلية) |

كاجل بيقفل أي جلسة بعد ١٢ ساعة. عشان كده الـ notebook **بتوقف لوحدها عند ١٠.٥ ساعة وتحفظ كل حاجة**، واللوج هيقول `SESSION BUDGET ... reached`.

**الجلسة ٢:** اعملي Save Version تاني، بس غيّري الـ Input:
- Output بتاع Stage 1 ✓
- **Output بتاع الجلسة ١ من Stage 2** ← مكان `resume-stage2`

⚠️ **شيلي `resume-stage2`** في الجلسة ٢. لو سبتيه، الـ notebook هتلاقي ملفين بنفس الاسم وهتوقف وتقولك `DUPLICATE` — ده حماية مش خطأ.

**خلصت لو:** آخر اللوج فيه `Done. Prediction store -> ... (208336 rows)` — **٢٠٨,٣٣٦ صف بالظبط**. لو الرقم أقل، يبقى الجلسة وقفت عند الحد الزمني وفيه جلسة كمان.

> ✅ **الجلسة ١ خلصت صح — ومحصلش أي مشكلة.**
> اللوج قال `SESSION BUDGET of 10.5 h reached after 85 of 112 runs` وحفظ
> **١٤٦,٣٢٩ صف**. ده الحد الأماني اللي إحنا حاطينه بنفسنا، **مش عطل**.
> فاضل **٢٧ رن**، أتقلهم خمس فولدات `xproj_subtype_shared7_gitreq`
> (١٠ إيبوك على ~٤,٦٠٠ صف = ~١٧ دقيقة للفولد). بحساب أوقاتك الفعلية
> الجلسة ٢ هتاخد **٢.٥–٣.٥ ساعة** بس.
>
> **الجلسة ٢ خطوة بخطوة — صفحة جديدة، مش تعديل القديمة:**
> ١. Create → New Notebook → File → Import Notebook ← الملف الجديد `stage2-finetuned-baselines.ipynb`
> ٢. Settings: GPU T4 ×2 · Internet On
> ٣. Add Input: **Output بتاع Stage 1** + **Output بتاع الجلسة ١ من Stage 2** — بس كده
>    (**مش** `resume-stage2` ولا `stage2-outputs` — لو اتنين بنفس الاسم هتوقف وتقولك `DUPLICATE`)
> ٤. Save Version → Save & Run All
>
> أول اللوج لازم يقول: `146,329 rows ... -> this is a PARTIAL GitReq store - resume Stage 2 from it`
> وبعدها `Plan: 340 runs total, 27 remaining`. **خلصت لما** آخر سطر يقول `(208336 rows)`.
> **الـ Output بتاع الصفحة الجديدة دي هو "Stage 2 النهائي"** اللي Stage 4 و 5 محتاجينه.
>
> ✋ **قبل Save Version في أي مرحلة:** بصّي على قسم **Input** في العمود اللي على اليمين —
> لازم تشوفي أسامي الـ inputs **مكتوبة هناك**. لو فاضي، يبقى محدش اتضاف.
> ولو نسيتي input، الكود **بيوقف في أول ١٠ ثواني** ويقولك اسم الملف الناقص
> (`MISSING INPUT: ...`) — بدل ما كان يكمّل ويقع بعدها، أو (في Stage 2) يبدأ
> الـ٣٤٠ رن من الصفر ويضيّع ١٠.٥ ساعة.
>
> 🔢 **الترتيب مهم: Import الأول، وبعدين Add Input.** الملفات القديمة كان جواها
> inputs مخفية من رنات أغسطس، والـ Import ممكن يمسح اللي إنتي ضفتيه بإيدك.
> شلتها من السبع ملفات، بس برضه خلي الترتيب ده دايمًا. ولو حاجة ناقصة، اللوج
> هيطبع **"WHAT IS ACTUALLY MOUNTED"** ويوريكي كاجل حط إيه بالظبط.
>
> 🔁 **أي Import جديد بيشيل المدخلات.** يوم ٦ أكتوبر عملنا Import لنسخة أحدث من
> Stage 3 في نفس الصفحة، والتشغيل اللي بعده طلع من غير أي مدخلات. فبعد **كل**
> Import: ضيفي المدخلات تاني، واعملي تحديث للصفحة، واتأكدي إنها ظاهرة قبل
> Save Version.
>
> ⚠️ **Stage 3 و 3b لازم من الملفات الجديدة** — القديمة كان فيها خطأ كان هيوقّع
> الرن في آخره بعد ٣–٦ ساعات (`unmapped` على خلايا GitReq). اتصلّح واتجرّب.

### ٣) `stage3-llm-harnes`
| | |
|---|---|
| **Settings** | Accelerator: **GPU T4 x2** · Internet: **On** |
| **Add Input** | Output بتاع Stage 1 (`gitReq_data-pipeline`) + **مصدر واحد بس** فيه `predictions_llm.parquet` (٣٥,٠٤٩ صف): داتاسِت `resume-stage3` **أو** Output الرن القديم بتاع `stage3-llm-harnes` — **مش الاتنين** (هتوقف وتقول `DUPLICATE`) |
| **Secrets** (Add-ons → Secrets) | `HF_TOKEN` **لازم** — نفس اللي استخدمتيه قبل كده؛ من غيره Llama-3.1-8B و Gemma-2-2B بيتشالوا (مالهمش بديل). `GROQ_API_KEY` و `GEMINI_API_KEY` و `OPENROUTER_API_KEY` اختياري — من غيرهم موديلات الـ API مش هتاخد خلايا GitReq |
| **الوقت** | ٥–٧ ساعات تقريبًا (حد أمان تلقائي عند ١٠ ساعات) |
| **أول اللوج لازم يقول** | `unified.parquet ... 7,712 rows ... OK` و `predictions_llm.parquet ... 35,049 rows ... OK` وبعدها `No duplicates. Running the stage now.` · `SEEDED 35049 rows` · `Resume check: all 35049 stored predictions are items the current plan selects.` · تحت EVALUATION SETS يظهر `fr_nfr/gitreq` و `security/gitreq` |
| **نجحت لو** | آخر اللوج: `PASS  every local model answered its whole plan (both phases)` و `RESULT: ALL CHECKS PASSED` — والـ store زاد **٢٥,٢٠٠ صف على الأقل** (الموديلات المحلية، بالظبط) + صفوف الـ API |

> 🛡️ **حمايتين جداد في Stage 3 و 3b:**
> * **فحص المدخلات نفسه بتاع Stage 2** — لو ملف ناقص أو متكرر أو حجمه غلط بتوقف في أول ثواني
>   وتطبع **WHAT IS ACTUALLY MOUNTED** (كاجل حط إيه بالظبط).
> * **فحص الاستكمال** — قبل ما أي موديل يتحمّل، بتتأكد إن كل إجابة قديمة في الـ store
>   لسه على نفس الأسئلة اللي الكود هيختارها دلوقتي. جرّبته على الـ store بتاعك الحقيقي
>   مع GitReq: ✅ مطابق، والمطلوب بالظبط **٢٥,٢٠٠** إجابة جديدة (GitReq بس — ولا سؤال
>   قديم هيتعاد). لو ظهر `THE SEEDED STORE DOES NOT MATCH` — **متغيّريش حاجة وابعتيلي اللوج.**
> * ولو الرن وقف عند حد الـ ١٠ ساعات، آخر اللوج هيقول `FAIL  every local model answered its
>   whole plan` ومعاه العدد الناقص → جلسة تانية: صفحة جديدة، Stage 1 + **Output الرن ده** بس.

> ⏱️ **الجلسة ١ من Stage 3 (٦–٧ أكتوبر) خلص وقتها — ومفيش حاجة ضاعت.**
> الست موديلات المحلية خلّصوا Phase 1 كلها (**١٤,٤٠٠** إجابة) واتحفظت. بعدها Groq
> بقى يرد ببطء جدًا (كل سؤال ~٤٦ ثانية بدل ٢.٤)، وفضل كده لحد ما كاجل قفل الجلسة
> عند ١٢ ساعة — قبل Phase 2.
> * **اتصلّح في Stage 3 و 3b:** كل API ليه **حد وقت** = ضعف وقته المتوقع + ٢٠ دقيقة.
>   لو عدّاه بيقف، وإجاباته بتتحفظ، والموديلات المحلية بتكمّل عادي. لو ده حصل
>   هتشوفي في اللوج كلمة `allowance` — **مش عطل**.
> * **الجلسة ٢:** صفحة جديدة (Import للملف الجديد) ← Add Input: Output بتاع Stage 1
>   + **Output الجلسة ١ من Stage 3** بس. **مش** الداتاسِت اللي فيه ٣٥,٠٤٩ صف
>   (لو الاتنين موجودين هتوقف وتقول `DUPLICATE`).
> * أول اللوج: `predictions_llm.parquet` حوالي **٥٠,٣٠٠** صف و
>   `larger than the two-corpus reference` — ده **ملاحظة مش خطأ**.
> * الباقي **١٠,٨٠٠** إجابة محلية بالظبط (Phase 2). خلصت لما آخر اللوج يقول
>   `PASS  every local model answered its whole plan (both phases)` و `RESULT: ALL CHECKS PASSED`.

> ⚠️ **مهم جدًا — Groq شال Llama-3.3-70B.**
> في ١٦ أغسطس ٢٠٢٦ نقلت Groq الموديل `llama-3.3-70b-versatile` لباقة
> enterprise بس، فالمفتاح المجاني بقى يرجّع `model not available`. الموديل ده
> هو الـ open_hosted بتاع ورقتك، وعنده **٨٧٠ صف** في الـ store القديم.
>
> * **لازم تضيفي الـ resume store.** من غيره الـ notebook هتبدأ من الصفر
>   والـ٨٧٠ صف دول **هيختفوا للأبد** — مفيش رن تاني يقدر يرجّعهم، لأن Groq
>   مبقتش بتقدّم الموديل أصلًا. الـ notebook دلوقتي بتطبع تحذير كبير لو الـ
>   store مش موجود، بدل سطر لوج صغير.
> * الـ notebook بتجرّب `qwen/qwen3.8-27b` الأول (وده اللي اشتغل فعلًا مع
>   مفتاحك يوم ٢٤ سبتمبر) بسعره المنشور، وبعديه `qwen3.6-27b` و `gpt-oss-120b`
>   و `gpt-oss-20b`. الترتيب مثبّت عشان Stage 3 و Stage 3b يختاروا **نفس
>   الموديل** — لو كل واحدة اختارت موديل مختلف، الجداول هتتناقض.
> * صفوف Llama الـ٨٧٠ **بتتحفظ زي ما هي**؛ الموديل الجديد بياخد `model_tag`
>   لوحده (`groq-qwen3.8-27b`) فمفيش حاجة بتمسح حاجة.
> * في الورقة: اكتبي إن Llama-3.3-70B اتشال من الخدمة في نص الدراسة، واذكري
>   تغطيته الفعلية زي ما هي. الرن بيسجّل ده لوحده في `stage3_manifest.json`
>   تحت `api_models_retired_since_committed_run`.
> * مسألة السعر التقديري اتحلّت: كل الموديلات الأربعة بأسعارها المنشورة،
>   وأي مسار `:free` على OpenRouter سعره صفر **بقاعدة** مش بتقدير.
> * **السيرفر المشغول مبقاش بيغيّر الموديل.** يوم ٦ أكتوبر `gemini-3.1-flash-lite`
>   (الموديل التجاري اللي في نتايجك القديمة) رد بـ `503` "مشغول"، والكود القديم
>   نقل لـ `gemini-3.5-flash-lite` — يعني موديلين Gemini مختلفين بين الـ corpora.
>   دلوقتي بيستنى ويعيد المحاولة (١٥ و٣٠ و٦٠ ثانية)، ولو لسه مشغول بيسيب Gemini
>   الجلسة دي وجلسة بعدها تكمّله، بدل ما يغيّر الموديل. لو شفتي في اللوج
>   `sits this session out` يبقى ده اللي حصل — **مش عطل**.

### ٤) `stage3b-subtype-harness`
| | |
|---|---|
| **Settings** | نفس Stage 3 (GPU T4 x2 · Internet On · نفس الـ Secrets) |
| **Add Input** | Output بتاع Stage 1 (`gitReq_data-pipeline`) + **مصدر واحد بس** فيه `predictions_subtype.parquet` (١٦,٧٨٦ صف): داتاسِت `resume-stage3b` **أو** Output الرن القديم بتاع `stage3b-subtype-harness` — مش الاتنين |
| **امتى** | أول ما Stage 2 أو Stage 3 تخلص (كاجل = ٢ GPU في نفس الوقت) |
| **الوقت** | ٣–٥ ساعات تقريبًا |
| **أول اللوج لازم يقول** | `predictions_subtype.parquet ... 16,786 rows ... OK` · `SEEDED 16786 rows` · `Resume check: all 16786 stored predictions ...` · تحت EVALUATION SETS يظهر `subtype_shared7/gitreq` و `subtype_shared7/promise` |
| **نجحت لو** | `PASS  every local model answered its whole plan (both phases)` و `RESULT: ALL CHECKS PASSED` — والـ store زاد **١١,٠٣٠ صف على الأقل** + صفوف الـ API |

### ٥) `stage3b-repair`
| | |
|---|---|
| **Settings** | Accelerator: **None** |
| **Add Input** | Output بتاع Stage 3 + Output بتاع Stage 3b |
| **الوقت** | دقايق |

### ٦) `stage4-analysis`
| | |
|---|---|
| **Settings** | Accelerator: **None** · Internet: **Off** |
| **Add Input** | Output بتاع Stage 1 + **آخر** Output بتاع Stage 2 + Output بتاع repair |
| **نجحت لو** | `tab2_main_transfer.csv` فيه **١٠ أعمدة** `x-data from ...` |

### ٧) `stage5-cost`
| | |
|---|---|
| **Settings** | Accelerator: **None** · Internet: **Off** |
| **Add Input** | آخر Output بتاع Stage 2 + Output بتاع repair + Output بتاع Stage 4 |

---

## حصة الـ GPU
كاجل بيدي حوالي **٣٠ ساعة GPU في الأسبوع**، و **٢ رن GPU بس في نفس الوقت**. الباقي بعد جلسة Stage 2 الأولى: ٣.٢ (Stage 2) + ٥–٧ (Stage 3) + ٣–٥ (Stage 3b) = ~١١–١٥ ساعة — يكفوا في أسبوع واحد.

## لو حاجة وقفت
كل notebook بتطبع **في الأول** قايمة بالملفات اللي لقتها وعدد صفوفها، وبتوقف برسالة واضحة لو فيه مشكلة (ملف ناقص، ملف متكرر، حجم غلط). اقري أول ٣٠ سطر في اللوج — السبب هيكون مكتوب هناك.
