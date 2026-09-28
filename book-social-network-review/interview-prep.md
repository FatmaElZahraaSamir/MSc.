# Book Social Network: مراجعة المشروع + أسئلة الإنترفيو

> **المشروع:** https://github.com/EsmaelSamir/book-social-network، والنسخة اللي اتراجعت هي commit `078d813` (بتاريخ 11 يوليو 2026).
>
> **اتعمل إيه في المراجعة:** اتقرا كل كود الباك إند والفرونت إند، واتعمل build للاتنين، واتشغلت الـ tests.
> بعد كده الباك إند اشتغل فعلًا على PostgreSQL واتجرب بطلبات حقيقية (curl)، والفرونت اتجرب في متصفح (Playwright).
>
> أي غلط جنبه **✅** معناه إنه اتشاف وهو بيحصل فعلًا في التجربة، مش مجرد استنتاج من قراية الكود.
>
> مسارات ملفات الباك إند كلها تحت `book-network/src/main/java/com/global/book/`، والفرونت تحت `book-network-ui/src/app/`.

## الفهرس

1. [الخلاصة: المشروع تمام ولا لأ؟](#1-الخلاصة-المشروع-تمام-ولا-لأ)
2. [الأخطاء بالترتيب (من الأخطر للأبسط)](#2-الأخطاء-بالترتيب)
3. [أسئلة الباك إند (Spring Boot)](#3-أسئلة-الباك-إند-spring-boot)
4. [أسئلة الفرونت إند (Angular)](#4-أسئلة-الفرونت-إند-angular)
5. [لو طلبوا تعديل أو Live coding](#5-لو-طلبوا-تعديل-أو-live-coding)
6. [حاجات تانية مهمة قبل الإنترفيو](#6-حاجات-تانية-مهمة-قبل-الإنترفيو)
7. [أرقام ومعلومات لازم تبقى محفوظة](#7-أرقام-ومعلومات-لازم-تبقى-محفوظة)

---

## 1. الخلاصة: المشروع تمام ولا لأ؟

**الفكرة والشكل العام كويسين جدًا كمشروع Full-stack للإنترفيو**، والمشروع بيغطي حاجات كتير بيحبوا يسألوا فيها:
Spring Boot 4 و Spring Security مع JWT و JPA/PostgreSQL وإيميلات Async و Swagger، و Angular 21 بـ standalone components و lazy loading و guard و interceptor، و Docker و CI.

- الباك إند بيعمل build من غير مشاكل، و**الـ 13 test كلهم ناجحين ✅**.
- الفرونت بيعمل build ✅، بس فيه warning إن حجم الـ bundle أكبر من الـ budget.

**بس فيه أخطاء حقيقية لازم تتصلح قبل ما المشروع يتعرض في إنترفيو:**

- **4 مشاكل خطيرة:**
  - أي يوزر يقدر يعدّل كتب غيره ويغيّر صورها (IDOR).
  - الـ JWT secret مرفوع على GitHub، واتعمل بيه token مزوّر ودخل فعلًا.
  - نفس الكتاب ممكن يتسلف لشخصين في نفس اللحظة.
- **مشكلة كبيرة في الفرونت:** معظم الشاشات **مش بتعرض الداتا بعد ما توصل** (Angular 21 شغال zoneless والكود مكتوب بالطريقة القديمة).
  يعني لستة الكتب بتظهر فاضية، ورسالة غلط الـ login مش بتظهر، ونتيجة التفعيل مش بتظهر، وفورم التعديل بيظهر فاضي.
- أخطاء تانية بتطلّع 500 في حالات عادية، زي إضافة كتاب من غير "Share me"، أو feedback من غير تقييم.

الحلول أغلبها صغيرة. في حدود **يوم شغل** المشروع يبقى قوي جدًا، والأحسن كمان إن الأخطاء اللي هتتصلح تتحكي في الإنترفيو كقصص ("لقيت مشكلة كذا وحليتها إزاي")، وده بيفرق جدًا.

---

## 2. الأخطاء بالترتيب

### 🔴 خطيرة (Security / Data)

#### 1) أي يوزر يقدر يعدّل كتاب يوزر تاني (IDOR) ✅
- **فين:** `book/BookService.java:39-48` في `save()`، في الجزء الخاص بالـ update.
- **اللي بيحصل:** لو اتبعت `POST /books` ومعاه `id` كتاب مش بتاع اليوزر، السيرفر بيعدّله عادي.
  في التجربة: Bob غيّر عنوان كتاب Alice لـ `HACKED BY BOB` والرد كان **200**.
  وكمان لو الكتاب مش موجود بيرمي `RuntimeException` فبيرجع 500 بدل 404.
- **الحل:** بعد `findById` يتعمل check إن `book.getOwner().getId()` هو نفس id اليوزر الحالي، وإلا يترمي `OperationNotPermittedException`. الكود في [الجزء 5، تعديل 1](#تعديل-1--إصلاح-الـ-idor-سهل).

#### 2) أي يوزر يقدر يغيّر صورة غلاف كتاب غيره (IDOR) ✅
- **فين:** `book/BookService.java:205-214` في `uploadBookCoverPicture()`.
- **اللي بيحصل:** Bob رفع صورة لكتاب Alice والرد كان **202**، والصورة اتحفظت في فولدر Bob.
- **الحل:** نفس check الملكية.

#### 3) الـ JWT secret وباسوورد الداتابيز والميل مكتوبين في الكود ومرفوعين على GitHub ✅
- **فين:** `application-dev.yml` و `application-prod.yml`، ونفس الـ secret في الاتنين.
- **اللي بيحصل:** اتعمل token مزوّر لـ `alice@test.com` بـ Python، باستخدام الـ secret اللي في الريبو ومن غير الباسوورد، والسيرفر **قبله ورجّع 200**.
  يعني أي حد شاف الريبو يقدر يدخل بأي أكونت على أي سيرفر شغال بالكونفيج ده.
- **الحل:**
  - الـ secret يتقري من environment variable، يعني `secret-key: ${JWT_SECRET}`.
  - يبقى فيه secret مختلف لكل بيئة.
  - الـ secret الحالي يتغيّر (rotate)، لأنه بقى معروف.
  - يتضاف ملف `.env.example` من غير قيم حقيقية.

#### 4) نفس الكتاب ممكن يتسلف لاتنين في نفس اللحظة (Race condition) ✅
- **فين:** `book/BookService.java:136-164` في `borrowBook()`. الكود بيعمل check (`isAlreadyBorrowed`) وبعدين `save`، من غير transaction ولا lock.
- **اللي بيحصل:** Bob و Carol طلبوا نفس الكتاب في نفس اللحظة 5 مرات، و**4 مرات من الـ 5 الكتاب اتسلف للاتنين**.
- **الحل:** أي واحد من دول (الكود في [الجزء 5، تعديل 12](#تعديل-12--منع-السلف-المزدوج-متوسط)):
  - إضافة `@Transactional` مع `@Lock(PESSIMISTIC_WRITE)` على قراءة الكتاب.
  - استخدام `@Version` (optimistic locking).
  - عمل unique partial index في الداتابيز على `book_id` لما `return_approved = false`.

### 🟠 أخطاء في الشغل (Bugs)

#### 5) الشاشات مش بتتحدث بعد ما الداتا توصل (Angular zoneless) ✅ ده أكبر غلط في الفرونت
- **السبب:** Angular 21 بيشتغل **zoneless** افتراضيًا، ومفيش `zone.js` في `package.json`.
  والكود مكتوب بالطريقة القديمة: قيمة بتتحط في field عادي بعد `await` أو `.then()`، زي `this.bookResponse = await ...`.
  فـ Angular مش بيعرف إن حاجة اتغيرت، ومش بيعيد رسم الشاشة.
- **اللي اتشاف في المتصفح:**
  - صفحة `/books`: الـ component فيه 5 كتب، والشاشة فيها **0 كروت**. أول ما change detection اشتغل بالعافية، الـ 5 ظهروا.
  - صفحة Login بباسوورد غلط: رسالة الغلط موجودة في الـ component بس **مش ظاهرة**.
  - صفحة التفعيل: الأكونت **اتفعّل فعلًا في الداتابيز** بس رسالة "Activation Successful" مش بتظهر، فاليوزر فاكر إن مفيش حاجة حصلت.
  - صفحة تعديل كتاب (`/books/manage/2`): الداتا وصلت، بس الفورم **ظاهر فاضي**.
  - صفحة Borrowed books: الجدول فاضي.
  - يعني الشاشة بتتحدث بس لما اليوزر يعمل click على حاجة، فالـ UI دايمًا "متأخر خطوة".
- **الحل:**
  - **الأحسن:** استخدام signals، يعني `bookResponse = signal<PageResponseBookResponse>({})` وبعدين `this.bookResponse.set(...)`، وفي الـ template يبقى `bookResponse().content` (الكود في [تعديل 5](#تعديل-5--إصلاح-الشاشات-اللي-مش-بتتحدث-signals-سهل)).
  - **حل سريع:** `inject(ChangeDetectorRef).markForCheck()` بعد كل تحديث.
  - **أو:** رجوع zone.js، يعني `provideZoneChangeDetection()` مع الـ polyfill.

#### 6) صفحة التسجيل بتنقل لصفحة التفعيل حتى لو التسجيل فشل ✅
- **فين:** `pages/register-component/register-component.ts:29`. الاستدعاء `this.api.invoke(...)` معمول **من غير `await`**، فالـ try/catch ملوش أي لازمة.
- **اللي بيحصل:** اتجرب إيميل غلط وباسوورد 3 حروف. السيرفر رجّع 400، بس الصفحة راحت `/activate-account` ومفيش أي رسالة غلط.
- **الحل:** `async register()` مع `await`، ومعاها signals عشان الرسالة تظهر.

#### 7) إضافة كتاب من غير ما "Share me" يتعلّم عليه بترجع 500 ✅
- **السبب:** حاجتين مع بعض:
  - الفورم مش بيبعت `shareable` لو الـ checkbox متلمسش، لأن `shareable: true` معمولها comment في `manage-book-component.ts:25`.
  - في الباك، `BookRequest.shareable` نوعه `Boolean` (wrapper)، فبيوصل `null`، وبيحصل NullPointerException وقت الـ unboxing في `book/BookMapper.java:15`.
- **اللي بيحصل:** اتجرب من الـ API ومن الـ UI، والرد كان 500 برسالة `Cannot invoke "java.lang.Boolean.booleanValue()"`.
- **الحل:** في الـ record يبقى `boolean` (primitive)، أو يتكتب `Boolean.TRUE.equals(request.shareable())`. وفي Angular تبقى القيمة الابتدائية `shareable: false`.

#### 8) Feedback من غير تقييم (note) بيبوّظ صفحة الكتب لكل الناس ✅
- **السبب:** `FeedbackRequest.note` مفيهوش `@NotNull`، والـ `@Positive/@Min/@Max` بيعدّوا الـ null عادي.
  و `Book.getRates()` بيعمل `mapToDouble(Feedback::getNote)`، فبيحصل NPE.
- **اللي بيحصل:** اتحط feedback واحد من غير note على كتاب، وبعدها `GET /books` و `GET /books/owner` و `GET /books/{id}` كلهم رجعوا **500 لكل اليوزرز**.
- **الحل:** `@NotNull` على `note` و `nullable = false` على العمود. والأحسن كمان إن المتوسط يتحسب في الداتابيز (`AVG`).

#### 9) لو صاحب الكتاب عمله Archive وهو متسلف، الكتاب بيعلق للأبد ✅
- **فين:** `returnBorrowedBook` و `approveReturnBorrowedBook` بيرفضوا لو الكتاب archived أو مش shareable.
- **اللي بيحصل:** Bob استلف الكتاب، وبعدين Alice عملته archive. Bob مش عارف يرجّعه (400)، و Alice مش عارفة توافق على الإرجاع (400).
- **الحل:** الشرط ده يتشال من return و approve، ويتمنع الـ archive أو إلغاء الـ share لو الكتاب متسلف.

#### 10) رقم الصفحة في لستة الـ Feedback غلط ✅
- **فين:** `feedback/FeedbackService.java:56`، مستخدم `getNumberOfElements()` بدل `getNumber()`.
- **اللي بيحصل:** الصفحة رقم 0 وفيها 3 تعليقات رجعت `"number": 3`.

#### 11) التسجيل بإيميل موجود قبل كده بيرجع 500 وبيطلّع الـ SQL للعميل ✅
- **السبب:** مفيش check قبل الحفظ. الرد فيه اسم الـ constraint وجملة الـ INSERT كاملة.
- **الحل:**
  - استخدام `findByEmail` قبل الحفظ، ولو موجود يرجع **409 Conflict** برسالة واضحة.
  - إضافة handler لـ `DataIntegrityViolationException`، عشان لو طلبين وصلوا في نفس اللحظة.

#### 12) الـ Error handling بيحوّل أي غلط لـ 500 وبيكشف تفاصيل داخلية ✅
الـ `@ExceptionHandler(Exception.class)` في `handler/GlobalExceptionHandler.java:63` بيمسك كل حاجة، حتى أخطاء Spring العادية:

| الطلب | المفروض يرجع | اللي رجع فعلًا |
|---|---|---|
| `GET /books/999999` (مش موجود) | 404 | 500 |
| `GET /books/abc` | 400 | 500 |
| `GET /does-not-exist` | 404 | 500 |
| JSON بايظ | 400 | 500 |
| كود تفعيل غلط | 400 | 500 (والرسالة `"Ivalid Token"` فيها typo) |
| رفع صورة 12MB | 413 | 500 |

وكمان `exp.getMessage()` بيترجع للعميل، و `printStackTrace()` مستخدم بدل logger.

**الحل:**
- يتعمل handler لكل نوع: `EntityNotFoundException` → 404، و `HttpMessageNotReadableException` و `MethodArgumentTypeMismatchException` → 400، و `MaxUploadSizeExceededException` → 413.
- أو الكلاس يعمل extend لـ `ResponseEntityExceptionHandler`، ويستخدم `ProblemDetail`.
- الـ 500 يرجع رسالة عامة بس، والتفاصيل تتكتب بـ `log.error`.

#### 13) من غير token، أو لو الـ token انتهى، الرد 403 فاضي بدل 401 ✅
- **السبب:** مفيش `AuthenticationEntryPoint` متعرّف، والـ `JwtAuthFilter` مش بيمسك `ExpiredJwtException` ولا أي `JwtException`.
- **النتيجة:** الفرونت مش بيقدر يفرّق بين "الجلسة انتهت" و "ممنوع".
- **الحل:**
  - إضافة `.exceptionHandling(e -> e.authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)))`.
  - إضافة try/catch في الفلتر.
  - إضافة interceptor في Angular يعمل logout لما يوصله 401 ([تعديل 11](#تعديل-11--interceptor-يتعامل-مع-401-سهل)).

#### 14) لو الإيميل فشل محدش بيعرف، ومفيش طريقة لطلب كود جديد ✅
- **اللي بيحصل:**
  - الميثود `sendEmail` معمولة `@Async`، فالغلط بيتسجل في اللوج بس، والتسجيل بيرجع 201 عادي. اتجرب والـ SMTP مقفول، وده اللي حصل بالظبط.
  - اليوزر مش هيقدر يسجل تاني لأن الإيميل unique، ومفيش endpoint لـ "resend code".
- **كمان:** إعدادات الميل في الـ YAML متحطوطة في مكان غلط، فكلها متجاهلة:
  - `mail.auth` بدل `mail.smtp.auth`.
  - `mail.starttls.enabled` بدل `mail.smtp.starttls.enable`.
  - الـ timeouts مكتوبة من غير `smtp`، واللوج بيقول `timeout -1`، يعني الانتظار مالوش آخر لو سيرفر الميل علّق.

#### 15) كود التفعيل ضعيف
- الكود 6 أرقام بس (مليون احتمال) ومفيش rate limiting، ومش مربوط بالإيميل في الريكوست.
- عمود `token` **مش unique ومفيش عليه index**، وده اتشاف في الداتابيز. لو اتنين أخدوا نفس الكود، `findByToken` هيرمي `IncorrectResultSizeDataAccessException` ويرجع 500.
- الكود بيشتغل تاني بعد ما يتستخدم، لأن مفيش check على `validatedAt` ✅.

#### 16) حد رفع الصور الحقيقي 10MB مش 50MB ✅
- الإعداد `max-file-size: 50MB` متظبط، بس `max-request-size` متسابش على الافتراضي بتاعه وهو 10MB. صورة 12MB رجعت 500.

#### 17) Routes ناقصة في Angular ✅
- أيقونة التفاصيل (ℹ) بتروح `books/details/:id` ومفيش route ليها، والـ `BookDetailsComponent` نفسه فاضي ("works!").
- لينك "My waiting list" الـ route بتاعه معمول comment.
- الاتنين بيطلّعوا `NG04002: Cannot match any routes`.
- ومفيش route لـ `**` (صفحة 404).

#### 18) صفحة Manage book بتقرأ اسم غلط للأخطاء ✅
- **فين:** `manage-book-component.ts:85`. الكود بيقرأ `err.error.validationErrors`، والباك بيبعت `validateErrors`، فبيبقى `errorMsg = undefined`.
- **اللي بيحصل:** أول ما change detection يشتغل بعدها بيضرب `TypeError: Cannot read properties of undefined (reading 'length')`.
- **كمان:** رسايل الـ validation راجعة أكواد (`"100"`, `"101"`) مش كلام، فلازم mapping في الفرونت.

#### 19) اسم "Esmael" مكتوب ثابت في الـ navbar ✅
- **فين:** `book/components/menu-component/menu-component.html:41`. أي يوزر بيدخل بيشوف "Esmael"، واتجرب بأكونت Bob.
- **الحل:** الاسم يتقري من `fullName` اللي جوه الـ JWT ([تعديل 4](#تعديل-4--اسم-اليوزر-الحقيقي-في-الـ-navbar-سهل)).

#### 20) جدول Borrowed books بيعمل `track` بـ id الكتاب ✅
- **اللي بيحصل:** لو نفس الكتاب اتسلف مرتين، Angular بيطلّع `NG0955 duplicated keys`.
- **الحل:** `BorrowedBookResponse` يرجّع id الـ transaction، والـ track يبقى بيه.

#### 21) الـ port مختلف بين الباك والفرونت
- الـ dev profile شغال على **8078**، والفرونت و Swagger بيكلموا **8088**. فلو الباك اشتغل عادي بالـ dev profile، الفرونت مش هيوصله (عشان كده اتشغل بـ `--server.port=8088`).
- الـ URL مكتوب جوه ملف generated (`services/api-configuration.ts`). الأحسن يبقى في `environment.ts` ويتمرر بـ `provideApiConfiguration(...)`.

#### 22) الـ Feedback في صفحة Borrowed books بيضيع بصمت
- الميثود `giveFeedback()` من غير `await`، فأي غلط بيضيع.
- الـ slider بيبدأ من 0، والباك رافض الـ 0 (`@Positive`). فلو الكتاب اترجع "مع تقييم" من غير ما الـ slider يتحرك، التقييم مش بيتسجل ومحدش بيقول.
- الـ `feedbackRequest` مش بيتفضى بعد الإرسال.

### 🟡 جودة كود وترتيب
دي مش بتوقع المشروع، بس الـ interviewer ممكن يلاحظها:

**Git وحجم الريبو:**
- **صور يوزرز حقيقية مرفوعة على git:** `book-network/uploads/...` فيها 12 صورة، ولازم فولدر `uploads/` يتضاف لـ `.gitignore`.
- وفي Docker الصور بتضيع لما الـ container يتمسح، لأن مفيش volume ليها.

**الـ Tests:**
- الأمر `ng test`: **5 من 18 test بيفشلوا ✅**، لأنهم الـ specs الافتراضية ومحدش عدّلها.
- الباك: الـ 13 ناجحين ✅، بس مفيش tests لـ `BookService` ولا للـ security.

**الأداء والـ Transactions:**
- مفيش `@Transactional` في `BookService`، والكود شغال بس بسبب open-in-view (واللوج بيطلّع warning عليه).
- فيه N+1 queries في لستة الكتب.
- كل الأغلفة بتتقري من الديسك وتتبعت Base64 جوه JSON اللستة، وده تقيل جدًا.
- الإعداد `ddl-auto: update` حتى في prod، والأحسن Flyway أو Liquibase.

**أخطاء صغيرة في الباك:**
- ملف `Book.java` بيعمل import لـ `java.beans.Transient` بدل `jakarta.persistence.Transient`، وفيه import متكرر.
- أسماء فيها typo:
  - `autherName` (ودي بقت اسم عمود في الداتابيز).
  - `totalElments` (ودي في الـ API contract نفسه).
  - `photoes-output-path`.
  - `"Ivalid Token"`.
  - `"User Not  Found some3a"`.
- الـ `@Valid` على parameters في الـ services ملوش أي تأثير من غير `@Validated` على الكلاس.
- الـ `BusinessErrorCodes` مكتوب فيه `FORBIDDEN`، والكود بيرجّع 401.
- الـ JSON راجع فيه `"BusinessErrorDescription"` بحرف كبير جنب `businessErrorCode` بحرف صغير.
- الـ `FileStorageService`:
  - بيثق في الـ Content-Type اللي جاي من العميل، ولو كان null بيحصل NPE.
  - الامتداد بياخده من اسم الملف.
  - الصور القديمة مش بتتمسح.

**أخطاء صغيرة في الفرونت:**
- فيه `@Output() private` في `BookCardComponent`.
- فيه import مش مستخدم من `@angular/compiler` في الـ guard.
- بقايا SSR (`@angular/ssr` و `express`) والـ SSR نفسه مش متفعّل.
- فيه `console.log` كتير.
- كود الـ pagination متكرر في 4 components.
- فيه `type="email"` في خانة اسم المؤلف، و placeholder مكتوب فيه "1234 Main St".
- الصورة الافتراضية جاية من `source.unsplash.com`، ودي خدمة متوقفة.
- البحث في الـ navbar مش شغال، وأيقونة "waiting list" مش بتعمل حاجة.
- حجم الـ bundle الأولي **566kB** وده أكبر من الـ budget (500kB) ✅، بسبب Bootstrap و FontAwesome كاملين.

**الـ CI والـ Docker:**
- الـ CI بيشتغل يدوي بس (`workflow_dispatch`)، ومفيش pipeline للفرونت.
- الـ Dockerfile بيبني بـ `maven:3.8.7-openjdk-18` (نسخة مش LTS)، وبيشتغل كـ root.

**مدة الـ JWT:**
- القيمة `8640000` ms يعني **2.4 ساعة** ✅. غالبًا المقصود كان يوم، وده `86400000`.
- ومفيش refresh token.

---

## 3. أسئلة الباك إند (Spring Boot)

> ⭐ = سؤال متوقع جدًا.
>
> الأسئلة مكتوبة بالإنجليزي زي ما غالبًا هتتسأل، والإجابة بالعربي ومعاها الكلمات المهمة بالإنجليزي عشان تتقال في الإنترفيو.

### 3.1 Architecture و Spring Boot

**⭐ Q1. Walk me through the backend architecture. What happens when a request comes in?**

المشروع layered ومتقسم **package-by-feature** (`auth`, `book`, `feedback`, `history`, `user`...).
الطلب بيعدّي الأول على الـ Security filter chain، وفيها `JwtAuthFilter`.
بعدين بيروح لـ **Controller** (زي `BookController`)، وبعده **Service** وفيه البيزنس رولز، وبعده **Repository** (Spring Data JPA)، وآخر حاجة PostgreSQL.
الداتا بتدخل وتطلع كـ **DTOs** (`BookRequest` record و `BookResponse`)، وفيه **Mapper** بيحوّل. الأخطاء بتتجمع في `GlobalExceptionHandler`. وكل الـ URLs تحت `/api/v1` (الـ `context-path`).

**Q2. What does `@SpringBootApplication` do?**

هي 3 annotations في واحدة: `@Configuration` و `@EnableAutoConfiguration` و `@ComponentScan` على الـ package `com.global.book` وكل اللي تحته.
وفي المشروع متضاف عليها `@EnableJpaAuditing(auditorAwareRef = "auditAware")` و `@EnableAsync`.

**Q3. Why constructor injection with `@RequiredArgsConstructor`?**

مكتبة Lombok بتعمل constructor لكل field `final`. المميزات:
- الـ dependencies مش بتتغير (immutable).
- مينفعش الـ object يتعمل من غيرها.
- سهل تعمل unit test بـ mocks، وده اللي معمول في `FeedbackServiceTest` بـ `@InjectMocks`.
- مفيش field injection بالـ reflection.

**Q4. How do profiles work here?**

الإعداد `spring.profiles.active: ${ACTIVE_PROFILE:dev}` معناه: خد قيمة الـ environment variable `ACTIVE_PROFILE`، ولو مش موجودة استخدم `dev`.
- ملف `application-dev.yml`: localhost، على port 8078.
- ملف `application-prod.yml`: الـ DB والميل من environment variables (`DB_URL` و `MAILDEV_URL`)، على port 8088.

والـ docker-compose بيحط `ACTIVE_PROFILE: prod`.

**Q5. What is the `CommandLineRunner` bean in `BookNetworkApplication` for?**

بيشتغل مرة واحدة بعد ما التطبيق يقوم، وبيضيف role اسمه `USER` لو مش موجود. من غيره التسجيل بيفشل برسالة "ROLE USER was not initialized".
في المشاريع الحقيقية الأحسن تبقى Flyway migration.

**Q6. Why DTOs and not return the entities directly? Why records for requests?**

- **الـ DTOs:**
  - بتخبي حاجات زي الباسوورد والعلاقات.
  - بتمنع infinite recursion (Book ↔ Feedback) و `LazyInitializationException`.
  - بتخلي الـ API contract مستقل عن شكل الداتابيز.
- **الـ Records:**
  - مش بتتغير (immutable) ومن غير boilerplate.
  - شغالة كويس مع Bean Validation و Jackson.

**⭐ Q7. How does `@Async` work in `EmailService`? What if sending fails?**

الـ `@EnableAsync` مع `@Async` بيخلوا Spring يعمل proxy يشغّل الميثود على thread pool، فالتسجيل بيرجع فورًا من غير ما يستنى الإيميل.
- لو الميثود `void` ورمت exception، الغلط **مش بيوصل للي نادى عليها**. بيروح لـ `AsyncUncaughtExceptionHandler` وبيتكتب في اللوج بس (اتجرب ✅).
  وعشان كده `throws MessagingException` في الـ controllers ملهاش لازمة.
- **فخ:** لو الميثود اتنادت من جوه نفس الكلاس (self-invocation) مش هتبقى async، لأن الاستدعاء مش بيعدّي على الـ proxy.

### 3.2 Security و JWT

**⭐ Q8. Explain the full authentication flow: register, activate, login, then an authenticated request.**

1. **التسجيل (Register):** اليوزر بيتحفظ بـ `enabled=false`، والباسوورد متشفّر بـ BCrypt، ومعاه role `USER`. بعدين بيتعمل كود 6 أرقام بـ `SecureRandom`، صالح 15 دقيقة، وبيتبعت إيميل (Thymeleaf template).
2. **التفعيل (Activate):** `POST /auth/activate-account?token=` بتعمل `enabled=true` وتحفظ `validatedAt`.
3. **الدخول (Login):** `POST /auth/authenticate`، وبعدها `AuthenticationManager`، وبعدها `DaoAuthenticationProvider`، وده بيحمّل اليوزر بالإيميل ويقارن الباسوورد ويتأكد إنه enabled و مش locked. بعد كده `JwtService` بيعمل token.
4. **أي طلب بعد كده:** Angular بيحط `Authorization: Bearer <token>` في الـ header، و `JwtAuthFilter` بيتأكد منه ويحط اليوزر في الـ `SecurityContext`، والـ controller بياخده كـ `Authentication connectedUser`.

**⭐ Q9. How does `JwtAuthFilter` work?**

الفلتر بيعمل extend لـ `OncePerRequestFilter` (بيشتغل مرة واحدة لكل request)، وخطواته:
1. أي path بيبدأ بـ `/auth` بيعدّي من غير check.
2. بيقرا الـ header، ولو مش `Bearer ` بيسيب الطلب يكمل من غير authentication.
3. الميثود `extractUsername` بتتأكد من الـ signature بالمفتاح، وبتطلّع الإيميل من `sub`.
4. بعدها `loadUserByUsername`، وبعدها `isTokenValid` (نفس اليوزر، والـ token مش expired).
5. بيعمل `UsernamePasswordAuthenticationToken` بالـ authorities، ويحطه في `SecurityContextHolder`.

الفلتر متسجل بـ `addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)`.

**⭐ Q10. What's inside the JWT? Is it encrypted?**

- **الـ header:** `{"alg":"HS256"}`.
- **الـ payload:** `sub` (الإيميل)، و `fullName`، و `authorities: ["USER"]`، و `iat`، و `exp`.
- **الـ signature:** HMAC-SHA256 بالـ secret.

الـ token **signed مش encrypted**. الـ payload مجرد Base64URL، وأي حد يقدر يقراه على jwt.io، فمينفعش يتحط فيه أي حاجة سرية. الـ signature بتمنع إن حد يعدّل فيه.

**⭐ Q11. How long is the token valid? What happens after it expires?**

القيمة `expiration: 8640000` ms، يعني **2.4 ساعة**.
- بعد ما يخلص، jjwt بيرمي `ExpiredJwtException` جوه الفلتر، والرد دلوقتي 403 فاضي. المفروض يبقى 401 (غلط 13).
- في Angular، الـ guard بيشيك على الـ expiry بـ `JwtHelperService.isTokenExpired` ويرجّع اليوزر للـ login وقت التنقل.
- مفيش refresh token، فاليوزر لازم يعمل login تاني.

**Q12. How do you implement logout with JWT?**

الـ JWT stateless، فالـ logout الحالي هو إن الفرونت يمسح الـ token (`MenuComponent.logout()` بتنادي `clearToken()`).
السيرفر مش بيقدر "يلغي" token قبل الـ `exp` إلا بحاجة من دول:
- قايمة denylist في Redis لحد ما الـ token يخلص.
- استخدام access token قصير مع refresh token محفوظ في الداتابيز ويتلغي.
- رقم token version لكل يوزر في الداتابيز.

**⭐ Q13. Why is CSRF disabled? And what does `STATELESS` mean?**

- **الـ CSRF:** هجوم الـ CSRF معتمد إن المتصفح بيبعت الـ cookies لوحده. هنا الـ token بيتبعت يدوي في الـ `Authorization` header، فالـ CSRF مش بيأثر.
  لو الـ JWT اتنقل لـ cookie، لازم CSRF يرجع يشتغل، أو يتستخدم `SameSite=Strict`.
- **الـ `SessionCreationPolicy.STATELESS`:** معناها إن Spring Security مش بيعمل `HttpSession` خالص، وكل request لازم يكون معاه الـ token بتاعه.
  وده بيسهّل الـ horizontal scaling، لأن أي instance تقدر ترد على أي request.

**Q14. How are passwords stored?**

بـ `BCryptPasswordEncoder`. بيحط salt عشوائي وليه cost قابل للزيادة (الافتراضي 10)، وهو one-way hash مش تشفير، فمفيش decrypt.
في الـ login، `DaoAuthenticationProvider` بيستخدم `passwordEncoder.matches`.

**Q15. What happens at login if the account isn't activated or the password is wrong?**

الـ `DaoAuthenticationProvider` بيرمي واحد من دول:
- لو الأكونت لسه متفعّلش: `DisabledException`.
- لو الباسوورد غلط: `BadCredentialsException`.
- لو الأكونت مقفول: `LockedException`.

والـ `GlobalExceptionHandler` بيرجّع **401** ومعاه `businessErrorCode` (303 أو 304 أو 302).

**Q16. Why do you get 403 and not 401 when the token is missing or invalid?**

اتجرب ✅. السبب إن مفيش `AuthenticationEntryPoint` متعرّف (مفيش httpBasic ولا formLogin)، فـ Spring بيستخدم `Http403ForbiddenEntryPoint`.
وكمان أخطاء jjwt بتطلع من الفلتر من غير ما حد يمسكها.
الحل: `HttpStatusEntryPoint(UNAUTHORIZED)` مع try/catch لـ `JwtException`.

**⭐ Q17. What is CORS and how is it configured here?**

المتصفح بيمنع أي طلب من origin لـ origin تاني (من 4200 لـ 8088) إلا لو السيرفر سامح.
الـ `BeansConfig.corsFilter()` مظبوط كده:
- الـ origin: `http://localhost:4200`.
- مسموح بالـ credentials (`allowCredentials`).
- الـ headers: `Origin` و `Content-Type` و `Accept` و `Authorization`.
- الـ methods ومنها `PATCH`.

و `.cors(withDefaults())` في `SecurityConfig` بياخد الـ bean ده. وقبل الطلبات "الخطيرة"، المتصفح بيبعت **preflight** `OPTIONS`.
**ملحوظة:** الـ origin مكتوب ثابت، والمفروض يبقى configurable لكل بيئة.

**⭐ Q18. Can user B edit user A's book?**

في الكود الحالي **أيوه** (غلط 1، واتجرب ✅). ده اسمه **IDOR / Broken Access Control**، وهو رقم 1 في OWASP Top 10.
- **الحل:** check الملكية في الـ service، وده الأحسن لأنه قريب من البيزنس.
- **أو:** `@PreAuthorize("@bookSecurity.isOwner(#bookId, authentication)")` بـ bean مخصوص.
- الرد يبقى 403، أو 404 لو مش عايزين نكشف إن الكتاب موجود.

**Q19. Where is the JWT secret stored? What's the risk?**

مكتوب في الـ YAML ومرفوع على GitHub (غلط 3). اتعمل بيه token مزوّر ودخل ✅.
الحل:
- يتقري من environment variable أو secret manager.
- يبقى فيه secret مختلف لكل بيئة.
- يتعمل rotate للـ secret الحالي.
- الـ secret يبقى 256 bit على الأقل لـ HS256، والحالي 32 byte فتمام.

**Q20. What is `@EnableMethodSecurity(securedEnabled = true)` for?**

بتشغّل `@PreAuthorize` و `@PostAuthorize` و `@Secured` على الميثودز. مش مستخدمة لسه، وهتنفع لو اتضاف ADMIN.
**فخ حلو:** الـ roles هنا اسمها `USER` من غير `ROLE_`، فـ `hasRole('USER')` **مش هتشتغل**، لأنها بتدور على `ROLE_USER`. الصح هنا `hasAuthority('USER')`.

### 3.3 JPA و Hibernate والداتابيز

**⭐ Q21. Explain the entities and their relationships.**

- كل `User` عنده كتب كتير (العلاقة اسمها `Book.owner`).
- كل `Book` ليه `Feedback` كتير.
- جدول `BookTransactionHistory` بيربط `User` بـ `Book`، وده سجل الاستلاف، وفيه `returned` و `returnApproved`.
- العلاقة بين `User` و `Role` هي many-to-many، والـ join table اسمه `_user_roles`، والـ roles بتتحمل EAGER.
- كل `Token` (كود التفعيل) تبع `User` واحد.
- الكلاس `BaseEntity` معمول `@MappedSuperclass`، وفيه `id` وحقول الـ auditing، و `Book` و `Feedback` و `BookTransactionHistory` بيورثوا منه.

**Q22. Why is the table called `_user`?**

لأن `user` كلمة محجوزة (reserved word) في PostgreSQL.

**⭐ Q23. How does auditing work (`@CreatedDate`, `@CreatedBy`)?**

محتاجة 3 حاجات:
- `@EnableJpaAuditing(auditorAwareRef = "auditAware")`.
- `@EntityListeners(AuditingEntityListener.class)` على `BaseEntity`.
- كلاس `ApplicationAuditAware` بيقرا اليوزر من الـ `SecurityContext`.

والتواريخ بتتملى لوحدها. `createdBy` بيتحفظ فيه **الإيميل**، وبيتستخدم في `FeedbackMapper` عشان يعرف `ownFeedback`.
**عيب بسيط:** لو اليوزر غيّر إيميله، الربط ده هيبوظ، والأحسن يتحفظ الـ id.

**⭐ Q24. LAZY vs EAGER, and is there an N+1 problem?**

- **الافتراضي:** `@ManyToOne` بيبقى EAGER، و `@OneToMany` بيبقى LAZY.
- **في المشروع:** `Book.owner` EAGER، و `User.roles` EAGER صريح، و `Book.feedbacks` LAZY.
- **فيه N+1:** لستة 10 كتب بتعمل query للكتب وquery للـ count. وبعدين لكل كتاب: query للـ owner وroles بتاعه، وquery للـ feedbacks عشان يحسب الـ rate.
- **الحل:** واحد من دول:
  - `JOIN FETCH` أو `@EntityGraph(attributePaths = "owner")`.
  - `@BatchSize`.
  - استخدام DTO projection بتحسب `AVG(f.note)` بـ `GROUP BY` في query واحدة.

**Q25. What is open-in-view? Why does lazy loading work in the mapper without `@Transactional`?**

الإعداد `spring.jpa.open-in-view` شغال افتراضيًا، ومعناه إن الـ EntityManager بيفضل مفتوح طول الـ request، فالـ lazy loading بيشتغل حتى في الـ mapper.
عيوبه:
- الـ DB connection بيفضل ماسك طول الطلب.
- الـ queries بتتعمل في أماكن مش متوقعة.

واللوج بيطلّع warning عليه. الأحسن يتقفل، ويتستخدم `@Transactional(readOnly = true)` في الـ services.

**⭐ Q26. Where is `@Transactional` used? Where is it missing? What about rollback?**

- **مستخدم في:** `FeedbackService.save` بس. كل ميثود في Spring Data repository هي transaction لوحدها.
- **ناقص في:** العمليات اللي فيها أكتر من خطوة زي `borrowBook`، ودي محتاجة transaction مع lock.
- **الـ rollback الافتراضي:** بيحصل مع `RuntimeException`، ومش بيحصل مع checked exceptions زي `MessagingException` إلا لو اتكتب `rollbackFor`.
- **فخ حلو:** لو `@Transactional` اتحط على `activateAccount`، الـ branch بتاع الكود المنتهي هيحفظ كود جديد ويبعته بالإيميل، وبعدين يرمي `RuntimeException`. الـ rollback هيمسح الكود الجديد، مع إن الإيميل اتبعت خلاص.

**⭐ Q27. Is there a concurrency problem when borrowing?**

أيوه (غلط 4، واتجرب ✅: 4 من 5 مرات اتسلف مرتين). السبب إنه check ثم act من غير lock.
- **قفل pessimistic:** `SELECT ... FOR UPDATE` جوه `@Transactional`.
- **قفل optimistic:** `@Version`، ولو حصل تعارض بيترمي `OptimisticLockException` ويتعمل retry أو يرجع 409.
- **حماية على مستوى الداتابيز:** unique partial index.

**Q28. How is pagination implemented?**

بيتعمل `PageRequest.of(page, size, Sort.by("createdDate").descending())`، والنتيجة `Page<T>` بتتحول لـ `PageResponse`.
- الـ `Page` بيعمل count query. لو مش محتاجين العدد الكلي، `Slice` أسرع.
- الـ sort مهم عشان الصفحات تبقى ثابتة، وفي `findAllFeedbacksByBook` مفيش sort.
- وفيه bug في رقم الصفحة (غلط 10).

**Q29. JPQL `@Query` vs derived queries vs Specification: examples from the project?**

- **الـ Derived query:** `findByEmail`، والاسم نفسه هو الـ query.
- **الـ JPQL:** `findAllDisplayedBooks`، وده أوضح لما الشروط تبقى كتير.
- **الـ Specification:** `BookSpecification.withOwnerId`، مع `JpaSpecificationExecutor`، ودي أحسن حاجة للفلاتر الديناميكية زي البحث.

**Q30. (Trick) How do `:bookId` parameters work in `@Query` without `@Param`?**

لأن `spring-boot-starter-parent` بيشغّل الـ compiler flag `-parameters`، فأسماء الـ parameters بتتحفظ في الـ bytecode.

**Q31. How are IDs generated? Why is there an uploads folder `user/154`?**

الـ `@GeneratedValue` (AUTO) في PostgreSQL معناها sequence لكل entity، وده اتشاف في الداتابيز: `book_seq` بـ increment 50.
والـ Hibernate بيحجز 50 رقم مرة واحدة (pooled optimizer)، فبعد كل restart الأرقام ممكن تقفز 50.

**Q32. Is `ddl-auto: update` OK for production?**

لأ. مش بيمسح أعمدة ولا بيعمل rename، ومفيش history للتغييرات، وممكن يعمل حاجة مش متوقعة.
الصح: `validate` مع **Flyway** أو **Liquibase** migrations متسجلة في git.

**Q33. How do you prevent duplicate emails?**

الـ `@Column(unique = true)` موجود، وده constraint في الداتابيز، بس بيطلّع 500 (غلط 11).
الحل: check بـ `findByEmail` قبل الحفظ، ويرجع 409. ولازم كمان يتمسك `DataIntegrityViolationException`، عشان لو طلبين وصلوا في نفس اللحظة الاتنين هيعدّوا الـ check.

**Q34. Why `@SuperBuilder` and not `@Data` on entities?**

- **الـ `@SuperBuilder`:** عشان الـ builder بتاع `Book` يشمل حقول `BaseEntity`.
- **استخدام `@Data` على entity فكرة وحشة**، لأن `equals` و `hashCode` و `toString` بتلف على كل الحقول:
  - ممكن تحمّل علاقات lazy من غير قصد.
  - ممكن تعمل StackOverflow بسبب العلاقات اللي بتشاور على بعض.
- **المشروع** مستخدم `@Getter` و `@Setter` بس، وده صح.

### 3.4 تصميم الـ API والـ Errors

**⭐ Q35. How does the global exception handler work? What would you improve?**

الـ `@RestControllerAdvice` فيه `@ExceptionHandler` لكل نوع، وبيرجّع `ExceptionResponse`، وفيه `businessErrorCode` من الـ enum `BusinessErrorCodes`.
المشاكل (غلط 12، اتجرب ✅):
- الـ catch-all بيحوّل 404 و 400 لـ 500.
- بيكشف رسايل داخلية.
- بيستخدم `printStackTrace`.

التحسين:
- يتعمل handler مخصوص لكل نوع.
- استخدام `ProblemDetail` (RFC 9457).
- يتعمل logging صح.

**Q36. How does validation work? Why are the messages numbers like `"100"`?**

الـ `@Valid @RequestBody` مع constraints على الـ record. لو في غلط بيترمي `MethodArgumentNotValidException`، والرد بيبقى 400 وفيه `{"validateErrors":["100","101",...]}`.
الأكواد كانت متعمولة عشان الفرونت يترجمها (i18n)، بس الفرونت مش بيعمل ده.
ملاحظات:
- الـ `@NotEmpty` بيشمل `@NotNull` أصلًا.
- الـ `@NotBlank` أحسن للنصوص.

**Q37. Is this API RESTful? What would you change?**

- **الكويس:**
  - الـ URLs أسماء (nouns).
  - الـ pagination بـ query params.
  - استخدام `PATCH` للتعديلات الجزئية.
  - كود 201 للتسجيل.
- **اللي محتاج يتغير:**
  - الـ `POST /books` بيعمل create و update الاتنين، والأحسن `PUT /books/{id}` للتعديل.
  - الـ create يرجع 201 ومعاه `Location` header.
  - الـ toggles (`PATCH /books/shareable/{id}`) مش idempotent، والأحسن `PATCH /books/{id}` ومعاه body `{"shareable": true}`.
  - الـ upload بيرجع 202، ودي معناها "هيتعمل بعدين"، والأصح 200 أو 204.
  - كلمة `totalElments` فيها typo جوه الـ contract.

**⭐ Q38. Explain the borrow, return, approve flow.**

كل عملية استلاف ليها صف في `BookTransactionHistory`:
```
borrow  → returned=false, returnApproved=false   (الكتاب مع المستلف)
return  → returned=true                          (المستلف رجّعه)
approve → returnApproved=true                    (المالك أكد، والكتاب بقى متاح تاني)
```
والـ `isAlreadyBorrowed` بيدور على أي صف فيه `returnApproved=false`.
- **الشروط:**
  - مينفعش حد يستلف كتابه.
  - الكتاب لازم يبقى shareable ومش archived.
  - الكتاب مش متسلف لحد تاني.
- **العيوب:** الـ archive وهو متسلف (غلط 9)، والـ race (غلط 4).

**Q39. How does file upload work? What would you change?**

الـ endpoint بياخد `@RequestPart("file") MultipartFile` مع `consumes = multipart/form-data`. الصورة بتتحفظ على الديسك في `./uploads/user/{id}/{timestamp}.{ext}`، والـ path بيتحفظ في الداتابيز. ولما حد يطلب الكتاب، الصورة بتتقري وتتبعت `byte[]`، يعني Base64 جوه الـ JSON.
المشاكل:
- الحد الحقيقي 10MB (غلط 16).
- مفيش check ملكية (غلط 2).
- بيثق في الـ content-type.
- الـ Base64 تقيل في اللستة.
- الديسك المحلي مش بيعمل scale، والـ container بيضيّع الصور.

الأحسن: S3 أو MinIO، ويترجع URL للصورة، ولو فيه CDN يبقى أحسن.

**Q40. What is springdoc / Swagger used for here?**

الـ springdoc بيولّد `/v3/api-docs` و swagger-ui لوحده. `@SecurityScheme(name = "bearerAuth")` بيخلي ممكن تحط الـ JWT في Swagger UI وتجرب.
والفرونت بيولّد الـ client بتاعه من الـ `openapi.json` ده بـ ng-openapi-gen.
في prod، الأحسن Swagger يتقفل أو يتحمي.

### 3.5 الإيميل والتفعيل

**Q41. Explain account activation. What are its weaknesses?**

- **الفلو:** كود 6 أرقام بـ `SecureRandom`، صالح 15 دقيقة، محفوظ في جدول `token`. لو الكود انتهى، بيتبعت كود جديد وبيرجع error.
- **ليه `SecureRandom` مش `Random`:** `Random` ممكن حد يتوقع الأرقام اللي جاية منه.
- **العيوب (غلط 15):**
  - مفيش rate limit، فممكن تجربة كل الاحتمالات.
  - الكود مش unique، وممكن يتكرر بين يوزرز.
  - مش مربوط بالإيميل.
  - ممكن يتستخدم تاني ✅.
  - مفيش resend.

**Q42. How is the email built and tested locally?**

الإيميل معمول بـ Thymeleaf template في `templates/activate_account.html`. `SpringTemplateEngine.process(name, context)` بيطلّع HTML، و `MimeMessageHelper` بيبعته.
في الـ dev فيه **MailDev** في docker-compose: الـ SMTP على 1025، والـ UI على `localhost:1080` وبيعرض الإيميلات اللي اتبعتت.

### 3.6 Testing و DevOps

**⭐ Q43. What tests did you write? How do you unit test a service?**

- **كلاس `FeedbackServiceTest`:**
  - `@ExtendWith(MockitoExtension.class)`.
  - الـ `@Mock` للـ repositories، و `@InjectMocks` للـ service.
  - `when(...).thenReturn(...)` و `assertThrows`.
  - `verify(repo, never()).save(any())` و `verifyNoInteractions`.
- **كلاس `EmailServiceTest`:** بيستخدم `ArgumentCaptor` عشان يتأكد من الـ subject.
- **الـ `contextLoads`:** معمول `@SpringBootTest`، ومحتاج داتابيز.

الـ 13 ناجحين ✅.
**الناقص:**
- اختبارات لـ `BookService`.
- اختبارات للـ controllers بـ `@WebMvcTest` أو MockMvc مع `spring-security-test`.
- اختبارات للـ repositories بـ `@DataJpaTest` و **Testcontainers**.

وفي Boot 4 بيتستخدم `@MockitoBean`، مش `@MockBean` القديمة.

**⭐ Q44. Explain the Dockerfile and docker-compose.**

- **الـ Dockerfile (multi-stage):**
  - المرحلة الأولى Maven بيبني الـ jar. `dependency:go-offline` بيعمل cache layer للـ dependencies.
  - المرحلة التانية `amazoncorretto:17` فيها الـ jar بس، فالـ image بتبقى أصغر ومن غير أدوات build.
- **الـ Compose:**
  - خدمة postgres ومعاها volume.
  - خدمة pgadmin.
  - خدمة maildev.
  - خدمة bsn-api، ومتظبط ليها `DB_URL` و `MAILDEV_URL` و `ACTIVE_PROFILE=prod`.
  - خدمة bsn-api-ui (nginx).
  - كلهم على نفس الـ network `spring-demo`، فبيكلموا بعض بالاسم (`postgres:5432`).
- **تحسينات:**
  - إضافة healthchecks مع `depends_on: condition: service_healthy`.
  - إضافة volume لـ `uploads`.
  - يوزر non-root.
  - بناء الـ image بـ JDK 17 أو 21.
  - الـ secrets من `.env`.

**Q45. Explain the CI pipeline.**

الـ GitHub Actions بيمشي بالترتيب ده:
1. عمل compile.
2. تشغيل unit-tests، ومعاه Postgres كـ service container.
3. عمل build (`package -DskipTests`).
4. عمل build-image، وده بيقرا الـ version من الـ pom ويعمل push لـ Docker Hub باستخدام secrets.

**التحسين:**
- يشتغل على `push` و `pull_request` بدل التشغيل اليدوي بس.
- إضافة `cache: maven` في setup-java.
- إضافة job للفرونت.
- الـ build يتعمل مرة واحدة والناتج يتنقل كـ artifact.

---

## 4. أسئلة الفرونت إند (Angular)

**⭐ Q1. How is the Angular app structured and bootstrapped?**

المشروع Angular 21 بـ **standalone components** من غير `NgModule`. التطبيق بيبدأ بـ `bootstrapApplication(App, appConfig)`.
في `app.config.ts`:
- `provideRouter(routes)`.
- `provideHttpClient(withFetch(), withInterceptors([httpTokenInterceptor]))`.
- `provideBrowserGlobalErrorListeners()`.

الفولدرات:
- فولدر `pages/` فيه login و register و activate.
- فولدر `book/pages/` فيه صفحات الكتب.
- فولدر `book/components/` فيه الكارت والمنيو والنجوم.
- فولدر `services/` فيه الـ client الـ generated و token و guard و interceptor.

**⭐ Q2. How does routing and lazy loading work here?**

- كل صفحة معمولة بـ `loadComponent: () => import(...)`، فكل صفحة بتبقى chunk لوحدها وبتتحمل وقت ما تتطلب. ده ظاهر في الـ build، مثلًا `login-component` حجمه 2.66kB.
- الـ route `books` ليه `MainComponent` كـ layout، فيه الـ menu و `<router-outlet>`، وجواه children.
- الـ path الفاضي `''` بيعمل redirect لـ `login`.
- **الناقص:** route `**` (صفحة 404) و route التفاصيل (غلط 17).

**⭐ Q3. How does the auth guard work? Is it real security?**

الـ `authGuard` معمول functional `CanActivateFn`. بيعمل `inject(TokenService)`، ولو الـ token مش موجود أو expired (بـ `JwtHelperService`) بيروّح على login.
متحط على `canActivate` و `canActivateChild`.
**هو مش security حقيقية**، ده UX بس، لأن أي حد يقدر يعدّي الفرونت. الحماية الحقيقية في الباك.
**تحسين:** يرجّع `router.createUrlTree(['/login'])` بدل `navigate` ويرجّع `false`.

**⭐ Q4. How does the HTTP interceptor work?**

الـ `httpTokenInterceptor` معمول functional `HttpInterceptorFn`. الـ `HttpRequest` مينفعش يتعدّل (immutable)، فبيتعمل `req.clone({ setHeaders: { Authorization: 'Bearer ...' } })` وبعدين `next(req)`.
**تحسينات:**
- الـ token ميتبعتش غير للـ API بس.
- إضافة `catchError` لو الرد 401، يعمل logout ويروح login ([تعديل 11](#تعديل-11--interceptor-يتعامل-مع-401-سهل)).

**⭐ Q5. Where is the token stored? Pros and cons?**

في `localStorage`.
- **المميزات:** سهل، وبيفضل موجود بعد الـ refresh.
- **العيب:** أي JavaScript على الصفحة يقدر يقراه، فلو حصل XSS الـ token يتسرق.
- **البديل:** cookie بـ `HttpOnly; Secure; SameSite`، ومعاها CSRF protection. أو access token في الـ memory مع refresh token في cookie.

**⭐⭐ Q6. What is zoneless change detection? Why do lists appear empty?**

- **زمان:** `zone.js` كان بيراقب أي حاجة async (click أو HTTP أو setTimeout) ويشغّل change detection لوحده.
- **في Angular 21:** بقى **zoneless** افتراضيًا. Angular بيعيد الرسم بس لما:
  - قيمة signal تتغير.
  - يحصل event من الـ template (زي `(click)`).
  - حد ينادي `markForCheck()`.
  - الـ `async` pipe يجيب قيمة جديدة.
- **في المشروع:** الـ fields العادية بتتغير بعد `await`، فالشاشة مش بتتحدث (غلط 5، اتجرب ✅: 5 كتب في الـ state و 0 على الشاشة).
- **الحل:** signals ([تعديل 5](#تعديل-5--إصلاح-الشاشات-اللي-مش-بتتحدث-signals-سهل)).

**Q7. Explain signals.**

- الـ `signal(value)`: قيمة بتقراها بـ `()`، وتغيّرها بـ `.set()` أو `.update()`.
- الـ `computed()`: قيمة محسوبة من signals تانية، وبتتحدث لوحدها.
- الـ `effect()`: كود بيشتغل لما signal يتغير.
- الـ `input()` و `output()` و `model()`: البديل الجديد لـ `@Input` و `@Output`.

الـ signals للـ state، و RxJS للـ streams والأحداث. وفيه `toSignal()` بيحوّل observable لـ signal.

**Q8. Promises vs Observables: which does the project use?**

الـ `Api.invoke` الـ generated بيحوّل الـ Observable لـ Promise بـ `firstValueFrom`، والكود بيستخدم async/await.
- **ميزة الـ Promise:** بسيطة.
- **عيوبها:**
  - مفيش cancel. لو حد داس بسرعة على صفحات مختلفة، الردود ممكن توصل بترتيب غلط.
  - مفيش operators. البحث مثلًا محتاج `debounceTime` و `switchMap`.

**Q9. What is ng-openapi-gen and why use it?**

بيولّد models و functions typed من `openapi.json` بالأمر `npm run api-gen`.
المميزات: type safety، ومفيش كود HTTP بيتكتب باليد. أي تغيير في الباك محتاج إعادة توليد.
**مينفعش تعدّل الملفات الـ generated.** مثلًا `rootUrl` مكتوب جوه واحد منهم، والصح إنه يتظبط بـ `provideApiConfiguration(...)`.

**Q10. Template-driven vs Reactive forms?**

المشروع مستخدم **template-driven** (`[(ngModel)]` مع `FormsModule`)، ومفيش validation في الفرونت خالص.
الـ **Reactive forms** (`FormGroup` و `Validators.required/email/minLength(8)`) أحسن للفورمز الكبيرة وللـ validation، ويتعمل فيها نفس قواعد الباك.

**⭐ Q11. New control flow `@if/@for` and why `track` is required.**

الـ `@if` و `@else` و `@for` بدل `*ngIf` و `*ngFor`. الـ `track` إجباري عشان Angular يعرف كل عنصر، ويعيد استخدام الـ DOM بدل ما يرسم كله من الأول.
لازم يكون unique. في Borrowed books الـ track بـ id الكتاب، والكتاب ممكن يتكرر، فبيطلع `NG0955` (غلط 20 ✅).

**Q12. How do components communicate here?**

الـ `BookCardComponent` component عرض بس (presentational): بياخد `@Input() book` و `manage`، وبيطلّع أحداث بـ `@Output() EventEmitter`: `share` و `archive` و `borrow` و `edit` و `details`.
الصفحة الأب (smart/container) هي اللي بتكلم الـ API.
في Angular الجديد ممكن `input()` و `output()`. و `@Output() private` مش مظبوطة.

**Q13. Constructor vs `ngOnInit`? `inject()` vs constructor injection?**

- **الـ constructor:** للـ DI بس.
- **الـ `ngOnInit`:** للـ initialization، زي جلب الداتا. الـ inputs بتكون وصلت قبله.
- **الـ `inject()`:** بتشتغل في الـ field initializers، ومهمة في الـ functional guards والـ interceptors اللي مفيهاش constructor. المشروع مستخدم الاتنين.
- **الـ `providedIn: 'root'`:** معناها singleton على مستوى التطبيق كله، زي `TokenService` و `Api`.

**Q14. How is pagination implemented? How would you improve it?**

الـ state فيه `page` و `size`، والصفحات بتتعمل بـ `Array(totalPages).fill(0).map((x, i) => i)`، ومعاها أزرار first و prev و next و last.
الكود ده **متكرر في 4 components**، والأحسن `PaginationComponent` واحد، بياخد `page` و `totalPages` كـ input ويطلّع `pageChange`.

**Q15. How are images displayed and uploaded?**

- **العرض:** Base64 في `data:image/jpg;base64,...`.
- **المعاينة قبل الرفع:** `FileReader.readAsDataURL`.
- **الرفع:** multipart بعد حفظ الكتاب. ده طلبين ورا بعض، فلو التاني فشل الكتاب بيتحفظ من غير صورة.

**Q16. How are errors shown to the user? What's wrong now?**

صفحة الـ login بتستخدم try/catch مع `await`، والباقي بيستخدم `.catch`، والرسايل بتتقري من `validateErrors` أو `error`.
المشاكل:
- صفحة register من غير `await` (غلط 6 ✅).
- اسم الحقل غلط في manage-book (غلط 18 ✅).
- حتى لو الغلط اتمسك، مش بيظهر بسبب الـ zoneless (غلط 5 ✅).

**التحسين:** interceptor مركزي للأخطاء مع toast service.

**Q17. Angular and security (XSS)?**

- الـ interpolation `{{ }}` بيعمل escape لوحده، و `[innerHTML]` بيتعمل له sanitize.
- الـ `bypassSecurityTrust*` خطيرة.
- الـ guards مش security.
- مفيش أي secret المفروض يتحط في الفرونت.

**⭐ Q18. How is the frontend built and deployed?**

الأمر `ng build` بيطلّع الملفات في `dist/book-network-ui/browser`، وده جوه container فيه nginx.
الـ `nginx.conf` فيه `try_files $uri $uri/ /index.html`. ده مهم عشان لو حد عمل refresh على `/books/my-books`، nginx يرجّع `index.html` والـ Angular router يكمل.
الـ budgets في `angular.json`، والـ build بيطلّع warning (566kB أكبر من 500kB ✅).

**Q19. Why is there `isPlatformBrowser` in the guard and TokenService?**

دي بقايا SSR. على السيرفر مفيش `localStorage` ولا `window`.
بس الـ SSR مش متفعّل في `angular.json` مع إن الـ packages متسطبة، فالأحسن يتشالوا أو الـ SSR يتفعّل صح.

**Q20. How do you test Angular components?**

الـ Angular 21 بيستخدم **Vitest** مع `TestBed`. الـ specs الموجودة هي الافتراضية، و 5 من 18 بيفشلوا ✅: الـ `app.spec` مستني `<h1>Hello`، والـ components اللي فيها `RouterLink` مش لاقية `ActivatedRoute`.
**الحل:**
- `providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()]`.
- `HttpTestingController` عشان تعمل mock للـ API.

**Q21. How would you improve performance?**

- الـ lazy loading (موجود).
- استخدام signals.
- الـ `track` يبقى صح.
- مفيش Base64 في اللستات.
- استخدام `debounce` في البحث.
- استخدام `@defer` للأجزاء التقيلة.
- استيراد الأجزاء المطلوبة بس من Bootstrap و FontAwesome.

**Q22. UX and accessibility issues?**

- الأيقونات اللي بتتداس هي `<i>` مش `<button>`، فمش بتشتغل بالكيبورد ومفيهاش `aria-label`.
- مفيش loading state.
- الأزرار مش بتتقفل وقت الطلب، فالـ double click بيبعت طلبين، وده بيساعد على غلط 4.
- الـ archive مفيهوش confirmation.

---

## 5. لو طلبوا تعديل أو Live coding

> دي أكتر تعديلات متوقعة، مرتبة من الأرجح للأقل. الأكواد مكتوبة على نفس ستايل وأسماء المشروع.

### تعديل 1 — إصلاح الـ IDOR (سهل)
في `BookService.save()` جوه `if (request.id() != null)`، وبنفس الشكل في `uploadBookCoverPicture()`:
```java
book = bookRepository.findById(request.id())
        .orElseThrow(() -> new EntityNotFoundException("No book found with ID:: " + request.id()));
if (!Objects.equals(book.getOwner().getId(), user.getId())) {
    throw new OperationNotPermittedException("You cannot update others books");
}
```

### تعديل 2 — Delete book (متوسط)
```java
// BookController
@DeleteMapping("/{book-id}")
public ResponseEntity<Void> deleteBook(@PathVariable("book-id") Integer bookId, Authentication connectedUser) {
    service.deleteBook(bookId, connectedUser);
    return ResponseEntity.noContent().build();
}

// BookService
@Transactional
public void deleteBook(Integer bookId, Authentication connectedUser) {
    Book book = bookRepository.findById(bookId)
            .orElseThrow(() -> new EntityNotFoundException("No book found with ID:: " + bookId));
    User user = (User) connectedUser.getPrincipal();
    if (!Objects.equals(book.getOwner().getId(), user.getId())) {
        throw new OperationNotPermittedException("You cannot delete others books");
    }
    if (bookTransactionHistoryRepository.isAlreadyBorrowed(bookId)) {
        throw new OperationNotPermittedException("The book is currently borrowed");
    }
    bookRepository.delete(book);
}
```
**نقطة هيسألوا فيها:** الـ feedbacks والـ history فيهم foreign key على الكتاب، فالـ delete هيفشل لو فيه صفوف مربوطة بيه. الحلول:
- تمسحهم الأول.
- أو **soft delete**، وده الأحسن. المشروع أصلًا فيه `archived`، وممكن يتضاف `deleted` بنفس الطريقة، والـ history يفضل للـ audit.

وفي الفرونت: زرار في `BookCardComponent` (في وضع `manage`) عليه `(delete)` output، وقبل الحذف `confirm()`.

### تعديل 3 — البحث عن كتاب بالعنوان أو المؤلف (متوسط)
الـ `JpaSpecificationExecutor` موجود أصلًا:
```java
// BookSpecification
public static Specification<Book> isDisplayedFor(Integer userId) {
    return (root, query, cb) -> cb.and(
            cb.isFalse(root.get("archived")),
            cb.isTrue(root.get("shareable")),
            cb.notEqual(root.get("owner").get("id"), userId));
}

public static Specification<Book> titleOrAuthorContains(String keyword) {
    return (root, query, cb) -> {
        String like = "%" + keyword.toLowerCase() + "%";
        return cb.or(
                cb.like(cb.lower(root.get("title")), like),
                cb.like(cb.lower(root.get("autherName")), like));
    };
}

// BookService
Page<Book> books = bookRepository.findAll(
        BookSpecification.isDisplayedFor(user.getId())
                .and(BookSpecification.titleOrAuthorContains(keyword)),
        pageable);
```
وفي الـ controller: `@GetMapping("/search")` مع `@RequestParam String keyword` و page و size.
في الفرونت:
1. إضافة `[(ngModel)]` على خانة البحث في الـ navbar.
2. استخدام `router.navigate(['/books'], { queryParams: { q } })`.
3. الـ `BookListComponent` يسمع لـ `queryParamMap`.

ويستحسن `debounceTime`.

### تعديل 4 — اسم اليوزر الحقيقي في الـ navbar (سهل)
```ts
// token-service.ts
get fullName(): string {
  const token = this.token;
  return token ? this.jwtHelper.decodeToken(token)?.fullName ?? '' : '';
}

// menu-component.ts
private tokenService = inject(TokenService);
protected readonly fullName = this.tokenService.fullName;
```
```html
<span class="text-capitalize fw-bold">{{ fullName }}</span>
```

### تعديل 5 — إصلاح الشاشات اللي مش بتتحدث (signals) (سهل)
مثال على `BookListComponent`، ونفس الفكرة في باقي الصفحات:
```ts
bookResponse = signal<PageResponseBookResponse>({});
pages = computed(() => Array.from({ length: this.bookResponse().totalPages ?? 0 }, (_, i) => i));

private async findAllBooks() {
  try {
    this.bookResponse.set(await this.api.invoke(findAllBooks, { page: this.page, size: this.size }));
  } catch (err) {
    console.log(err);
  }
}
```
```html
@for (book of bookResponse().content; track book.id) { ... }
@for (pageIndex of pages(); track pageIndex) { ... }
```
وأي field بيتغير بعد `await`، زي `message` و `errorMsg` و `submitted`، لازم يبقى signal هو كمان.

### تعديل 6 — صفحة تفاصيل الكتاب مع التعليقات (متوسط)
1. إضافة route `{ path: 'details/:bookId', loadComponent: ... BookDetailsComponent }` جوه children الـ `books`.
2. في `BookDetailsComponent` يتنادي `findBookById` و `findAllFeedbackByBook`، والنتيجة تتحط في signals، ومعاها pagination للتعليقات.
3. التعليق اللي `ownFeedback = true` يتعلّم بلون مختلف.

### تعديل 7 — منع تكرار الإيميل (سهل)
```java
// AuthenticationService.register — قبل الحفظ
if (userRepository.findByEmail(request.getEmail()).isPresent()) {
    throw new EmailAlreadyUsedException("Email already registered");
}
```
مع handler بيرجّع **409**، و code جديد في `BusinessErrorCodes`.

### تعديل 8 — تغيير الباسوورد (متوسط)
دي **متوقعة جدًا**، لأن الأكواد `INCORRECT_CURRENT_PASSWORD (300)` و `NEW_PASSWORD_DOES_NOT_MATCH (301)` موجودة في `BusinessErrorCodes` ومش مستخدمة.
الخطوات:
1. إضافة endpoint `PATCH /users/password` بياخد body `{ currentPassword, newPassword, confirmationPassword }`.
2. التأكد بـ `passwordEncoder.matches(current, user.getPassword())`، ولو غلط يرمي 300.
3. لو الجديد مش زي التأكيد يرمي 301.
4. حفظ الباسوورد الجديد: `user.setPassword(passwordEncoder.encode(newPassword))`.

### تعديل 9 — إعادة إرسال كود التفعيل (سهل)
إضافة `POST /auth/resend-code?email=`:
- لو اليوزر موجود ولسه مش `enabled`، يتعمل كود جديد ويتبعت.
- **الرد يبقى هو هو في كل الحالات**، عشان محدش يعرف مين مسجّل (user enumeration).
- مع rate limit.

### تعديل 10 — Feedback مرة واحدة ولمن استلف بس (متوسط)
- استخدام query `existsBy...` يتأكد إن فيه transaction للكتاب ده باسم اليوزر ده، وفيها `returned = true`.
- التأكد إن مفيش feedback قبل كده من نفس اليوزر لنفس الكتاب، ومعاه unique constraint على `(created_by, book_id)`.

### تعديل 11 — Interceptor يتعامل مع 401 (سهل)
```ts
export const httpTokenInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  const token = tokenService.token;
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        tokenService.clearToken();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};
```
ده محتاج الباك يرجّع 401 صح (غلط 13).

### تعديل 12 — منع السلف المزدوج (متوسط)
```java
// BookRepository
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT b FROM Book b WHERE b.id = :id")
Optional<Book> findByIdForUpdate(@Param("id") Integer id);

// BookService
@Transactional
public Integer borrowBook(Integer bookId, Authentication connectedUser) {
    Book book = bookRepository.findByIdForUpdate(bookId)
            .orElseThrow(() -> new EntityNotFoundException("No book found with ID:: " + bookId));
    // ... نفس الـ checks والـ save
}
```
الطلب التاني بيستنى لحد ما الأول يعمل commit، وبعدها `isAlreadyBorrowed` بترجع `true` فبيترفض.

### تعديل 13 — Error handling صح (سهل)
```java
@ExceptionHandler(EntityNotFoundException.class)
public ResponseEntity<ExceptionResponse> handleException(EntityNotFoundException exp) {
    return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ExceptionResponse.builder().error(exp.getMessage()).build());
}
```
ونفس الفكرة لـ 400 و 413. والـ catch-all يرجّع رسالة عامة بس، ويعمل `log.error("Unexpected error", exp)`.

### تعديل 14 — Unit test لـ `borrowBook` (سهل)
```java
@ExtendWith(MockitoExtension.class)
class BookServiceTest {
    @Mock private BookRepository bookRepository;
    @Mock private BookTransactionHistoryRepository bookTransactionHistoryRepository;
    @Mock private BookMapper bookMapper;
    @Mock private FileStorageService fileStorageService;
    @Mock private Authentication authentication;
    @InjectMocks private BookService bookService;

    @Test
    void shouldNotBorrowOwnBook() {
        User owner = User.builder().id(1).build();
        Book book = Book.builder().id(5).owner(owner).shareable(true).archived(false).build();
        when(bookRepository.findById(5)).thenReturn(Optional.of(book));
        when(authentication.getPrincipal()).thenReturn(owner);

        assertThrows(OperationNotPermittedException.class, () -> bookService.borrowBook(5, authentication));
        verify(bookTransactionHistoryRepository, never()).save(any());
    }
}
```

### تعديلات تانية ممكن تيجي
- **إضافة ADMIN role:**
  - إضافة role `ADMIN` في الـ seed.
  - عمل endpoint بـ `@PreAuthorize("hasAuthority('ADMIN')")` يعرض كل اليوزرز أو يعمل lock لأكونت.
- **قايمة الانتظار (Waiting list):**
  - عمل entity `WaitingList(user, book)` و endpoints للإضافة والحذف والعرض.
  - صفحة `my-waiting-list`.
  - إيميل لما الكتاب يرجع (bonus).
- **الـ Refresh token:** refresh token طويل محفوظ في الداتابيز ويتلغي، و access token قصير.
- **فورم التسجيل بـ Reactive Forms:** validators زي الباك بالظبط، ورسايل تحت كل خانة.
- **الأغلفة كـ URL:** endpoint `GET /books/{id}/cover` يرجّع الصورة (`image/jpeg`) بدل Base64 في اللستة.
- **الترتيب (Sorting):** `sort=title,asc` في اللستة.
- **الـ API URL في `environment.ts`:** بدل ما يبقى ثابت في ملف generated.

---

## 6. حاجات تانية مهمة قبل الإنترفيو

### أ) أهم حاجات تتصلح الأول (تقريبًا يوم شغل)
1. إضافة check الملكية في `save` و `uploadBookCoverPicture` (غلط 1 و 2).
2. الـ JWT secret يتنقل لـ environment variable، ويتغيّر (غلط 3).
3. استخدام signals في الصفحات اللي فيها داتا async (غلط 5)، ودي أكتر حاجة هتبان لو حد شغّل المشروع قدامه.
4. إضافة `await` في register، و `shareable: false` افتراضي، و `@NotNull` على `note` (غلط 6 و 7 و 8).
5. رجوع 404 و 401 صح (غلط 12 و 13).
6. إضافة `@Transactional` مع lock في `borrowBook` (غلط 4).
7. فولدر `uploads/` يتشال من git ويتضاف لـ `.gitignore`، والـ port يتوحّد (غلط 21).
8. الـ specs اللي بتفشل تتصلح أو تتمسح (`ng test`).

### ب) الأخطاء تتحول لقصص (STAR)
الـ interviewer بيحب يسمع "لقيت مشكلة، وأثبتها، وحليتها، واتأكدت". مثال:
> "I noticed that two users could borrow the same book at the same time. I reproduced it by sending two parallel requests, and 4 out of 5 attempts created two active borrows. I fixed it with a pessimistic lock inside a transaction and added a test."

**مهم:** القصة دي تتقال بس بعد ما التصليح يتعمل فعلًا.

### ج) Pitch في دقيقة (بالإنجليزي)
> "Book Social Network is a full-stack web app for sharing books inside a community. Users register, activate their account with a 6-digit code sent by email, and log in with JWT. They can add books with a cover, choose which ones are shareable, borrow books from other members, return them, and the owner approves the return. Borrowers can rate and review books. The backend is Spring Boot 4 with Spring Security (stateless JWT), Spring Data JPA on PostgreSQL, asynchronous Thymeleaf emails and OpenAPI documentation. The frontend is Angular 21 with standalone, lazy-loaded components, a functional guard and interceptor, and a typed API client generated from the OpenAPI spec. Everything runs with Docker Compose, and a GitHub Actions pipeline compiles, tests and publishes the Docker image."

### د) الأسئلة العامة اللي بتيجي مع أي مشروع
- **"What was the hardest part?"**
  - الـ security flow: الـ JWT filter و CORS والـ 403 مقابل 401.
  - أو الـ zoneless change detection في Angular 21.
- **"What would you do differently?"**
  - كتابة tests من الأول.
  - الـ config يبقى بالـ environment variables.
  - استخدام signals من البداية.
  - الـ error handling بـ `ProblemDetail`.
  - استخدام Flyway.
- **"How would you scale it?"**
  - الـ JWT stateless، فممكن أكتر من instance ورا load balancer.
  - الصور على S3 أو MinIO مع CDN.
  - إضافة indexes على `book_id` و `user_id` و `token`، لأنها مش موجودة دلوقتي.
  - عمل cache للستة الكتب (Redis).
  - الإيميلات من خلال queue زي RabbitMQ أو Kafka بدل `@Async`.
- **"How do you know it works?"**
  - الـ unit tests بـ Mockito.
  - الـ integration tests بـ Testcontainers.
  - الـ Swagger للتجربة اليدوية.
  - الـ MailDev للإيميلات.

### هـ) مصدر المشروع
هيكل المشروع قريب جدًا من الكورس المشهور **Book Social Network (BSN)** بتاع Bouali Ali: نفس الأسماء، و `BusinessErrorCodes`، و `bsn-api`، و `mail-dev-bsn`، و `spring-demo`.
فيه interviewers كتير يعرفوه. لو المشروع مبني عليه، **مفيش أي مشكلة**، والأحسن يتقال ده بثقة، والتركيز يبقى على اللي اتضاف أو اتغير:
- الترقية لـ Spring Boot 4 و Angular 21 (zoneless و Vitest).
- الـ unit tests بتاعة Feedback و Email.
- (بعد التصليح) الأخطاء اللي اتلقت واتحلت.

المهم إن **كل سطر يبقى مفهوم وممكن يتشرح**، لأن أسئلة زي "ليه عملت كده؟" هي اللي بتفرق.

### و) الـ README محتاج
- صور (screenshots) أو GIF للتطبيق.
- خطوات تشغيل واضحة (`docker compose up`، والـ ports، ولينك MailDev).
- رسمة architecture بسيطة.
- ملف `.env.example`.
- جزء "Known limitations / Next steps".

### ز) رسمتين تبقى جاهزة تترسم على الورق
```
Auth:  Angular ──(email+password)──▶ /auth/authenticate ──▶ AuthenticationManager ──▶ DaoAuthenticationProvider
                                                                  │ (UserDetailsService + BCrypt)
       ◀──────────────── JWT (sub, fullName, authorities, exp) ◀──┘
       Angular (interceptor: Authorization: Bearer) ──▶ JwtAuthFilter ──▶ SecurityContext ──▶ Controller

Borrow: [available] ──borrow──▶ [borrowed: returned=false] ──return──▶ [returned=true] ──approve──▶ [available]
```

---

## 7. أرقام ومعلومات لازم تبقى محفوظة

| البند | القيمة |
|---|---|
| Spring Boot / Java | 4.0.6 / 17 (Hibernate 7.2) |
| Angular | 21.2 (zoneless، standalone، Vitest) |
| الداتابيز | PostgreSQL (الجداول: `_user`، `_user_roles`، `role`، `token`، `book`، `feedback`، `book_transaction_history`) |
| Context path | `/api/v1` |
| Ports | API: 8088 (prod) و 8078 (dev)، UI: 4200، MailDev UI: 1080 و SMTP: 1025، pgAdmin: 5050، Postgres: 5432 |
| JWT | HS256، مدته 2.4 ساعة (`8640000` ms)، فيه `sub` و `fullName` و `authorities` |
| كود التفعيل | 6 أرقام، `SecureRandom`، صالح 15 دقيقة |
| Pagination | الافتراضي في الباك `size=10`، والفرونت بيبعت `size=5` |
| Upload | `max-file-size` 50MB، بس الحد الفعلي 10MB (`max-request-size`) |
| Tests | الباك: 13 test كلهم ناجحين. الفرونت: 18 spec منهم 5 بيفشلوا |
| Endpoints | `auth`: register, authenticate, activate-account، `books`: CRUD, owner, borrowed, returned, shareable, archived, borrow, return, approve, cover، `feedbacks`: save, by book |
