/** CEMS portal attendance — GPS with reliable boot + user-triggered Enable GPS. */
(function () {
    "use strict";

    function $(id) {
        return document.getElementById(id);
    }

    function setStatus(statusEl, text, kind) {
        if (!statusEl) {
            return;
        }
        statusEl.textContent = text;
        statusEl.classList.remove("text-bg-secondary", "text-bg-success", "text-bg-danger", "text-bg-warning");
        if (kind === "ok") {
            statusEl.classList.add("text-bg-success");
        } else if (kind === "err") {
            statusEl.classList.add("text-bg-danger");
        } else if (kind === "wait") {
            statusEl.classList.add("text-bg-warning");
        } else {
            statusEl.classList.add("text-bg-secondary");
        }
    }

    function setGpsFields(latInput, lonInput, lat, lon) {
        if (latInput) {
            latInput.value = String(lat);
        }
        if (lonInput) {
            lonInput.value = String(lon);
        }
    }

    function formatGeoError(err) {
        if (!err) {
            return "Unable to get GPS. Enable location permission.";
        }
        // GeolocationPositionError codes: 1 PERMISSION_DENIED, 2 POSITION_UNAVAILABLE, 3 TIMEOUT
        if (err.code === 1) {
            return "Location permission denied. Allow Location for this site, then retry.";
        }
        if (err.code === 2) {
            return "Position unavailable. Try localhost/HTTPS or another device.";
        }
        if (err.code === 3) {
            return "GPS timeout. Move near a window / outdoors and retry.";
        }
        return err.message || "Unable to get GPS. Enable location permission.";
    }

    function requestPosition(onOk, onErr) {
        if (!navigator.geolocation) {
            onErr({ message: "Geolocation is not supported by this browser." });
            return;
        }
        // insecure origin hint (HTTP non-localhost)
        try {
            var host = window.location.hostname;
            var secure =
                window.isSecureContext ||
                host === "localhost" ||
                host === "127.0.0.1";
            if (!secure) {
                onErr({
                    message:
                        "GPS blocked on insecure HTTP. Open via http://localhost:8069 or HTTPS.",
                });
                return;
            }
        } catch (e) {
            /* ignore */
        }

        navigator.geolocation.getCurrentPosition(
            function (pos) {
                onOk(pos.coords.latitude, pos.coords.longitude);
            },
            function (err) {
                onErr(err);
            },
            {
                // false is more reliable on laptops without GPS chip
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 60000,
            }
        );
    }

    function wireCheckInGps() {
        var checkInBtn = $("o_cems_check_in_btn");
        var gpsBtn = $("o_cems_gps_btn");
        var latIn = $("o_cems_latitude");
        var lonIn = $("o_cems_longitude");
        var statusEl = $("o_cems_gps_status");

        if (!checkInBtn && !gpsBtn) {
            return;
        }

        function runGps() {
            setStatus(statusEl, "Requesting GPS…", "wait");
            if (checkInBtn) {
                checkInBtn.disabled = true;
            }
            requestPosition(
                function (lat, lon) {
                    setGpsFields(latIn, lonIn, lat, lon);
                    setStatus(
                        statusEl,
                        "GPS OK (" + lat.toFixed(5) + ", " + lon.toFixed(5) + ")",
                        "ok"
                    );
                    if (checkInBtn) {
                        checkInBtn.disabled = false;
                    }
                },
                function (err) {
                    setStatus(statusEl, formatGeoError(err), "err");
                    if (checkInBtn) {
                        checkInBtn.disabled = true;
                    }
                }
            );
        }

        if (gpsBtn) {
            gpsBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                runGps();
            });
        }

        // Auto-try once (may work); Enable GPS button is the reliable fallback
        setStatus(statusEl, "GPS not ready — click Enable GPS", "secondary");
        runGps();
    }

    function wireCheckOutGps() {
        var checkOutForm = $("o_cems_check_out_form");
        if (!checkOutForm) {
            return;
        }
        var outLat = $("o_cems_out_latitude");
        var outLon = $("o_cems_out_longitude");
        var gpsBtn = $("o_cems_out_gps_btn");
        var statusEl = $("o_cems_out_gps_status");

        function runGps() {
            if (statusEl) {
                setStatus(statusEl, "Requesting GPS…", "wait");
            }
            requestPosition(
                function (lat, lon) {
                    setGpsFields(outLat, outLon, lat, lon);
                    if (statusEl) {
                        setStatus(
                            statusEl,
                            "GPS OK (" + lat.toFixed(5) + ", " + lon.toFixed(5) + ")",
                            "ok"
                        );
                    }
                },
                function (err) {
                    if (statusEl) {
                        setStatus(statusEl, formatGeoError(err), "err");
                    }
                    // check-out still allowed without GPS
                }
            );
        }

        if (gpsBtn) {
            gpsBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                runGps();
            });
        }
        runGps();
    }

    function initGps() {
        var root = $("o_cems_portal_attendance");
        if (!root) {
            return;
        }
        wireCheckInGps();
        wireCheckOutGps();
    }

    function boot() {
        initGps();
    }

    // Odoo frontend assets often load AFTER DOMContentLoaded — handle both.
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
