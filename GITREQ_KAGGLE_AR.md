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
| ٢ `stage2-finetuned-baselines` | 🟡 **٨٥ من ١١٢** | `predictions_finetuned.parquet` (١٤٦,٣٢٩ صف — بتخلص عند ٢٠٨,٣٣٦) |
| ٣ و ٣b و repair و ٤ و ٥ | ⬜ لسه | — |

فاضل **٢٧ رن** في Stage 2 = **٣.٢ ساعة** بالظبط (محسوبة من أوقات رنك نفسه).

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

الباقي من الـ GPU: ٣.٢ (Stage 2) + ٣–٦ (Stage 3) + ٢–٥ (Stage 3b) = **٩–١٥ ساعة**،
داخلين في أسبوع واحد من حصّة كاجل (~٣٠ ساعة).

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
| **Settings** | Accelerator: **GPU T4** · Internet: **On** |
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
> ٢. Settings: GPU T4 · Internet On
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
> ⚠️ **Stage 3 و 3b لازم من الملفات الجديدة** — القديمة كان فيها خطأ كان هيوقّع
> الرن في آخره بعد ٣–٦ ساعات (`unmapped` على خلايا GitReq). اتصلّح واتجرّب.

### ٣) `stage3-llm-harnes`
| | |
|---|---|
| **Settings** | Accelerator: **GPU T4 x2** · Internet: **On** |
| **Add Input** | Output بتاع Stage 1 + داتاسِت `resume-stage3` |
| **Secrets** (Add-ons → Secrets) | `HF_TOKEN` **لازم** — نفس اللي استخدمتيه قبل كده؛ من غيره Llama-3.1-8B و Gemma-2-2B بيتشالوا (مالهمش بديل). `GROQ_API_KEY` و `GEMINI_API_KEY` اختياري — من غيرهم موديلات الـ API مش هتاخد خلايا GitReq |
| **الوقت** | ٣–٦ ساعات تقريبًا (حد أمان تلقائي عند ١٠ ساعات) |
| **نجحت لو** | الـ store زاد من ٣٥,٠٤٩ لحوالي ٦١,٠٠٠ صف |

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

### ٤) `stage3b-subtype-harness`
| | |
|---|---|
| **Settings** | نفس Stage 3 (GPU T4 x2 · Internet On · نفس الـ Secrets) |
| **Add Input** | Output بتاع Stage 1 + داتاسِت `resume-stage3b` |
| **الوقت** | ٢–٥ ساعات تقريبًا |
| **نجحت لو** | الـ store زاد من ١٦,٧٨٦ لحوالي ٢٨,٤٠٠ صف |

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
كاجل بيدي حوالي **٣٠ ساعة GPU في الأسبوع**. الخطة كلها ~٢٠–٢٥ ساعة (Stage 2 ~١٤، و3 و3b مع بعض ~٥–١١). يعني تكفي في أسبوع واحد، بس ابدئي بـ Stage 2 لأنها الأطول.

## لو حاجة وقفت
كل notebook بتطبع **في الأول** قايمة بالملفات اللي لقتها وعدد صفوفها، وبتوقف برسالة واضحة لو فيه مشكلة (ملف ناقص، ملف متكرر، حجم غلط). اقري أول ٣٠ سطر في اللوج — السبب هيكون مكتوب هناك.
