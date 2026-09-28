/** Live clock for CEMS hub Site Attendance panel. */
(function () {
    function pad(n) {
        return n < 10 ? '0' + n : String(n);
    }

    function tick() {
        var timeEl = document.getElementById('o_cems_hub_clock');
        var dateEl = document.getElementById('o_cems_hub_date');
        if (!timeEl && !dateEl) {
            return;
        }
        var now = new Date();
        if (timeEl) {
            timeEl.textContent =
                pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
        }
        if (dateEl) {
            dateEl.textContent = now.toLocaleDateString(undefined, {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            });
        }
    }

    function start() {
        if (!document.getElementById('o_cems_hub_clock')) {
            return;
        }
        tick();
        setInterval(tick, 1000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
