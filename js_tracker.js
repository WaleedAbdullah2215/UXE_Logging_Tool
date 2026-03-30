// UX Interaction Tracker - Injected JavaScript
// Captures all user interactions and sends to Python backend

(function() {
    'use strict';
    
    // Prevent multiple injections
    if (window.__UX_TRACKER_LOADED__) return;
    window.__UX_TRACKER_LOADED__ = true;
    
    console.log('[UX Tracker] Initialized on:', window.location.href);
    
    // Throttle helper
    function throttle(func, delay) {
        let lastCall = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                func(...args);
            }
        };
    }
    
    // Get element selector
    function getSelector(element) {
        if (!element) return '';
        if (element.id) return `#${element.id}`;
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/).slice(0, 2).join('.');
            if (classes) return `${element.tagName.toLowerCase()}.${classes}`;
        }
        return element.tagName.toLowerCase();
    }
    
    // Get element text (truncated)
    function getElementText(element) {
        if (!element) return '';
        const text = (element.innerText || element.textContent || element.value || '').trim();
        return text.substring(0, 100);
    }
    
    // Check if element is sensitive
    function isSensitiveField(element) {
        if (!element) return false;
        const type = (element.type || '').toLowerCase();
        const name = (element.name || '').toLowerCase();
        const id = (element.id || '').toLowerCase();
        
        const sensitivePatterns = ['password', 'passwd', 'pwd', 'ssn', 'credit', 'card', 'cvv', 'passport'];
        const checkString = `${type} ${name} ${id}`.toLowerCase();
        
        return sensitivePatterns.some(pattern => checkString.includes(pattern));
    }
    
    // Calculate scroll depth
    function getScrollDepth() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (documentHeight <= windowHeight) return 100;
        return Math.round((scrollTop / (documentHeight - windowHeight)) * 100);
    }
    
    // Track clicks
    document.addEventListener('click', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'click',
            element: getElementText(e.target),
            selector: getSelector(e.target),
            x: e.clientX,
            y: e.clientY
        });
    }, true);
    
    // Track double clicks
    document.addEventListener('dblclick', function(e) {
        window.__UX_LOG_EVENT__({
            type: 'dblclick',
            element: getElementText(e.target),
            selector: getSelector(e.target),
            x: e.clientX,
            y: e.clientY
        });
    }, true);
    
    // Track scroll (throttled to 500ms)
    const scrollHandler = throttle(function() {
        window.__UX_LOG_EVENT__({
            type: 'scroll',
            scroll_y: window.pageYOffset || document.documentElement.scrollTop,
            scroll_depth_percent: getScrollDepth()
        });
    }, 500);
    window.addEventListener('scroll', scrollHandler, true);
    
    // Track keypresses (NO content stored)
    document.addEventListener('keydown', function(e) {
        // Skip if in sensitive field
        if (isSensitiveField(e.target)) {
            window.__UX_LOG_EVENT__({
                type: 'keypress',
                key_type: '[SENSITIVE_FIELD]'
            });
            return;
        }
        
        window.__UX_LOG_EVENT__({
            type: 'keypress',
            key_type: e.key === 'Enter' ? 'Enter' : e.key === 'Backspace' ? 'Backspace' : 'KeyPressed'
        });
    }, true);
    
    // Track mouse movement (throttled to 1000ms)
    const mouseMoveHandler = throttle(function(e) {
        window.__UX_LOG_EVENT__({
            type: 'mousemove',
            x: e.clientX,
            y: e.clientY
        });
    }, 1000);
    document.addEventListener('mousemove', mouseMoveHandler, true);
    
    // Track focus changes
    window.addEventListener('focus', function() {
        window.__UX_LOG_EVENT__({
            type: 'focus_change',
            focus_state: 'focused'
        });
    });
    
    window.addEventListener('blur', function() {
        window.__UX_LOG_EVENT__({
            type: 'focus_change',
            focus_state: 'blurred'
        });
    });
    
    // Track visibility changes (tab switching)
    document.addEventListener('visibilitychange', function() {
        window.__UX_LOG_EVENT__({
            type: 'focus_change',
            focus_state: document.hidden ? 'hidden' : 'visible'
        });
    });
    
    console.log('[UX Tracker] All event listeners attached');
})();
