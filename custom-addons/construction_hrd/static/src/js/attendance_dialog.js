/** CEMS hub — attendance camera dialog (single Check In / Check Out). */
(function () {
    "use strict";

    function $(id) {
        return document.getElementById(id);
    }

    function requestPosition(onOk, onErr) {
        if (!navigator.geolocation) {
            onErr({ message: "Geolocation is not supported by this browser." });
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

        var stream = null;
        var mode = openBtn.getAttribute("data-mode") || "check_in";
        var gpsReady = false;
        var selfieReady = false;

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

        function startCamera() {
            showError("");
            selfieReady = false;
            setShutterMode(false);
            updateSubmitState();
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
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
                    video.srcObject = stream;
                    setPreview("live");
                    if (fileInput) {
                        fileInput.value = "";
                    }
                })
                .catch(function (err) {
                    var msg = "Unable to open camera. Allow camera permission.";
                    if (err && err.name === "NotAllowedError") {
                        msg = "Camera permission denied. Allow camera in site settings.";
                    } else if (err && err.name === "NotFoundError") {
                        msg = "No camera found on this device.";
                    }
                    showError(msg);
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
                    setGpsText(
                        "GPS OK (" + lat.toFixed(5) + ", " + lon.toFixed(5) + ")",
                        "ok"
                    );
                    updateSubmitState();
                },
                function (err) {
                    gpsReady = false;
                    setGpsText(formatGeoError(err), "err");
                    updateSubmitState();
                }
            );
        }

        function openDialog() {
            mode = openBtn.getAttribute("data-mode") || "check_in";
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
            setShutterMode(false);
            setPreview("live");
            if (snapshot) {
                snapshot.src = "";
            }
            if (fileInput) {
                fileInput.value = "";
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
