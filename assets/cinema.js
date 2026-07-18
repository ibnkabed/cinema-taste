(() => {
    'use strict';

    const genreArabic = {
        Thriller:'إثارة', Action:'أكشن', Mystery:'غموض', 'Sci-Fi':'خيال علمي',
        Crime:'جريمة', Horror:'رعب', Drama:'دراما', Adventure:'مغامرة',
        Comedy:'كوميديا', Romance:'رومانسية', Biography:'سيرة', History:'تاريخ',
        War:'حرب', Fantasy:'فانتازيا', Western:'غرب أمريكي', Music:'موسيقى',
        Musical:'موسيقي', Animation:'رسوم متحركة'
    };
    const i18n = window.CINEMA_I18N;
    const isEnglish = () => i18n?.language === 'en';
    const t = (arabic, english) => i18n?.t(arabic, english) || arabic;
    const destinationLabels = {
        liked:{ar:'أعمال أعجبتني',en:'Liked titles'},
        disliked:{ar:'أعمال لم تعجبني',en:'Disliked titles'},
        watchlist:{ar:'قائمة المشاهدة',en:'Watchlist'}
    };
    const typeLabels = {movie:{ar:'فيلم',en:'Movie'},series:{ar:'مسلسل',en:'Series'},episode:{ar:'حلقة',en:'Episode'}};
    const destinationLabel = (key) => destinationLabels[key]?.[isEnglish() ? 'en' : 'ar'] || key;
    const typeLabel = (key) => typeLabels[key]?.[isEnglish() ? 'en' : 'ar'] || key || t('عمل', 'Title');
    let data = window.CINEMA_DATA || null;
    let toastTimer;
    let selectedWork = null;
    let pendingTransfer = null;
    let omdbStatusChecked = false;
    let discoveryPromptAr = '';
    let discoveryPromptEn = '';
    let lastDiscoveryAnalysis = null;

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
    const el = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };
    const localNumber = (value, digits = 0) => new Intl.NumberFormat(isEnglish() ? 'en-US' : 'ar-SA-u-nu-latn', {maximumFractionDigits:digits,minimumFractionDigits:digits}).format(Number(value || 0));
    const formatDate = (value) => {
        if (!value) return '—';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return new Intl.DateTimeFormat(isEnglish() ? 'en-US' : 'ar-SA-u-nu-latn', {year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(date);
    };
    const genreLabel = (name) => isEnglish() ? name : (genreArabic[name] || name);

    function showToast(message, type = '') {
        const toast = $('#toast');
        toast.textContent = i18n?.translateMessage(message) || message;
        toast.className = `toast show ${type}`.trim();
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.className = 'toast', 4200);
    }

    function switchView(name, pushHash = true) {
        $$('.view').forEach(view => view.classList.toggle('active', view.dataset.page === name));
        $$('.nav-link').forEach(link => link.classList.toggle('active', link.dataset.view === name));
        if (pushHash) history.replaceState(null, '', `#${name}`);
        if (name === 'add' || name === 'predict') checkOmdbStatus();
    }

    async function requestJson(path, options = {}) {
        if (location.protocol === 'file:') {
            throw new Error(t('شغّل الصفحة من «تشغيل الذائقة السينمائية» لتفعيل البحث والحفظ.', 'Run the project launcher to enable search and saving.'));
        }
        let response;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 20000);
        try {
            response = await fetch(path, {
                method:options.method || 'GET',
                headers:options.body ? {'Content-Type':'application/json'} : undefined,
                body:options.body ? JSON.stringify(options.body) : undefined,
                cache:'no-store',
                signal:controller.signal
            });
        } catch (err) {
            const timedOut = err && err.name === 'AbortError';
            const error = new Error(timedOut
                ? t(`انتهت مهلة الطلب (20 ثانية) دون رد من الخادم المحلي [${path}]. أعد تشغيل «تشغيل الذائقة السينمائية» ثم حاول مجددًا.`, `The local request timed out after 20 seconds [${path}]. Restart the Cinema Taste launcher and try again.`)
                : t(`تعذر الوصول للخادم المحلي [${path}]: ${err && err.message ? err.message : err}. أعد تشغيل «تشغيل الذائقة السينمائية» ثم حاول مجددًا.`, `Could not reach the local server [${path}]: ${err && err.message ? err.message : err}. Restart the Cinema Taste launcher and try again.`));
            error.code = timedOut ? 'local_server_timeout' : 'local_server_unavailable';
            throw error;
        } finally {
            clearTimeout(timer);
        }
        let payload = {};
        try { payload = await response.json(); } catch (_) { /* handled below */ }
        if (!response.ok || payload.ok === false) {
            const error = new Error(i18n?.translateMessage(payload.error) || payload.error || t('تعذر إكمال العملية.', 'The operation could not be completed.'));
            error.code = payload.code || 'request_failed';
            error.details = payload;
            throw error;
        }
        return payload;
    }

    function selectedDestination() {
        return $('input[name="add-destination"]:checked')?.value || 'liked';
    }

    function setButtonBusy(button, busy, busyText) {
        if (!button) return;
        if (busy) {
            button.dataset.originalText = button.textContent;
            button.textContent = busyText;
            button.disabled = true;
        } else {
            button.textContent = button.dataset.originalText || button.textContent;
            button.disabled = false;
        }
    }

    function syncDestinationUI() {
        const destination = selectedDestination();
        const ratingField = $('#add-rating-field');
        const rating = $('#add-rating');
        const liked = destination === 'liked';
        ratingField.hidden = !liked;
        rating.required = liked;
        if (!liked) rating.value = '';
        $('#add-destination-badge').textContent = destinationLabel(destination);
        $('#add-confirm-btn').textContent = `${t('✓ إضافة إلى', '✓ Add to')} ${destinationLabel(destination)}`;
    }

    async function checkOmdbStatus(force = false) {
        if (omdbStatusChecked && !force) return;
        const status = $('#omdb-status');
        const keyBox = $('#omdb-key-box');
        try {
            const result = await requestJson('/api/status');
            omdbStatusChecked = true;
            keyBox.hidden = result.omdbConfigured;
            status.textContent = result.omdbConfigured ? t('OMDb — متصل', 'OMDb — connected') : t('OMDb — يحتاج مفتاحًا', 'OMDb — key required');
            status.classList.toggle('ready', result.omdbConfigured);
        } catch (error) {
            status.textContent = t('OMDb — يتطلب المشغل المحلي', 'OMDb — local launcher required');
            status.classList.remove('ready');
            keyBox.hidden = true;
            $('#add-search-results').replaceChildren(el('p', 'add-error-text', error.message));
        }
    }

    async function saveOmdbKey() {
        const input = $('#omdb-key-input');
        const button = $('#omdb-key-save');
        const key = input.value.trim();
        if (!key) {
            showToast(t('ألصق مفتاح OMDb أولًا.', 'Paste an OMDb key first.'), 'error');
            input.focus();
            return;
        }
        setButtonBusy(button, true, t('جارٍ التحقق…', 'Checking…'));
        try {
            await requestJson('/api/omdb/key', {method:'POST', body:{key}});
            input.value = '';
            omdbStatusChecked = false;
            await checkOmdbStatus(true);
            showToast(t('تم حفظ مفتاح OMDb وتفعيل الاتصال.', 'The OMDb key was saved and the connection is active.'));
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    function renderAddResults(results) {
        const root = $('#add-search-results');
        root.replaceChildren();
        if (!results.length) {
            root.append(el('p', 'add-error-text', t('لم يظهر عمل مطابق. جرّب الاسم الأصلي أو احذف سنة الإصدار.', 'No matching title appeared. Try the original title or remove the release year.')));
            return;
        }
        results.forEach(item => {
            const button = el('button', 'add-result-card');
            button.type = 'button';
            button.dataset.imdbId = item.imdbId;
            const icon = el('span', 'add-result-icon', item.type === 'series' ? '📺' : item.type === 'episode' ? '▶️' : '🎬');
            const copy = el('span', 'add-result-copy');
            copy.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · ${typeLabel(item.type)} · ${item.imdbId}`));
            button.append(icon, copy, el('span', 'add-result-arrow', isEnglish() ? '→' : '←'));
            button.addEventListener('click', () => loadWorkDetails(item.imdbId, button));
            root.append(button);
        });
    }

    async function searchOmdb(event) {
        event.preventDefault();
        const title = $('#add-search-title').value.trim();
        const year = $('#add-search-year').value.trim();
        const button = $('.add-search-btn');
        if (title.length < 2) {
            showToast(t('اكتب حرفين على الأقل من اسم العمل.', 'Enter at least two characters of the title.'), 'error');
            $('#add-search-title').focus();
            return;
        }
        setButtonBusy(button, true, t('جارٍ البحث…', 'Searching…'));
        $('#add-search-results').replaceChildren(el('p', '', t('جارٍ البحث في OMDb…', 'Searching OMDb…')));
        try {
            const result = await requestJson('/api/omdb/search', {method:'POST', body:{title,year}});
            renderAddResults(result.results || []);
        } catch (error) {
            if (error.code === 'missing_key' || error.code === 'invalid_key') {
                $('#omdb-key-box').hidden = false;
                $('#omdb-status').textContent = t('OMDb — يحتاج مفتاحًا', 'OMDb — key required');
            }
            $('#add-search-results').replaceChildren(el('p', 'add-error-text', error.message));
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    function setDetailsMessage(icon, heading, message, success = false) {
        selectedWork = null;
        $('#add-details-form').hidden = true;
        const empty = $('#add-empty-state');
        empty.hidden = false;
        empty.classList.toggle('success', success);
        empty.replaceChildren(el('span', '', icon), el('h2', '', heading), el('p', '', message));
    }

    function fillDetailsForm(work) {
        selectedWork = work;
        const form = $('#add-details-form');
        Object.entries(work).forEach(([name, value]) => {
            const input = form.elements.namedItem(name);
            if (input) input.value = value || '';
        });
        $('#add-imdb-id').textContent = work.imdbId;
        $('#add-preview-heading').textContent = work.title || t('عمل جديد', 'New title');
        $('#add-empty-state').hidden = true;
        form.hidden = false;
        syncDestinationUI();
    }

    async function loadWorkDetails(imdbId, sourceButton) {
        $$('.add-result-card').forEach(card => card.classList.toggle('active', card === sourceButton));
        setDetailsMessage('⏳', t('جارٍ جلب البيانات', 'Loading metadata'), t('لحظات ونجهّز بطاقة العمل كاملة.', 'One moment while the complete title card is prepared.'));
        try {
            const result = await requestJson('/api/omdb/details', {method:'POST', body:{imdbId}});
            fillDetailsForm(result.work);
        } catch (error) {
            setDetailsMessage('⚠️', t('تعذر جلب البيانات', 'Could not load metadata'), error.message);
            showToast(error.message, 'error');
        }
    }

    function editableWorkFromForm() {
        const form = $('#add-details-form');
        const work = {imdbId:selectedWork?.imdbId || ''};
        ['title','originalTitle','titleType','year','imdbRating','numVotes','runtime','releaseDate','genres','directors','url'].forEach(name => {
            work[name] = form.elements.namedItem(name).value.trim();
        });
        return work;
    }

    function resetAddFlow(result, icon, heading) {
        hydrate(result.data);
        showToast(result.message);
        $('#add-search-form').reset();
        $('#add-search-results').replaceChildren(el('p', '', t('ابدأ بكتابة اسم عمل آخر، ثم اختر النتيجة الصحيحة.', 'Enter another title, then choose the correct result.')));
        setDetailsMessage(icon, heading, result.message, true);
        syncDestinationUI();
    }

    function closeTransferPrompt(cancelled = false) {
        pendingTransfer = null;
        $('#transfer-modal').hidden = true;
        if (cancelled) showToast(t('تم إلغاء العملية.', 'The operation was cancelled.'));
    }

    function openTransferPrompt(payload, details) {
        pendingTransfer = payload;
        const source = isEnglish() ? destinationLabel(details.existingDestination || '') : (details.existingDestinationLabel || 'القائمة الحالية');
        const target = isEnglish() ? destinationLabel(details.requestedDestination || payload.destination) : (details.requestedDestinationLabel || destinationLabel(payload.destination));
        $('#transfer-message').textContent = t(`العمل موجود مسبقًا داخل «${source}». هل تريد إلغاء العملية أم نقله إلى «${target}»؟`, `This title is already in “${source}”. Cancel or move it to “${target}”?`);
        $('#transfer-confirm').textContent = t(`نقل إلى ${target}`, `Move to ${target}`);
        $('#transfer-modal').hidden = false;
        $('#transfer-confirm').focus();
    }

    async function confirmTransfer() {
        if (!pendingTransfer) return;
        const payload = pendingTransfer;
        const button = $('#transfer-confirm');
        setButtonBusy(button, true, t('جارٍ النقل…', 'Moving…'));
        try {
            const result = await requestJson('/api/works/transfer', {method:'POST', body:payload});
            pendingTransfer = null;
            $('#transfer-modal').hidden = true;
            resetAddFlow(result, '↔', t('تم نقل العمل', 'Title moved'));
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    async function addSelectedWork(event) {
        event.preventDefault();
        if (!selectedWork) return;
        const destination = selectedDestination();
        const rating = $('#add-rating').value;
        if (destination === 'liked' && !rating) {
            showToast(t('اختر تقييمك قبل إضافة العمل إلى قائمة الإعجاب.', 'Choose your rating before adding the title to Liked.'), 'error');
            $('#add-rating').focus();
            return;
        }
        const button = $('#add-confirm-btn');
        const payload = {destination,rating,work:editableWorkFromForm()};
        setButtonBusy(button, true, t('جارٍ الحفظ…', 'Saving…'));
        try {
            const result = await requestJson('/api/works/add', {
                method:'POST',
                body:payload
            });
            resetAddFlow(result, '✅', t('تمت إضافة العمل', 'Title added'));
        } catch (error) {
            const details = error.details || {};
            if (error.code === 'duplicate' && details.existingDestination && details.existingDestination !== destination) {
                openTransferPrompt(payload, details);
            } else {
                showToast(error.message, 'error');
            }
        } finally {
            setButtonBusy(button, false);
        }
    }

    function renderDiscoveryResults(results) {
        const root = $('#discovery-results');
        root.replaceChildren();
        if (!results.length) {
            root.append(el('p', '', t('لم تظهر نتائج مطابقة. جرّب الاسم الأصلي أو غيّر سنة الإصدار.', 'No matching results appeared. Try the original title or change the release year.')));
            return;
        }
        results.forEach(item => {
            const button = el('button', 'discovery-result');
            button.type = 'button';
            if (item.poster) {
                const image = document.createElement('img');
                image.src = item.poster;
                image.alt = '';
                image.loading = 'lazy';
                image.addEventListener('error', () => image.replaceWith(el('span', 'poster-fallback', '🎬')));
                button.append(image);
            } else {
                button.append(el('span', 'poster-fallback', '🎬'));
            }
            const text = el('span');
            text.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · ${typeLabel(item.type)}`));
            button.append(text, el('span', '', t('تحليل ←', 'Analyse →')));
            button.addEventListener('click', () => analyzeDiscovery(item.imdbId, button));
            root.append(button);
        });
    }

    async function searchDiscovery(event) {
        event.preventDefault();
        const button = $('#discovery-search-button');
        const title = $('#discovery-search-title').value.trim();
        const year = $('#discovery-search-year').value.trim();
        if (title.length < 2) {
            showToast(t('اكتب حرفين على الأقل من اسم العمل.', 'Enter at least two characters of the title.'), 'error');
            return;
        }
        setButtonBusy(button, true, t('جارٍ البحث…', 'Searching…'));
        $('#discovery-results').replaceChildren(el('p', '', t('جارٍ البحث في OMDb…', 'Searching OMDb…')));
        try {
            const payload = await requestJson('/api/omdb/search', {method:'POST', body:{title, year}});
            renderDiscoveryResults(payload.results || []);
        } catch (error) {
            $('#discovery-results').replaceChildren(el('p', '', error.message));
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    function renderAnalysisReferences(target, rows) {
        const root = $(target);
        root.replaceChildren();
        if (!rows.length) {
            root.append(el('div', 'analysis-reference empty', t('لا توجد مقارنة قريبة كفاية.', 'No sufficiently close comparison is available.')));
            return;
        }
        rows.slice(0, 4).forEach(item => {
            const row = el('div', 'analysis-reference');
            row.append(
                el('b', '', item.title),
                el('span', '', `${item.similarity}%${item.rating ? ` · ${item.rating}/10` : ''}`)
            );
            root.append(row);
        });
    }

    function renderDiscoveryAnalysis(work, analysis, demo = false) {
        lastDiscoveryAnalysis = {work, analysis, demo};
        discoveryPromptAr = analysis.codexPromptAr || '';
        discoveryPromptEn = analysis.codexPromptEn || '';
        $('#discovery-empty').hidden = true;
        $('#discovery-analysis').hidden = false;
        $('#analysis-title').textContent = work.title || work.Title || '—';
        const genres = String(work.genres || work.Genres || '').split(',').map(item => item.trim()).filter(Boolean);
        const year = work.year || work.Year || '—';
        const runtime = work.runtime || work['Runtime (mins)'] || '—';
        $('#analysis-meta').textContent = `${year} · ${genres.slice(0, 3).map(genreLabel).join(isEnglish() ? ', ' : '، ') || t('تصنيف غير متاح', 'Genre unavailable')} · ${runtime} ${t('دقيقة', 'min')}${demo ? t(' · عينة محلية', ' · local sample') : ''}`;
        $('#analysis-score').textContent = `${analysis.score}%`;
        $('#analysis-verdict').textContent = isEnglish() ? analysis.verdictEn : analysis.verdictAr;
        $('#analysis-confidence').textContent = `${t('درجة الثقة', 'Confidence')} ${analysis.confidence}%`;
        $('#analysis-disclaimer').textContent = isEnglish() ? analysis.disclaimerEn : analysis.disclaimerAr;

        const reasons = $('#analysis-reasons');
        reasons.replaceChildren();
        (isEnglish() ? (analysis.reasonsEn || []) : (analysis.reasonsAr || [])).forEach(reason => reasons.append(el('span', '', reason)));
        renderAnalysisReferences('#analysis-liked', analysis.similarLiked || []);
        renderAnalysisReferences('#analysis-disliked', analysis.similarDisliked || []);
        $('#analysis-summary-en').textContent = `${analysis.verdictEn}. Initial reading ${analysis.score}/100 with ${analysis.confidence}/100 confidence. ${(analysis.reasonsEn || []).join(' ')} ${analysis.disclaimerEn}`;
    }

    async function analyzeDiscovery(imdbId, sourceButton) {
        setButtonBusy(sourceButton, true, t('جارٍ التحليل…', 'Analysing…'));
        try {
            const payload = await requestJson('/api/taste/analyze', {method:'POST', body:{imdbId}});
            renderDiscoveryAnalysis(payload.work, payload.analysis, false);
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(sourceButton, false);
        }
    }

    async function analyzeSelectedWork() {
        if (!selectedWork) {
            showToast(t('اختر عملًا من نتائج OMDb أولًا.', 'Choose a title from the OMDb results first.'), 'error');
            return;
        }
        const button = $('#predict-from-add-btn');
        setButtonBusy(button, true, t('جارٍ القياس…', 'Measuring…'));
        try {
            const payload = await requestJson('/api/taste/analyze', {method:'POST', body:{work:editableWorkFromForm()}});
            switchView('predict');
            renderDiscoveryAnalysis(payload.work, payload.analysis, false);
            showToast(t('تم إرسال بيانات OMDb إلى صفحة مدى القابلية.', 'OMDb metadata was sent to the Likelihood page.'));
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    async function loadDiscoveryDemo() {
        const button = $('#discovery-demo-button');
        setButtonBusy(button, true, t('جارٍ التحليل…', 'Analysing…'));
        try {
            const payload = await requestJson('/api/taste/demo');
            renderDiscoveryAnalysis(payload.work, payload.analysis, true);
            showToast(t('تم تحميل عينة محلية دون استخدام OMDb.', 'A local sample was loaded without using OMDb.'));
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    async function copyDiscoveryPrompt(language) {
        const value = language === 'en' ? discoveryPromptEn : discoveryPromptAr;
        if (!value) {
            showToast(t('حلّل عملًا أولًا لإنشاء الموجز.', 'Analyse a title first to create the brief.'), 'error');
            return;
        }
        try {
            await navigator.clipboard.writeText(value);
            showToast(language === 'en' ? 'English GPT-5.6 brief copied.' : 'تم نسخ موجز GPT‑5.6 بالعربية.');
        } catch (_) {
            const area = document.createElement('textarea');
            area.value = value;
            area.style.position = 'fixed';
            area.style.opacity = '0';
            document.body.append(area);
            area.select();
            document.execCommand('copy');
            area.remove();
            showToast(language === 'en' ? 'English GPT-5.6 brief copied.' : 'تم نسخ موجز GPT‑5.6 بالعربية.');
        }
    }

    const sessionEnglish = [
        {
            match:'الجلسة الرابعة',
            title:'Session 4 — Visual identity and Add Work repair — 14 July 2026',
            excerpt:'The interface adopted its dark navy and cinematic gold identity, and a display-layer bug in the OMDb Add Work flow was diagnosed and fixed.',
            text:'This session records the approved dark navy and cinematic gold visual identity, the compact no-scroll layout review, and the repair of the Add Work loading overlay. It also documents a successful real OMDb add test and the rule that visual browser validation must accompany programmatic checks.'
        },
        {
            match:'الجلسة الخامسة',
            title:'Session 5 — Moving titles between lists and project cleanup — 14 July 2026',
            excerpt:'Duplicate handling became a deliberate move flow between Liked, Disliked, and Watchlist while preserving CSV safety.',
            text:'This session documents the safe transfer workflow. A title already in another list can be cancelled or moved explicitly; moving into Liked requires a personal rating. The server creates backups, prevents duplicates, and restores both files if a transfer fails.'
        },
        {
            match:'الجلسة الثالثة',
            title:'Session 3 — Cinema Taste portal development — 14 July 2026',
            excerpt:'The local portal, data refresh flow, watchlist ranking, and OMDb-backed Add Work experience were consolidated.',
            text:'This session documents the development of the local Cinema Taste portal, its data refresh workflow, watchlist scoring, taste-profile sections, OMDb connection, and the project rules that keep viewing records local.'
        },
        {
            match:'Obsession',
            title:'Session — Obsession and Get Out comparison — 2 July 2026',
            excerpt:'A live viewing discussion tested the model against Obsession and its strong structural resemblance to Get Out.',
            text:'This session records a live calibration example. Obsession was compared with Get Out through psychological tension, gradual escalation, social unease, and a high-concept premise. The final 9/10 rating strengthened that reference cluster in the personal model.'
        },
        {
            match:'تحليل الذائقة السينمائية',
            title:'Cinema Taste analysis session — 1 July 2026',
            excerpt:'The first personal taste model identified positive genres, caution patterns, director signals, and the need for explainable recommendations.',
            text:'This session establishes the first taste model from liked and disliked viewing history. Strong signals include thriller, action, mystery, crime, and high-concept science fiction. Caution signals include slow awards-led drama, conventional biography, and low direct tension. The model must explain every recommendation with personal evidence rather than popularity alone.'
        }
    ];

    function sessionDisplay(session) {
        if (!isEnglish()) return session;
        return sessionEnglish.find(item => session.title.includes(item.match)) || {
            title:'Session note',
            excerpt:'This session note is preserved in its original Arabic source.',
            text:'The original session note is preserved in Arabic in the local project data.'
        };
    }

    function watchReason(reason) {
        if (!isEnglish()) return reason;
        return reason
            .replace(/^تركيبة مناسبة: /, 'Compatible genre mix: ')
            .replace(/^إشارة مخرج إيجابية: /, 'Positive director signal: ')
            .replace(/^مدة مناسبة لإيقاعك$/, 'Runtime fits your pacing preference')
            .replace(/^عامل مخاطرة: /, 'Risk signal: ')
            .replace(/^توافق متوسط يحتاج معايرة بعد المشاهدة$/, 'Moderate fit; calibrate after watching')
            .replaceAll('،', ',');
    }

    function watchVerdict(item) {
        if (!isEnglish()) return item.verdict;
        return {high:'Watch first', good:'Good candidate', medium:'Medium risk', low:'Postpone'}[item.band] || item.verdict;
    }

    function renderSummary() {
        const summary = data.summary;
        $('#stat-liked').textContent = localNumber(summary.liked);
        $('#stat-disliked').textContent = localNumber(summary.disliked);
        $('#stat-watchlist').textContent = localNumber(summary.watchlist);
        $('#stat-average').textContent = localNumber(summary.averageRating, 2);
        $('#stat-high').textContent = localNumber(summary.highRated);
        $('#stat-genre').textContent = genreLabel(summary.topGenre);
        $('#stat-sessions').textContent = localNumber(summary.sessions);
        $('#header-update').textContent = `${t('آخر تحديث', 'Last update')} ${formatDate(data.meta.generatedAt)}`;
        $('#session-count-pill').textContent = `${localNumber(summary.sessions)} ${t('جلسة', 'sessions')}`;

        const pick = data.watchlist[0];
        if (pick) $('#home-top-pick').textContent = `${pick.title} — ${isEnglish() ? `${pick.score}% fit` : `توافق ${pick.score}%`}`;
        const session = data.sessions[0];
        if (session) $('#home-latest-session').textContent = `${t('أحدث جلسة:', 'Latest session:')} ${sessionDisplay(session).title}`;

        const changes = data.meta.changes || {};
        const deltas = changes.deltas || {};
        const parts = [];
        if (deltas.liked) parts.push(`${deltas.liked > 0 ? '+' : ''}${deltas.liked} ${t('إعجاب', 'liked')}`);
        if (deltas.disliked) parts.push(`${deltas.disliked > 0 ? '+' : ''}${deltas.disliked} ${t('عدم إعجاب', 'disliked')}`);
        if (deltas.watchlist) parts.push(`${deltas.watchlist > 0 ? '+' : ''}${deltas.watchlist} ${t('قائمة مشاهدة', 'watchlist')}`);
        if (deltas.sessions) parts.push(`${deltas.sessions > 0 ? '+' : ''}${deltas.sessions} ${t('جلسة', 'sessions')}`);
        $('#change-summary').textContent = parts.length ? `${t('آخر تغيير:', 'Latest change:')} ${parts.join(' · ')}` : t('البيانات متزامنة مع الملفات المحلية', 'Data is synced with local files');
    }

    function renderBars(target, rows) {
        const root = $(target);
        root.replaceChildren();
        const max = Math.max(...rows.slice(0, 7).map(item => item.count), 1);
        rows.slice(0, 7).forEach(item => {
            const row = el('div', 'bar-row');
            row.append(el('span', '', genreLabel(item.name)));
            const track = el('div', 'bar-track');
            const fill = el('div', 'bar-fill');
            fill.style.width = `${Math.max(7, item.count * 100 / max)}%`;
            track.append(fill);
            row.append(track, el('b', '', localNumber(item.count)));
            root.append(row);
        });
    }

    function renderTaste() {
        $('#taste-formula').textContent = isEnglish() ? 'Tight plot + clear danger + pressured character + earned escalation' : data.taste.formula;
        $('#taste-risk-formula').textContent = isEnglish() ? 'Slow pacing + cold or awards-led treatment + weak direct tension' : data.taste.riskFormula;
        renderBars('#liked-genre-bars', data.taste.likedGenres || []);
        renderBars('#disliked-genre-bars', data.taste.dislikedGenres || []);

        const references = $('#reference-chips');
        references.replaceChildren();
        (data.references.highRated || []).slice(0, 14).forEach(work => {
            references.append(el('span', 'chip', `${work.title} · ${work.rating}/10`));
        });
        const directors = $('#director-chips');
        directors.replaceChildren();
        (data.taste.positiveDirectors || []).slice(0, 12).forEach(item => {
            directors.append(el('span', 'chip', `${item.name} +${item.signal}`));
        });
    }

    function renderWatchlist() {
        const root = $('#watchlist-rows');
        const query = $('#watch-search').value.trim().toLowerCase();
        const band = $('#watch-filter').value;
        const rows = (data.watchlist || []).filter(item => {
            const matchesBand = band === 'all' || item.band === band;
            const haystack = `${item.title} ${item.originalTitle} ${item.directors.join(' ')} ${item.genres.join(' ')}`.toLowerCase();
            return matchesBand && (!query || haystack.includes(query));
        });
        root.replaceChildren();
        if (!rows.length) {
            root.append(el('div', 'empty-row', t('لا توجد أعمال مطابقة لهذا البحث.', 'No titles match this search.')));
            return;
        }
        rows.forEach(item => {
            const row = el('article', 'watch-row');
            const title = el('div', 'watch-title');
            title.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · IMDb ${item.imdb || '—'}`));
            const meta = el('div', 'watch-meta');
            meta.append(el('span', '', item.genres.slice(0, 3).map(genreLabel).join(isEnglish() ? ', ' : '، ') || '—'), el('small', '', `${item.runtime || '—'} ${t('دقيقة', 'min')}`));
            const reason = el('div', 'watch-reason', item.reasons.map(watchReason).join(' · '));
            const score = el('div', 'watch-score');
            score.append(el('span', `score-tag ${item.band}`, watchVerdict(item)), el('b', '', `${item.score}%`));
            row.append(title, meta, reason, score);
            root.append(row);
        });
    }

    function renderSession(index) {
        const session = data.sessions[index];
        if (!session) return;
        const display = sessionDisplay(session);
        $$('.session-card').forEach((card, cardIndex) => card.classList.toggle('active', cardIndex === index));
        const reader = $('#session-reader');
        reader.replaceChildren();
        reader.append(el('span', 'session-date', formatDate(session.date)), el('h2', '', display.title), el('div', 'session-text', display.text || display.excerpt));
    }

    function renderSessions() {
        const root = $('#session-list');
        root.replaceChildren();
        (data.sessions || []).forEach((session, index) => {
            const display = sessionDisplay(session);
            const card = el('button', 'session-card');
            card.type = 'button';
            card.append(el('b', '', display.title), el('p', '', display.excerpt), el('small', '', formatDate(session.date)));
            card.addEventListener('click', () => renderSession(index));
            root.append(card);
        });
        if (data.sessions.length) renderSession(0);
    }

    function hydrate(nextData) {
        data = nextData;
        window.CINEMA_DATA = nextData;
        renderSummary();
        renderTaste();
        renderWatchlist();
        renderSessions();
    }

    function bindEvents() {
        $$('.nav-link').forEach(link => link.addEventListener('click', () => switchView(link.dataset.view)));
        $$('[data-open-view]').forEach(link => link.addEventListener('click', () => switchView(link.dataset.openView)));
        $('#watch-search').addEventListener('input', renderWatchlist);
        $('#watch-filter').addEventListener('change', renderWatchlist);
        $('#add-search-form').addEventListener('submit', searchOmdb);
        $('#discovery-search-form').addEventListener('submit', searchDiscovery);
        $('#discovery-demo-button').addEventListener('click', loadDiscoveryDemo);
        $('#predict-from-add-btn').addEventListener('click', analyzeSelectedWork);
        $('#copy-prompt-ar').addEventListener('click', () => copyDiscoveryPrompt('ar'));
        $('#copy-prompt-en').addEventListener('click', () => copyDiscoveryPrompt('en'));
        $('#add-details-form').addEventListener('submit', addSelectedWork);
        $('#omdb-key-save').addEventListener('click', saveOmdbKey);
        $('#transfer-cancel').addEventListener('click', () => closeTransferPrompt(true));
        $('#transfer-confirm').addEventListener('click', confirmTransfer);
        $$('input[name="add-destination"]').forEach(input => input.addEventListener('change', syncDestinationUI));
        window.addEventListener('hashchange', () => {
            const name = location.hash.slice(1);
            if ($(`[data-page="${name}"]`)) switchView(name, false);
        });
        window.addEventListener('cinema-languagechange', () => {
            syncDestinationUI();
            if (data) hydrate(data);
            if (lastDiscoveryAnalysis) {
                renderDiscoveryAnalysis(lastDiscoveryAnalysis.work, lastDiscoveryAnalysis.analysis, lastDiscoveryAnalysis.demo);
            }
            omdbStatusChecked = false;
            const activePage = $('.view.active')?.dataset.page;
            if (activePage === 'add' || activePage === 'predict') checkOmdbStatus(true);
        });
    }

    bindEvents();
    syncDestinationUI();
    if (data) {
        hydrate(data);
        const initialView = location.hash.slice(1);
        if (initialView && $(`[data-page="${initialView}"]`)) switchView(initialView, false);
    } else {
        showToast(t('لم يتم العثور على ملف البيانات. شغّل أداة التحديث أولًا.', 'The data file was not found. Run the update tool first.'), 'error');
        $('#data-health span').textContent = t('البيانات غير جاهزة', 'Data not ready');
    }
})();
