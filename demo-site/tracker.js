/**
 * Lightweight Real-Time Web Traffic Analytics Tracker Snippet
 * Embedded via: <script src="/tracker.js" data-site-id="demo-site" defer></script>
 * Resilient: Never blocks rendering, fails gracefully if collector is offline.
 */
(function () {
  "use strict";

  // Prevent double initialization
  if (window.__TRAFFIC_TRACKER_INITIALIZED__) return;
  window.__TRAFFIC_TRACKER_INITIALIZED__ = true;

  try {
    const currentScript = document.currentScript || document.querySelector("script[data-site-id]");
    const siteId = (currentScript && currentScript.getAttribute("data-site-id")) || "demo-site";
    
    // Collector API endpoint: can be overridden via window.__COLLECTOR_URL__ or data-api-url attribute
    const collectorUrl =
      (currentScript && currentScript.getAttribute("data-api-url")) ||
      window.__COLLECTOR_URL__ ||
      "http://localhost:8000/api/collect";

    // 1. Session Management in sessionStorage
    const SESSION_KEY = "_ta_session_id";
    let sessionId = "";
    try {
      sessionId = sessionStorage.getItem(SESSION_KEY);
      if (!sessionId) {
        sessionId = "sess_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
        sessionStorage.setItem(SESSION_KEY, sessionId);
      }
    } catch (e) {
      sessionId = "sess_fallback_" + Date.now();
    }

    const pageStartTime = performance.now();

    // 2. Performance & Load Time Calculation
    function getLoadTimeMs() {
      try {
        const perfEntries = performance.getEntriesByType("navigation");
        if (perfEntries && perfEntries.length > 0) {
          const nav = perfEntries[0];
          return Math.round(nav.loadEventEnd > 0 ? nav.loadEventEnd - nav.startTime : performance.now());
        }
      } catch (e) {}
      return Math.round(performance.now() - pageStartTime);
    }

    // 3. Safe Dispatch Helper (JSON fetch or sendBeacon)
    function sendPayload(payload, useBeacon = false) {
      try {
        const jsonStr = JSON.stringify(payload);
        if (useBeacon && navigator.sendBeacon) {
          // sendBeacon sends with text/plain by default; backend parses both
          const blob = new Blob([jsonStr], { type: "application/json" });
          const sent = navigator.sendBeacon(collectorUrl, blob);
          if (sent) return;
        }

        // Fallback or standard async fetch
        fetch(collectorUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: jsonStr,
          keepalive: useBeacon,
          mode: "cors",
        }).catch(function () {
          // Silently ignore network failures if backend is offline
        });
      } catch (err) {
        // Tracker must NEVER throw to host application
      }
    }

    function buildBasePayload(eventType) {
      return {
        site_id: siteId,
        session_id: sessionId,
        event_type: eventType,
        path: window.location.pathname || "/",
        referrer: document.referrer || "",
        user_agent: navigator.userAgent || "",
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        load_time_ms: 0.0,
        duration_ms: 0.0,
        status_code: 200,
      };
    }

    // 4. Track Pageview on DOM Ready / Window Load
    function trackPageview() {
      const payload = buildBasePayload("pageview");
      payload.load_time_ms = getLoadTimeMs();
      
      // Check if page indicates error state (e.g., custom 404 indicator)
      if (document.body && document.body.getAttribute("data-status-code")) {
        payload.status_code = parseInt(document.body.getAttribute("data-status-code"), 10) || 200;
      }
      sendPayload(payload, false);
    }

    if (document.readyState === "complete") {
      setTimeout(trackPageview, 50);
    } else {
      window.addEventListener("load", function () {
        setTimeout(trackPageview, 50);
      });
    }

    // 5. Track Link Clicks
    document.addEventListener("click", function (evt) {
      try {
        const target = evt.target && evt.target.closest("a");
        if (target && target.href) {
          const payload = buildBasePayload("click");
          payload.referrer = window.location.href;
          payload.path = target.getAttribute("href") || target.pathname;
          sendPayload(payload, false);
        }
      } catch (e) {}
    }, { passive: true });

    // 6. Track Form Submissions
    document.addEventListener("submit", function (evt) {
      try {
        const form = evt.target;
        if (form) {
          const payload = buildBasePayload("form_submit");
          payload.path = form.getAttribute("action") || window.location.pathname;
          sendPayload(payload, false);
        }
      } catch (e) {}
    }, { passive: true });

    // 7. Track Time-on-Page on Unload / Visibility Hidden
    let unloaded = false;
    function trackUnload() {
      if (unloaded) return;
      unloaded = true;
      const durationMs = Math.round(performance.now() - pageStartTime);
      const payload = buildBasePayload("unload");
      payload.duration_ms = durationMs;
      sendPayload(payload, true);
    }

    window.addEventListener("beforeunload", trackUnload);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") {
        trackUnload();
      }
    });

  } catch (globalErr) {
    // Top-level catch to guarantee no interference with host page
  }
})();
