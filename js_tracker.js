// UX Interaction Tracker - Injected JavaScript
// Captures all user interactions and sends to Python backend

(function() {
    'use strict';

    if (window.__UX_TRACKER_LOADED__) return;
    window.__UX_TRACKER_LOADED__ = true;

    console.log('[UX Tracker] Initialized on:', window.location.href);

    // ── Helpers ──────────────────────────────────────────────────────────────

    function throttle(func, delay) {
        let lastCall = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastCall >= delay) { lastCall = now; func(...args); }
        };
    }

    function getSelector(el) {
        if (!el) return '';
        if (el.id) return '#' + el.id;
        if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\s+/).slice(0, 2).join('.');
            if (cls) return el.tagName.toLowerCase() + '.' + cls;
        }
        return el.tagName.toLowerCase();
    }

    function getElementText(el) {
        if (!el) return '';
        return (el.innerText || el.textContent || el.value || '').trim().substring(0, 100);
    }

    function isSensitiveField(el) {
        if (!el) return false;
        const check = ((el.type || '') + ' ' + (el.name || '') + ' ' + (el.id || '')).toLowerCase();
        return ['password','passwd','pwd','ssn','credit','card','cvv','passport'].some(p => check.includes(p));
    }

    function getScrollDepth() {
        const wh = window.innerHeight;
        const dh = document.documentElement.scrollHeight;
        const st = window.pageYOffset || document.documentElement.scrollTop;
        if (dh <= wh) return 100;
        return Math.round((st / (dh - wh)) * 100);
    }

    // Identify the semantic role of an input field for UX research
    function getFieldName(el) {
        if (!el) return 'unknown';
        const candidates = [el.name, el.id, el.placeholder,
                            el.getAttribute('aria-label'),
                            el.getAttribute('data-field')];
        for (const c of candidates) {
            if (c && c.trim()) return c.trim().substring(0, 60);
        }
        // Try label
        if (el.id) {
            const lbl = document.querySelector('label[for="' + el.id + '"]');
            if (lbl) return lbl.innerText.trim().substring(0, 60);
        }
        return el.tagName.toLowerCase();
    }

    // ── State ─────────────────────────────────────────────────────────────────

    let lastScrollY = window.pageYOffset || 0;
    const inputStartTimes = new WeakMap(); // el -> ISO timestamp

    // ── Click ─────────────────────────────────────────────────────────────────

    document.addEventListener('click', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'click',
            element: getElementText(e.target),
            selector: getSelector(e.target),
            x: e.clientX,
            y: e.clientY
        });
    }, true);

    document.addEventListener('dblclick', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'dblclick',
            element: getElementText(e.target),
            selector: getSelector(e.target),
            x: e.clientX,
            y: e.clientY
        });
    }, true);

    // ── Input field tracking ──────────────────────────────────────────────────

    // Typing start
    document.addEventListener('focusin', function(e) {
        const el = e.target;
        if (!el || !['INPUT','TEXTAREA','SELECT'].includes(el.tagName)) return;
        if (isSensitiveField(el)) return;
        inputStartTimes.set(el, new Date().toISOString());
        window.__UX_LOG_EVENT__({
            type: 'input_start',
            field_name: getFieldName(el),
            selector: getSelector(el)
        });
    }, true);

    // Typing end
    document.addEventListener('focusout', function(e) {
        const el = e.target;
        if (!el || !['INPUT','TEXTAREA','SELECT'].includes(el.tagName)) return;
        if (isSensitiveField(el)) return;
        const startTime = inputStartTimes.get(el) || null;
        window.__UX_LOG_EVENT__({
            type: 'input_end',
            field_name: getFieldName(el),
            selector: getSelector(el),
            typing_start: startTime,
            typing_end: new Date().toISOString()
        });
        inputStartTimes.delete(el);
    }, true);

    // ── Scroll ────────────────────────────────────────────────────────────────

    const scrollHandler = throttle(function() {
        const currentY = window.pageYOffset || document.documentElement.scrollTop;
        const direction = currentY > lastScrollY ? 'down' : 'up';
        lastScrollY = currentY;
        window.__UX_LOG_EVENT__({
            type: 'scroll',
            scroll_y: currentY,
            scroll_depth_percent: getScrollDepth(),
            scroll_direction: direction
        });
    }, 400);
    window.addEventListener('scroll', scrollHandler, true);

    // ── Keyboard ──────────────────────────────────────────────────────────────

    document.addEventListener('keydown', function(e) {
        if (isSensitiveField(e.target)) {
            window.__UX_LOG_EVENT__({ type: 'keypress', key_type: '[SENSITIVE_FIELD]' });
            return;
        }
        const key = e.key;
        window.__UX_LOG_EVENT__({
            type: 'keypress',
            key_type: key === 'Enter' ? 'Enter' : key === 'Backspace' ? 'Backspace' : 'KeyPressed'
        });
    }, true);

    // ── Mouse movement ────────────────────────────────────────────────────────

    const mouseMoveHandler = throttle(function(e) {
        window.__UX_LOG_EVENT__({ type: 'mousemove', x: e.clientX, y: e.clientY });
    }, 1000);
    document.addEventListener('mousemove', mouseMoveHandler, true);

    // ── Focus / visibility ────────────────────────────────────────────────────

    window.addEventListener('focus', function() {
        window.__UX_LOG_EVENT__({ type: 'focus_change', focus_state: 'focused' });
    });
    window.addEventListener('blur', function() {
        window.__UX_LOG_EVENT__({ type: 'focus_change', focus_state: 'blurred' });
    });
    document.addEventListener('visibilitychange', function() {
        window.__UX_LOG_EVENT__({
            type: 'focus_change',
            focus_state: document.hidden ? 'hidden' : 'visible'
        });
    });

    // ── Form error detection ──────────────────────────────────────────────────

    // Watch for HTML5 validation errors on submit
    document.addEventListener('invalid', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'form_error',
            field_name: getFieldName(e.target),
            selector: getSelector(e.target),
            message: (e.target.validationMessage || '').substring(0, 120)
        });
    }, true);

    // Watch for submit failures (form submitted but page didn't navigate = likely error)
    document.addEventListener('submit', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'form_submit',
            selector: getSelector(e.target)
        });
    }, true);

    console.log('[UX Tracker] All event listeners attached');
})();
