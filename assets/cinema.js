(() => {
    'use strict';

    const genreArabic = {
        Thriller:'إثارة', Action:'أكشن', Mystery:'غموض', 'Sci-Fi':'خيال علمي',
        Crime:'جريمة', Horror:'رعب', Drama:'دراما', Adventure:'مغامرة',
        Comedy:'كوميديا', Romance:'رومانسية', Biography:'سيرة', History:'تاريخ',
        War:'حرب', Fantasy:'فانتازيا', Western:'غرب أمريكي', Music:'موسيقى',
        Musical:'موسيقي', Animation:'رسوم متحركة'
    };
    const destinationLabels = {
        liked:'أعمال أعجبتني',
        disliked:'أعمال لم تعجبني',
        watchlist:'قائمة المشاهدة'
    };
    const typeLabels = {movie:'فيلم',series:'مسلسل',episode:'حلقة'};
    let data = window.CINEMA_DATA || null;
    let toastTimer;
    let selectedWork = null;
    let pendingTransfer = null;
    let omdbStatusChecked = false;
    let discoveryPromptAr = '';
    let discoveryPromptEn = '';

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
    const el = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };
    const localNumber = (value, digits = 0) => new Intl.NumberFormat('ar-SA-u-nu-latn', {maximumFractionDigits:digits,minimumFractionDigits:digits}).format(Number(value || 0));
    const formatDate = (value) => {
        if (!value) return '—';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return new Intl.DateTimeFormat('ar-SA-u-nu-latn', {year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(date);
    };
    const genreLabel = (name) => genreArabic[name] || name;

    function showToast(message, type = '') {
        const toast = $('#toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`.trim();
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.className = 'toast', 4200);
    }

    function switchView(name, pushHash = true) {
        $$('.view').forEach(view => view.classList.toggle('active', view.dataset.page === name));
        $$('.nav-link').forEach(link => link.classList.toggle('active', link.dataset.view === name));
        if (pushHash) history.replaceState(null, '', `#${name}`);
        if (name === 'add' || name === 'search') checkOmdbStatus();
    }

    async function requestJson(path, options = {}) {
        if (location.protocol === 'file:') {
            throw new Error('شغّل الصفحة من «تشغيل الذائقة السينمائية» لتفعيل البحث والحفظ.');
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
                ? `انتهت مهلة الطلب (20 ثانية) دون رد من الخادم المحلي [${path}]. أعد تشغيل «تشغيل الذائقة السينمائية» ثم حاول مجددًا.`
                : `تعذر الوصول للخادم المحلي [${path}]: ${err && err.message ? err.message : err}. أعد تشغيل «تشغيل الذائقة السينمائية» ثم حاول مجددًا.`);
            error.code = timedOut ? 'local_server_timeout' : 'local_server_unavailable';
            throw error;
        } finally {
            clearTimeout(timer);
        }
        let payload = {};
        try { payload = await response.json(); } catch (_) { /* handled below */ }
        if (!response.ok || payload.ok === false) {
            const error = new Error(payload.error || 'تعذر إكمال العملية.');
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
        $('#add-destination-badge').textContent = destinationLabels[destination];
        $('#add-confirm-btn').textContent = `✓ إضافة إلى ${destinationLabels[destination]}`;
    }

    async function checkOmdbStatus(force = false) {
        if (omdbStatusChecked && !force) return;
        const status = $('#omdb-status');
        const keyBox = $('#omdb-key-box');
        try {
            const result = await requestJson('/api/status');
            omdbStatusChecked = true;
            keyBox.hidden = result.omdbConfigured;
            status.textContent = result.omdbConfigured ? 'OMDb — متصل' : 'OMDb — يحتاج مفتاحًا';
            status.classList.toggle('ready', result.omdbConfigured);
        } catch (error) {
            status.textContent = 'OMDb — يتطلب المشغل المحلي';
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
            showToast('ألصق مفتاح OMDb أولًا.', 'error');
            input.focus();
            return;
        }
        setButtonBusy(button, true, 'جارٍ التحقق…');
        try {
            await requestJson('/api/omdb/key', {method:'POST', body:{key}});
            input.value = '';
            omdbStatusChecked = false;
            await checkOmdbStatus(true);
            showToast('تم حفظ مفتاح OMDb وتفعيل الاتصال.');
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
            root.append(el('p', 'add-error-text', 'لم يظهر عمل مطابق. جرّب الاسم الأصلي أو احذف سنة الإصدار.'));
            return;
        }
        results.forEach(item => {
            const button = el('button', 'add-result-card');
            button.type = 'button';
            button.dataset.imdbId = item.imdbId;
            const icon = el('span', 'add-result-icon', item.type === 'series' ? '📺' : item.type === 'episode' ? '▶️' : '🎬');
            const copy = el('span', 'add-result-copy');
            copy.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · ${typeLabels[item.type] || item.type || 'عمل'} · ${item.imdbId}`));
            button.append(icon, copy, el('span', 'add-result-arrow', '←'));
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
            showToast('اكتب حرفين على الأقل من اسم العمل.', 'error');
            $('#add-search-title').focus();
            return;
        }
        setButtonBusy(button, true, 'جارٍ البحث…');
        $('#add-search-results').replaceChildren(el('p', '', 'جارٍ البحث في OMDb…'));
        try {
            const result = await requestJson('/api/omdb/search', {method:'POST', body:{title,year}});
            renderAddResults(result.results || []);
        } catch (error) {
            if (error.code === 'missing_key' || error.code === 'invalid_key') {
                $('#omdb-key-box').hidden = false;
                $('#omdb-status').textContent = 'OMDb — يحتاج مفتاحًا';
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
        $('#add-preview-heading').textContent = work.title || 'عمل جديد';
        $('#add-empty-state').hidden = true;
        form.hidden = false;
        syncDestinationUI();
    }

    async function loadWorkDetails(imdbId, sourceButton) {
        $$('.add-result-card').forEach(card => card.classList.toggle('active', card === sourceButton));
        setDetailsMessage('⏳', 'جارٍ جلب البيانات', 'لحظات ونجهّز بطاقة العمل كاملة.');
        try {
            const result = await requestJson('/api/omdb/details', {method:'POST', body:{imdbId}});
            fillDetailsForm(result.work);
        } catch (error) {
            setDetailsMessage('⚠️', 'تعذر جلب البيانات', error.message);
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
        $('#add-search-results').replaceChildren(el('p', '', 'ابدأ بكتابة اسم عمل آخر، ثم اختر النتيجة الصحيحة.'));
        setDetailsMessage(icon, heading, result.message, true);
        syncDestinationUI();
    }

    function closeTransferPrompt(cancelled = false) {
        pendingTransfer = null;
        $('#transfer-modal').hidden = true;
        if (cancelled) showToast('تم إلغاء العملية.');
    }

    function openTransferPrompt(payload, details) {
        pendingTransfer = payload;
        const source = details.existingDestinationLabel || 'القائمة الحالية';
        const target = details.requestedDestinationLabel || destinationLabels[payload.destination];
        $('#transfer-message').textContent = `العمل موجود مسبقًا داخل «${source}». هل تريد إلغاء العملية أم نقله إلى «${target}»؟`;
        $('#transfer-confirm').textContent = `نقل إلى ${target}`;
        $('#transfer-modal').hidden = false;
        $('#transfer-confirm').focus();
    }

    async function confirmTransfer() {
        if (!pendingTransfer) return;
        const payload = pendingTransfer;
        const button = $('#transfer-confirm');
        setButtonBusy(button, true, 'جارٍ النقل…');
        try {
            const result = await requestJson('/api/works/transfer', {method:'POST', body:payload});
            pendingTransfer = null;
            $('#transfer-modal').hidden = true;
            resetAddFlow(result, '↔', 'تم نقل العمل');
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
            showToast('اختر تقييمك قبل إضافة العمل إلى قائمة الإعجاب.', 'error');
            $('#add-rating').focus();
            return;
        }
        const button = $('#add-confirm-btn');
        const payload = {destination,rating,work:editableWorkFromForm()};
        setButtonBusy(button, true, 'جارٍ الحفظ…');
        try {
            const result = await requestJson('/api/works/add', {
                method:'POST',
                body:payload
            });
            resetAddFlow(result, '✅', 'تمت إضافة العمل');
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
            root.append(el('p', '', 'لم تظهر نتائج مطابقة. جرّب الاسم الأصلي أو غيّر سنة الإصدار.'));
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
            text.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · ${typeLabels[item.type] || item.type || 'عمل'}`));
            button.append(text, el('span', '', 'تحليل ←'));
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
            showToast('اكتب حرفين على الأقل من اسم العمل.', 'error');
            return;
        }
        setButtonBusy(button, true, 'جارٍ البحث…');
        $('#discovery-results').replaceChildren(el('p', '', 'جارٍ البحث في OMDb…'));
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
            root.append(el('div', 'analysis-reference empty', 'لا توجد مقارنة قريبة كفاية.'));
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
        discoveryPromptAr = analysis.codexPromptAr || '';
        discoveryPromptEn = analysis.codexPromptEn || '';
        $('#discovery-empty').hidden = true;
        $('#discovery-analysis').hidden = false;
        $('#analysis-title').textContent = work.title || work.Title || '—';
        const genres = String(work.genres || work.Genres || '').split(',').map(item => item.trim()).filter(Boolean);
        const year = work.year || work.Year || '—';
        const runtime = work.runtime || work['Runtime (mins)'] || '—';
        $('#analysis-meta').textContent = `${year} · ${genres.slice(0, 3).map(genreLabel).join('، ') || 'تصنيف غير متاح'} · ${runtime} دقيقة${demo ? ' · عينة محلية' : ''}`;
        $('#analysis-score').textContent = `${analysis.score}%`;
        $('#analysis-verdict').textContent = analysis.verdictAr;
        $('#analysis-confidence').textContent = `درجة الثقة ${analysis.confidence}%`;
        $('#analysis-disclaimer').textContent = analysis.disclaimerAr;

        const reasons = $('#analysis-reasons');
        reasons.replaceChildren();
        (analysis.reasonsAr || []).forEach(reason => reasons.append(el('span', '', reason)));
        renderAnalysisReferences('#analysis-liked', analysis.similarLiked || []);
        renderAnalysisReferences('#analysis-disliked', analysis.similarDisliked || []);
        $('#analysis-summary-en').textContent = `${analysis.verdictEn}. Initial reading ${analysis.score}/100 with ${analysis.confidence}/100 confidence. ${(analysis.reasonsEn || []).join(' ')} ${analysis.disclaimerEn}`;
    }

    async function analyzeDiscovery(imdbId, sourceButton) {
        setButtonBusy(sourceButton, true, 'جارٍ التحليل…');
        try {
            const payload = await requestJson('/api/taste/analyze', {method:'POST', body:{imdbId}});
            renderDiscoveryAnalysis(payload.work, payload.analysis, false);
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(sourceButton, false);
        }
    }

    async function loadDiscoveryDemo() {
        const button = $('#discovery-demo-button');
        setButtonBusy(button, true, 'جارٍ التحليل…');
        try {
            const payload = await requestJson('/api/taste/demo');
            renderDiscoveryAnalysis(payload.work, payload.analysis, true);
            showToast('تم تحميل عينة محلية دون استخدام OMDb.');
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            setButtonBusy(button, false);
        }
    }

    async function copyDiscoveryPrompt(language) {
        const value = language === 'en' ? discoveryPromptEn : discoveryPromptAr;
        if (!value) {
            showToast('حلّل عملًا أولًا لإنشاء الموجز.', 'error');
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

    function renderSummary() {
        const summary = data.summary;
        $('#stat-liked').textContent = localNumber(summary.liked);
        $('#stat-disliked').textContent = localNumber(summary.disliked);
        $('#stat-watchlist').textContent = localNumber(summary.watchlist);
        $('#stat-average').textContent = localNumber(summary.averageRating, 2);
        $('#stat-high').textContent = localNumber(summary.highRated);
        $('#stat-genre').textContent = genreLabel(summary.topGenre);
        $('#stat-sessions').textContent = localNumber(summary.sessions);
        $('#header-update').textContent = `آخر تحديث ${formatDate(data.meta.generatedAt)}`;
        $('#session-count-pill').textContent = `${localNumber(summary.sessions)} جلسة`;

        const pick = data.watchlist[0];
        if (pick) $('#home-top-pick').textContent = `${pick.title} — توافق ${pick.score}%`;
        const session = data.sessions[0];
        if (session) $('#home-latest-session').textContent = `أحدث جلسة: ${session.title}`;

        const changes = data.meta.changes || {};
        const deltas = changes.deltas || {};
        const parts = [];
        if (deltas.liked) parts.push(`${deltas.liked > 0 ? '+' : ''}${deltas.liked} إعجاب`);
        if (deltas.disliked) parts.push(`${deltas.disliked > 0 ? '+' : ''}${deltas.disliked} عدم إعجاب`);
        if (deltas.watchlist) parts.push(`${deltas.watchlist > 0 ? '+' : ''}${deltas.watchlist} قائمة مشاهدة`);
        if (deltas.sessions) parts.push(`${deltas.sessions > 0 ? '+' : ''}${deltas.sessions} جلسة`);
        $('#change-summary').textContent = parts.length ? `آخر تغيير: ${parts.join(' · ')}` : 'البيانات متزامنة مع الملفات المحلية';
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
        $('#taste-formula').textContent = data.taste.formula;
        $('#taste-risk-formula').textContent = data.taste.riskFormula;
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
            root.append(el('div', 'empty-row', 'لا توجد أعمال مطابقة لهذا البحث.'));
            return;
        }
        rows.forEach(item => {
            const row = el('article', 'watch-row');
            const title = el('div', 'watch-title');
            title.append(el('b', '', item.title), el('small', '', `${item.year || '—'} · IMDb ${item.imdb || '—'}`));
            const meta = el('div', 'watch-meta');
            meta.append(el('span', '', item.genres.slice(0, 3).map(genreLabel).join('، ') || '—'), el('small', '', `${item.runtime || '—'} دقيقة`));
            const reason = el('div', 'watch-reason', item.reasons.join(' · '));
            const score = el('div', 'watch-score');
            score.append(el('span', `score-tag ${item.band}`, item.verdict), el('b', '', `${item.score}%`));
            row.append(title, meta, reason, score);
            root.append(row);
        });
    }

    function renderSession(index) {
        const session = data.sessions[index];
        if (!session) return;
        $$('.session-card').forEach((card, cardIndex) => card.classList.toggle('active', cardIndex === index));
        const reader = $('#session-reader');
        reader.replaceChildren();
        reader.append(el('span', 'session-date', formatDate(session.date)), el('h2', '', session.title), el('div', 'session-text', session.text || session.excerpt));
    }

    function renderSessions() {
        const root = $('#session-list');
        root.replaceChildren();
        (data.sessions || []).forEach((session, index) => {
            const card = el('button', 'session-card');
            card.type = 'button';
            card.append(el('b', '', session.title), el('p', '', session.excerpt), el('small', '', formatDate(session.date)));
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
    }

    bindEvents();
    syncDestinationUI();
    if (data) {
        hydrate(data);
        const initialView = location.hash.slice(1);
        if (initialView && $(`[data-page="${initialView}"]`)) switchView(initialView, false);
    } else {
        showToast('لم يتم العثور على ملف البيانات. شغّل أداة التحديث أولًا.', 'error');
        $('#data-health span').textContent = 'البيانات غير جاهزة';
    }
})();
