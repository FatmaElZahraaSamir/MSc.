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

### ٣) `stage3-llm-harnes`
| | |
|---|---|
| **Settings** | Accelerator: **GPU T4 x2** · Internet: **On** |
| **Add Input** | Output بتاع Stage 1 + داتاسِت `resume-stage3` |
| **Secrets** (Add-ons → Secrets) | `HF_TOKEN` **لازم** — نفس اللي استخدمتيه قبل كده؛ من غيره Llama-3.1-8B و Gemma-2-2B بيتشالوا (مالهمش بديل). `GROQ_API_KEY` و `GEMINI_API_KEY` اختياري — من غيرهم موديلات الـ API مش هتاخد خلايا GitReq |
| **الوقت** | ٣–٦ ساعات تقريبًا (حد أمان تلقائي عند ١٠ ساعات) |
| **نجحت لو** | الـ store زاد من ٣٥,٠٤٩ لحوالي ٦١,٠٠٠ صف |

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
