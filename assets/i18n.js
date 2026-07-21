(() => {
    'use strict';

    const english = {
        'الذائقة السينمائية':'Cinema Taste',
        'اختيار اللغة':'Language selection',
        'التنقل الرئيسي':'Main navigation',
        '🏠 الرئيسية':'🏠 Home',
        '➕ إضافة عمل':'➕ Add Title',
        '🎯 مدى القابلية':'🎯 Likelihood',
        '🍿 قائمة المشاهدة':'🍿 Watchlist',
        '🎨 بصمة الذائقة':'🎨 Taste Profile',
        '🔎 البحث عن أعمال جديدة':'🔎 Discover New Titles',
        '📝 الجلسات':'📝 Sessions',
        'آخر تحديث —':'Last update —',
        'ليلة سينمائية على ذوقك':'A movie night shaped by your taste',
        'نموذج محلي يتعلّم من تقييماتك ويحوّلها إلى ترشيحات وقرارات مشاهدة واضحة.':'A local model that learns from your ratings and turns them into clear viewing choices.',
        'البيانات جاهزة':'Data ready',
        'ملخص المشروع':'Project summary',
        'أعمال أعجبتني':'Liked titles',
        'لم تعجبني':'Disliked titles',
        'قائمة المشاهدة':'Watchlist',
        'متوسط تقييمي':'My average rating',
        'تقييم 9 فأعلى':'Rated 9 or higher',
        'النوع الأقوى':'Strongest genre',
        'موجزات الجلسات':'Session briefs',
        '— جلسة':'— sessions',
        'ماذا تريد أن تفعل؟':'What would you like to do?',
        'البيانات متزامنة مع الملفات المحلية':'Data is synced with local files',
        'إضافة عمل':'Add Title',
        'ابحث عبر OMDb وأضف الفيلم أو المسلسل إلى قائمته.':'Search OMDb and add a movie or series to the right list.',
        'ابدأ الإضافة ←':'Start adding →',
        'ماذا أشاهد الليلة؟':'What should I watch tonight?',
        'أفضل مرشح من قائمة المشاهدة يظهر هنا.':'Your strongest watchlist candidate appears here.',
        'افتح القائمة ←':'Open watchlist →',
        'بصمة الذائقة':'Taste Profile',
        'الأنواع والمخرجون ومعادلة الإعجاب والنفور.':'Genres, directors, and the signals behind likes and dislikes.',
        'استكشف البصمة ←':'Explore profile →',
        'البحث عن أعمال جديدة':'Discover New Titles',
        'IMDb وRotten Tomatoes وJustWatch في مكان واحد.':'IMDb, Rotten Tomatoes, and JustWatch in one place.',
        'افتح البوابة ←':'Open discovery →',
        'سجل الجلسات':'Session Log',
        'استرجع ما تعلّمه النموذج من الجلسات السابقة.':'Review what the model learned in earlier sessions.',
        'راجع السجل ←':'Review log →',
        'فتح صفحة البحث عن أعمال جديدة':'Open Discover New Titles',
        '➕ إضافة فيلم/مسلسل جديد':'➕ Add a New Movie or Series',
        'ابحث عن العمل، راجع بياناته، ثم أضفه إلى القائمة المناسبة.':'Search for a title, review its metadata, then add it to the right list.',
        'OMDb — جارٍ التحقق':'OMDb — checking',
        'إعداد اتصال OMDb':'Set Up OMDb',
        'ألصق المفتاح المجاني مرة واحدة؛ سيُحفظ محليًا على جهازك.':'Paste the free key once; it is stored locally on your device.',
        'حفظ وتفعيل':'Save and activate',
        'الحصول على مفتاح مجاني ↗':'Get a free key ↗',
        'اسم الفيلم أو المسلسل':'Movie or series title',
        'سنة الإصدار — اختيارية':'Release year — optional',
        'أين تريد إضافته؟':'Where should it go?',
        'أعجبني':'Liked',
        'لم يعجبني':'Disliked',
        'أريد مشاهدته':'Want to watch',
        'تقييمي الشخصي':'My rating',
        'اختر التقييم':'Choose a rating',
        '🔎 ابحث في OMDb':'🔎 Search OMDb',
        '⚡ تجربة إضافة بلا مفتاح':'⚡ Instant no-key Add Title demo',
        'ابدأ بكتابة اسم العمل، ثم اختر النتيجة الصحيحة.':'Enter a title, then choose the correct result.',
        'بيانات العمل ستظهر هنا':'Title metadata will appear here',
        'اختر نتيجة الديمو':'Choose the demo result',
        'اضغط النتيجة لتشاهد جلب بيانات الحبكة والكتّاب والممثلين وبقية بيانات OMDb.':'Select the result to see the plot, writers, actors, and the rest of the OMDb metadata populate instantly.',
        'اكتملت تجربة الإضافة':'Add Title demo complete',
        'تمت محاكاة الإضافة بنجاح دون حفظ أو تغيير أي ملف خاص.':'The add flow was simulated successfully without saving or changing any private file.',
        'اختر نتيجة من محرك البحث لمراجعتها وتعديلها قبل الاعتماد.':'Choose a search result to review and edit before saving.',
        'الاسم':'Title',
        'الاسم الأصلي':'Original title',
        'النوع':'Type',
        'سنة الإصدار':'Release year',
        'تقييم IMDb':'IMDb rating',
        'عدد المصوّتين':'Vote count',
        'المدة بالدقائق':'Runtime in minutes',
        'تاريخ الإصدار':'Release date',
        'التصنيفات':'Genres',
        'المخرجون':'Directors',
        'الممثلون':'Actors',
        'الكتّاب':'Writers',
        'اللغة':'Language',
        'الحبكة':'Plot',
        'على ماذا استندت النسبة؟':'What is this score based on?',
        '🍿 إضافة إلى قائمة المشاهدة':'🍿 Add to watchlist',
        'رابط IMDb':'IMDb link',
        '🎯 قياس مدى القابلية':'🎯 Measure Likelihood',
        '✓ إضافة واعتماد':'✓ Add and save',
        '🍿 قائمة المشاهدة الذكية':'🍿 Smart Watchlist',
        'مرتبة وفق توافقها مع ذائقتك، لا وفق شهرتها العامة.':'Ranked by fit with your taste, not by global popularity.',
        'كل الترشيحات':'All candidates',
        'شاهد أولًا':'Watch first',
        'مرشح جيد':'Good candidate',
        'مخاطرة متوسطة':'Medium risk',
        'أجّله':'Postpone',
        'العمل':'Title',
        'النوع والمدة':'Genre and runtime',
        'سبب الترشيح':'Why it fits',
        'التوافق':'Fit',
        '🎨 بصمة الذائقة':'🎨 Taste Profile',
        'الخريطة التي تفسّر لماذا يجذبك عمل وينفّرك آخر.':'A map of why one title attracts you and another pushes you away.',
        'نموذج قابل للمعايرة':'Calibratable model',
        'معادلة الإعجاب':'Like formula',
        'الخطر والتصعيد أهم من القيمة النقدية المجردة.':'Risk and escalation matter more than abstract critical prestige.',
        'معادلة النفور':'Dislike formula',
        'الشهرة لا تعوّض غياب التوتر والارتباط المباشر.':'Popularity does not replace tension and direct engagement.',
        'الأنواع الأقوى':'Strongest genres',
        'داخل قائمة الإعجاب':'Within liked titles',
        'إشارات الحذر':'Caution signals',
        'متكررة في قائمة عدم الإعجاب':'Repeated among disliked titles',
        'عنقود 9/10':'9/10 cluster',
        'أهم الأعمال المرجعية':'Key reference titles',
        'إشارات المخرجين':'Director signals',
        'مستخرجة من سجلك':'Derived from your history',
        'مدى القابلية':'Likelihood',
        'نسبة توقعية لاحتمال إعجابك بالعمل قبل مشاهدته.':'An early estimate of how likely you are to enjoy a title before watching.',
        'احسب النسبة ←':'Calculate likelihood →',
        '🎯 مدى القابلية':'🎯 Likelihood',
        'نسبة توقعية أولية لاحتمال أن يعجبك العمل، مبنية على ذائقتك الفعلية.':'An initial estimate of how likely a title is to fit your real viewing taste.',
        'نسبة · ثقة · تفسير':'Score · confidence · explanation',
        'ابدأ باسم العمل':'Start with a title',
        'يستخدم OMDb لجلب البيانات، ثم يحللها محليًا.':'OMDb supplies metadata, then the app analyses it locally.',
        'تجربة فورية بلا مفتاح':'Instant no-key demo',
        'السنة — اختيارية':'Year — optional',
        'احسب النسبة':'Calculate likelihood',
        'اكتب اسم العمل، ثم اختر النتيجة الصحيحة لقراءة مدى قابليته لذائقتك.':'Enter a title, then choose the correct result to measure its fit with your taste.',
        'النسبة والتوقع سيظهران هنا':'The score and outlook will appear here',
        'النتيجة إيحاء أولي وليست حكمًا قاطعًا؛ سترافقها درجة ثقة وأسباب ومقارنات من سجلك.':'The result is an initial signal, not a final verdict; it includes confidence, reasons, and comparisons from your history.',
        'مدى القابلية المتوقع':'Expected likelihood',
        'نسبة توقعية':'Likelihood score',
        'أقرب أعمال أعجبتك':'Closest liked titles',
        'نسخ موجز GPT‑5.6 بالعربية':'Copy Arabic GPT‑5.6 brief',
        'Copy English brief':'Copy English brief',
        'بوابات موثوقة لاكتشاف الأعمال وقراءة التقييمات ومعرفة أماكن المشاهدة.':'Trusted sources for discovery, ratings, and where to watch.',
        '3 مصادر موثوقة':'3 trusted sources',
        '📝 سجل الجلسات والتعلّم':'📝 Session Log and Learning',
        'كل موجز جديد يصبح قاعدة إضافية داخل نموذج التوقع.':'Each new brief becomes another input to the prediction model.',
        'اختر جلسة لقراءة موجزها':'Choose a session to read its brief',
        'ستظهر هنا الخلاصة والقواعد الجديدة التي تعلّمها النموذج.':'The summary and newly learned rules will appear here.',
        'العمل موجود في قائمة أخرى':'This title is in another list',
        'إلغاء العملية':'Cancel',
        'نقل العمل':'Move title',
        'مفتاح OMDb':'OMDb key',
        'اكتب الاسم بالإنجليزية أو العربية':'Enter the title in English or Arabic',
        'مثال: 2026':'Example: 2026',
        'ابحث عن فيلم…':'Search for a movie…',
        'مواقع البحث عن الأفلام والمسلسلات وتحميلها':'Trusted sites for discovering movies and series and finding where to watch',
        'مواقع موثوقة لاكتشاف الأفلام والمسلسلات ومعرفة أماكن المشاهدة.':'Trusted sites for discovering movies and series and finding where to watch.',
        'مفتاح OMDb غير صالح.':'The OMDb key is invalid.',
        'أضف مفتاح OMDb أولًا لتفعيل البحث.':'Add an OMDb key first to enable search.',
        'تعذر الاتصال بـOMDb. تحقق من الإنترنت ثم أعد المحاولة.':'Could not connect to OMDb. Check the internet connection and try again.',
        'وصل رد غير صالح من OMDb.':'OMDb returned an invalid response.',
        'وصل رد غير متوقع من OMDb.':'OMDb returned an unexpected response.',
        'مفتاح OMDb غير صحيح أو غير مفعّل بعد.':'The OMDb key is incorrect or not active yet.',
        'لم يعثر OMDb على عمل مطابق.':'OMDb did not find a matching title.',
        'تم بلوغ حد طلبات OMDb لهذا اليوم.':'The OMDb daily request limit has been reached.',
        'اكتب حرفين على الأقل من اسم العمل.':'Enter at least two characters of the title.',
        'سنة الإصدار غير صحيحة.':'The release year is invalid.',
        'رقم IMDb غير صالح.':'The IMDb ID is invalid.',
        'بيانات العمل غير مكتملة.':'The title metadata is incomplete.',
        'اسم العمل مطلوب.':'The title is required.',
        'تقييم IMDb غير صحيح.':'The IMDb rating is invalid.',
        'اختر القائمة التي سيضاف إليها العمل.':'Choose the list where the title should be added.',
        'اختر تقييمك من 1 إلى 10.':'Choose a rating from 1 to 10.',
        'تعذر قراءة أعمدة ملف القائمة.':'Could not read the list file columns.',
        'طلب الإضافة غير مكتمل.':'The add request is incomplete.',
        'تعذر إنشاء النسخة الاحتياطية. أغلق الملف في Excel ثم أعد المحاولة.':'Could not create the backup. Close the file in Excel and try again.',
        'تعذر الكتابة في ملف القائمة. أغلق الملف في Excel ثم أعد المحاولة.':'Could not write to the list file. Close it in Excel and try again.',
        'طلب النقل غير مكتمل.':'The move request is incomplete.',
        'لم يعد العمل موجودًا في أي قائمة. أعد البحث ثم حاول مجددًا.':'The title is no longer in any list. Search again and retry.',
        'تغيرت بيانات القوائم أثناء العملية. أعد المحاولة.':'The list data changed during the operation. Try again.',
        'تعذر إنشاء نسخة أمان قبل النقل. أغلق ملفات CSV ثم أعد المحاولة.':'Could not create a safety copy before moving. Close the CSV files and try again.',
        'تعذر إكمال النقل، وتمت استعادة القائمتين كما كانتا.':'The move could not be completed, and both lists were restored.',
        'لا توجد عينة في قائمة المشاهدة.':'No demo title is available in the watchlist.',
        'المسار غير موجود.':'The requested path does not exist.'
    };

    let language = (() => {
        const query = new URLSearchParams(location.search).get('lang');
        if (query === 'ar' || query === 'en') return query;
        return localStorage.getItem('cinema-language') === 'en' ? 'en' : 'ar';
    })();

    const translate = (value) => english[value] || value;

    function translateTextNode(node) {
        if (node.parentElement?.closest('[data-i18n-skip],script,style')) return;
        if (node.__cinemaArabic === undefined) node.__cinemaArabic = node.nodeValue;
        const source = node.__cinemaArabic;
        const trimmed = source.trim();
        if (!trimmed) return;
        const translated = translate(trimmed);
        const start = source.match(/^\s*/)?.[0] || '';
        const end = source.match(/\s*$/)?.[0] || '';
        node.nodeValue = language === 'en' ? `${start}${translated}${end}` : source;
    }

    function translateAttributes(element) {
        for (const attribute of ['placeholder', 'title', 'aria-label']) {
            const key = `cinema${attribute.replace('-', '')}Ar`;
            if (element.dataset[key] === undefined && element.hasAttribute(attribute)) {
                element.dataset[key] = element.getAttribute(attribute);
            }
            const source = element.dataset[key];
            if (source !== undefined) element.setAttribute(attribute, language === 'en' ? translate(source) : source);
        }
    }

    function refresh(root = document) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) translateTextNode(node);
        root.querySelectorAll?.('[placeholder],[title],[aria-label]').forEach(translateAttributes);
        document.documentElement.lang = language;
        document.documentElement.dir = language === 'en' ? 'ltr' : 'rtl';
        document.body?.setAttribute('data-language', language);
        document.querySelectorAll('[data-language-option]').forEach(button => {
            const active = button.dataset.languageOption === language;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }

    function setLanguage(nextLanguage, notify = true) {
        if (nextLanguage !== 'ar' && nextLanguage !== 'en') return;
        language = nextLanguage;
        localStorage.setItem('cinema-language', language);
        refresh();
        if (notify) window.dispatchEvent(new CustomEvent('cinema-languagechange', {detail:{language}}));
    }

    function translateMessage(value) {
        if (language !== 'en' || !value) return value;
        const direct = translate(value);
        if (direct !== value) return direct;
        const listLabels = {'أعمال أعجبتني':'Liked titles','أعمال لم تعجبني':'Disliked titles','قائمة المشاهدة':'Watchlist'};
        return String(value)
            .replace(/«(أعمال أعجبتني|أعمال لم تعجبني|قائمة المشاهدة)»/g, (_, label) => `“${listLabels[label]}”`)
            .replace(/^تمت إضافة العمل إلى /, 'The title was added to ')
            .replace(/^تم نقل العمل من /, 'The title was moved from ')
            .replace(/ إلى /, ' to ')
            .replace(/^العمل موجود مسبقًا داخل /, 'The title already exists in ')
            .replace(/^العمل موجود بالفعل داخل /, 'The title already exists in ')
            .replace(/^آخر تحديث /, 'Last update ')
            .replace(/ جلسة$/, ' sessions')
            .replace(/ دقيقة/g, ' min')
            .replace(/توافق (\d+)%/g, '$1% fit')
            .replace(/^أحدث جلسة: /, 'Latest session: ')
            .replace(/^آخر تغيير: /, 'Latest change: ')
            .replace(/ إعجاب/g, ' liked')
            .replace(/ عدم إعجاب/g, ' disliked')
            .replace(/ قائمة مشاهدة/g, ' watchlist')
            .replace(/^نقل إلى /, 'Move to ');
    }

    window.CINEMA_I18N = {
        get language() { return language; },
        t(arabic, englishValue) { return language === 'en' ? (englishValue || translate(arabic)) : arabic; },
        translateMessage,
        refresh,
        setLanguage
    };

    document.querySelectorAll('[data-language-option]').forEach(button => {
        button.addEventListener('click', () => setLanguage(button.dataset.languageOption));
    });
    refresh();
})();
