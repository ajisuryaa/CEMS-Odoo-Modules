/** CEMS hub — attendance camera dialog (single Check In / Check Out). */
(function () {
    "use strict";

    function $(id) {
        return document.getElementById(id);
    }

    function requestPosition(onOk, onErr) {
        if (!navigator.geolocation) {
            onErr({ code: 0, message: "Geolocation is not supported by this browser." });
            return;
        }
        try {
            var host = window.location.hostname;
            var secure =
                window.isSecureContext ||
                host === "localhost" ||
                host === "127.0.0.1";
            if (!secure) {
                onErr({
                    code: 0,
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
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 60000,
            }
        );
    }

    function formatGeoError(err) {
        if (!err) {
            return "Unable to get GPS. Enable location permission.";
        }
        if (err.code === 1) {
            return "Location permission denied. Allow Location for this site.";
        }
        if (err.code === 2) {
            return "Position unavailable. Try outdoors or another device.";
        }
        if (err.code === 3) {
            return "GPS timeout. Move near a window and retry.";
        }
        return err.message || "Unable to get GPS.";
    }

    function initAttendanceDialog() {
        var openBtn = $("o_cems_att_open_btn");
        var dialog = $("o_cems_att_dialog");
        if (!openBtn || !dialog) {
            return;
        }

        var backdrop = $("o_cems_att_dialog_backdrop");
        var closeBtn = $("o_cems_att_dialog_close");
        var form = $("o_cems_att_dialog_form");
        var titleEl = $("o_cems_att_dialog_title");
        var video = $("o_cems_att_video");
        var canvas = $("o_cems_att_canvas");
        var snapshot = $("o_cems_att_snapshot");
        var fileInput = $("o_cems_att_selfie");
        var latIn = $("o_cems_att_latitude");
        var lonIn = $("o_cems_att_longitude");
        var gpsStatus = $("o_cems_att_gps_status");
        var errEl = $("o_cems_att_dialog_error");
        var shutter = $("o_cems_att_capture");
        var iconCapture = shutter && shutter.querySelector(".cems-att-icon-capture");
        var iconRetake = shutter && shutter.querySelector(".cems-att-icon-retake");
        var submitBtn = $("o_cems_att_submit");
        var permissionEl = $("o_cems_att_permission");
        var permissionLead = $("o_cems_att_permission_lead");
        var permissionSteps = $("o_cems_att_permission_steps");
        var permissionRetry = $("o_cems_att_permission_retry");

        var stream = null;
        var mode = openBtn.getAttribute("data-mode") || "check_in";
        var gpsReady = false;
        var selfieReady = false;
        var cameraDenied = false;
        var gpsDenied = false;
        var cameraOk = false;

        var STEPS = {
            camera: [
                "Tap the lock / info icon in the browser address bar.",
                "Find <strong>Camera</strong> and set it to <strong>Allow</strong>.",
                "Reload this page, then open Check In again.",
                "Still blocked? Device Settings → Apps / Safari → Camera → Allow for this site.",
            ],
            location: [
                "Tap the lock / info icon in the browser address bar.",
                "Find <strong>Location</strong> and set it to <strong>Allow</strong>.",
                "Reload this page, then open Check In again.",
                "On phone: Settings → Privacy / Location → enable for your browser, then Allow for this site.",
            ],
            both: [
                "Tap the lock / info icon in the browser address bar.",
                "Set <strong>Camera</strong> and <strong>Location</strong> to <strong>Allow</strong>.",
                "Reload this page, then open Check In again.",
                "Still blocked? Device Settings → Apps / Safari → Site permissions → Allow Camera & Location.",
            ],
        };

        function showError(msg) {
            if (!errEl) {
                return;
            }
            errEl.textContent = msg || "";
            errEl.classList.toggle("d-none", !msg);
        }

        function setGpsText(text, kind) {
            if (!gpsStatus) {
                return;
            }
            gpsStatus.textContent = text;
            gpsStatus.classList.remove("is-ok", "is-err", "is-wait");
            if (kind) {
                gpsStatus.classList.add("is-" + kind);
            }
        }

        function stopStream() {
            if (stream) {
                stream.getTracks().forEach(function (t) {
                    t.stop();
                });
                stream = null;
            }
            if (video) {
                video.srcObject = null;
            }
        }

        function updateSubmitState() {
            if (!submitBtn) {
                return;
            }
            var needGps = mode === "check_in";
            var ok = selfieReady && (!needGps || gpsReady);
            submitBtn.disabled = !ok;
            submitBtn.classList.toggle("d-none", !selfieReady);
        }

        function setShutterVisible(visible) {
            if (!shutter) {
                return;
            }
            shutter.classList.toggle("d-none", !visible);
            shutter.disabled = !visible;
        }

        function setShutterMode(captured) {
            if (!shutter) {
                return;
            }
            shutter.setAttribute(
                "aria-label",
                captured ? "Retake" : "Capture"
            );
            if (iconCapture) {
                iconCapture.classList.toggle("d-none", captured);
            }
            if (iconRetake) {
                iconRetake.classList.toggle("d-none", !captured);
            }
        }

        function setPreview(modeName) {
            if (video) {
                video.classList.toggle("d-none", modeName !== "live");
            }
            if (snapshot) {
                snapshot.classList.toggle("d-none", modeName !== "snap");
            }
        }

        function renderPermissionSteps(kind) {
            if (!permissionSteps) {
                return;
            }
            var items = STEPS[kind] || STEPS.both;
            permissionSteps.innerHTML = items
                .map(function (html) {
                    return "<li>" + html + "</li>";
                })
                .join("");
        }

        function refreshPermissionPanel() {
            var showCamera = cameraDenied;
            var showGps = gpsDenied && mode === "check_in";
            var show = showCamera || showGps;

            if (!permissionEl) {
                return;
            }

            if (!show) {
                permissionEl.classList.add("d-none");
                if (cameraOk && !selfieReady) {
                    setPreview("live");
                }
                setShutterVisible(cameraOk);
                return;
            }

            var kind = "both";
            var lead = "Camera or location access is blocked for this site.";
            if (showCamera && !showGps) {
                kind = "camera";
                lead = "Camera access is blocked. Check-in needs a selfie.";
            } else if (!showCamera && showGps) {
                kind = "location";
                lead = "Location access is blocked. Check-in needs GPS on site.";
            } else {
                kind = "both";
                lead = "Camera and location access are blocked for this site.";
            }

            if (permissionLead) {
                permissionLead.textContent = lead;
            }
            renderPermissionSteps(kind);
            permissionEl.classList.remove("d-none");

            // Hide live preview while permission help is shown
            if (video) {
                video.classList.add("d-none");
            }
            if (snapshot) {
                snapshot.classList.add("d-none");
            }
            setShutterVisible(false);
            if (submitBtn) {
                submitBtn.classList.add("d-none");
            }
        }

        function hidePermissionPanel() {
            cameraDenied = false;
            if (permissionEl) {
                permissionEl.classList.add("d-none");
            }
        }

        function startCamera() {
            showError("");
            selfieReady = false;
            cameraOk = false;
            setShutterMode(false);
            updateSubmitState();
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                cameraDenied = true;
                cameraOk = false;
                refreshPermissionPanel();
                showError("Camera is not supported in this browser.");
                return;
            }
            stopStream();
            navigator.mediaDevices
                .getUserMedia({
                    audio: false,
                    video: {
                        facingMode: "user",
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                    },
                })
                .then(function (mediaStream) {
                    stream = mediaStream;
                    cameraDenied = false;
                    cameraOk = true;
                    video.srcObject = stream;
                    if (fileInput) {
                        fileInput.value = "";
                    }
                    refreshPermissionPanel();
                    if (!permissionEl || permissionEl.classList.contains("d-none")) {
                        setPreview("live");
                        setShutterVisible(true);
                    }
                })
                .catch(function (err) {
                    cameraOk = false;
                    stopStream();
                    if (err && err.name === "NotAllowedError") {
                        cameraDenied = true;
                        refreshPermissionPanel();
                        showError("");
                        return;
                    }
                    cameraDenied = false;
                    refreshPermissionPanel();
                    var msg = "Unable to open camera. Allow camera permission.";
                    if (err && err.name === "NotFoundError") {
                        msg = "No camera found on this device.";
                    }
                    showError(msg);
                    setShutterVisible(false);
                });
        }

        function captureSelfie() {
            if (!video || !canvas || !fileInput) {
                return;
            }
            if (!stream || !video.videoWidth) {
                showError("Camera is not ready yet. Wait a moment and try again.");
                return;
            }
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            var ctx = canvas.getContext("2d");
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(
                function (blob) {
                    if (!blob) {
                        showError("Failed to capture image.");
                        return;
                    }
                    var file = new File([blob], "selfie.jpg", { type: "image/jpeg" });
                    try {
                        var dt = new DataTransfer();
                        dt.items.add(file);
                        fileInput.files = dt.files;
                    } catch (e) {
                        showError("This browser cannot attach the selfie to the form.");
                        return;
                    }
                    if (snapshot) {
                        snapshot.src = URL.createObjectURL(blob);
                    }
                    setPreview("snap");
                    stopStream();
                    selfieReady = true;
                    setShutterMode(true);
                    showError("");
                    updateSubmitState();
                },
                "image/jpeg",
                0.9
            );
        }

        function requestGps() {
            gpsReady = false;
            updateSubmitState();
            setGpsText("Requesting GPS…", "wait");
            requestPosition(
                function (lat, lon) {
                    if (latIn) {
                        latIn.value = String(lat);
                    }
                    if (lonIn) {
                        lonIn.value = String(lon);
                    }
                    gpsReady = true;
                    gpsDenied = false;
                    setGpsText(
                        "GPS OK (" + lat.toFixed(5) + ", " + lon.toFixed(5) + ")",
                        "ok"
                    );
                    refreshPermissionPanel();
                    updateSubmitState();
                },
                function (err) {
                    gpsReady = false;
                    gpsDenied = !!(err && err.code === 1);
                    setGpsText(formatGeoError(err), "err");
                    refreshPermissionPanel();
                    updateSubmitState();
                }
            );
        }

        function retryPermissions() {
            showError("");
            hidePermissionPanel();
            gpsDenied = false;
            cameraDenied = false;
            startCamera();
            requestGps();
        }

        function openDialog() {
            mode = openBtn.getAttribute("data-mode") || "check_in";
            cameraDenied = false;
            gpsDenied = false;
            cameraOk = false;
            if (titleEl) {
                titleEl.textContent = mode === "check_out" ? "Check Out" : "Check In";
            }
            if (form) {
                form.action =
                    mode === "check_out"
                        ? "/my/cems/attendance/check_out"
                        : "/my/cems/attendance/check_in";
            }
            if (submitBtn) {
                submitBtn.textContent = mode === "check_out" ? "Check Out" : "Check In";
                submitBtn.classList.toggle("primary", mode !== "check_out");
                submitBtn.classList.toggle("dark", mode === "check_out");
            }
            if (permissionEl) {
                permissionEl.classList.add("d-none");
            }
            dialog.hidden = false;
            dialog.setAttribute("aria-hidden", "false");
            document.body.classList.add("cems-att-dialog-open");
            startCamera();
            requestGps();
        }

        function closeDialog() {
            stopStream();
            selfieReady = false;
            gpsReady = false;
            cameraDenied = false;
            gpsDenied = false;
            cameraOk = false;
            setShutterMode(false);
            setShutterVisible(true);
            setPreview("live");
            if (snapshot) {
                snapshot.src = "";
            }
            if (fileInput) {
                fileInput.value = "";
            }
            if (permissionEl) {
                permissionEl.classList.add("d-none");
            }
            showError("");
            dialog.hidden = true;
            dialog.setAttribute("aria-hidden", "true");
            document.body.classList.remove("cems-att-dialog-open");
            updateSubmitState();
        }

        openBtn.addEventListener("click", function (ev) {
            ev.preventDefault();
            openDialog();
        });
        if (closeBtn) {
            closeBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                closeDialog();
            });
        }
        if (backdrop) {
            backdrop.addEventListener("click", function () {
                closeDialog();
            });
        }
        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape" && !dialog.hidden) {
                closeDialog();
            }
        });

        if (permissionRetry) {
            permissionRetry.addEventListener("click", function (ev) {
                ev.preventDefault();
                retryPermissions();
            });
        }

        if (shutter) {
            shutter.addEventListener("click", function (ev) {
                ev.preventDefault();
                if (selfieReady) {
                    startCamera();
                } else {
                    captureSelfie();
                }
            });
        }

        if (form) {
            form.addEventListener("submit", function (ev) {
                if (!selfieReady) {
                    ev.preventDefault();
                    showError("Please capture a selfie first.");
                    return;
                }
                if (mode === "check_in" && !gpsReady) {
                    ev.preventDefault();
                    showError("GPS is required for check-in. Allow location and wait.");
                }
            });
        }

        window.addEventListener("pagehide", stopStream);
        window.addEventListener("beforeunload", stopStream);
    }

    function boot() {
        initAttendanceDialog();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
