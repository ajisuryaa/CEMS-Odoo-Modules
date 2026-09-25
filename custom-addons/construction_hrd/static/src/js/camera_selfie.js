/** CEMS portal — open device camera and capture selfie (no file picker UX). */
(function () {
    "use strict";

    function $(id) {
        return document.getElementById(id);
    }

    function initCameraSelfie() {
        var root = $("o_cems_selfie_camera");
        if (!root) {
            return;
        }

        var video = $("o_cems_camera_video");
        var canvas = $("o_cems_camera_canvas");
        var snapshot = $("o_cems_camera_snapshot");
        var fileInput = $("o_cems_selfie");
        var btnStart = $("o_cems_camera_start");
        var btnCapture = $("o_cems_camera_capture");
        var btnRetake = $("o_cems_camera_retake");
        var errEl = $("o_cems_camera_error");
        var okEl = $("o_cems_camera_ok");
        var form = $("o_cems_check_in_form");
        var stream = null;

        function showError(msg) {
            if (errEl) {
                errEl.textContent = msg || "";
                errEl.classList.toggle("d-none", !msg);
            }
            if (okEl) {
                okEl.classList.add("d-none");
            }
        }

        function showOk() {
            if (errEl) {
                errEl.classList.add("d-none");
            }
            if (okEl) {
                okEl.classList.remove("d-none");
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

        function setPreviewMode(mode) {
            // mode: 'live' | 'snap' | 'idle'
            if (video) {
                video.classList.toggle("d-none", mode !== "live");
            }
            if (snapshot) {
                snapshot.classList.toggle("d-none", mode !== "snap");
            }
        }

        function startCamera() {
            showError("");
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
                    setPreviewMode("live");
                    btnCapture.disabled = false;
                    btnStart.textContent = "Restart Camera";
                    if (btnRetake) {
                        btnRetake.classList.add("d-none");
                    }
                    if (okEl) {
                        okEl.classList.add("d-none");
                    }
                    // Clear previous capture
                    if (fileInput) {
                        fileInput.value = "";
                    }
                })
                .catch(function (err) {
                    var msg = "Unable to open camera. Allow camera permission and try again.";
                    if (err && err.name === "NotAllowedError") {
                        msg = "Camera permission denied. Allow camera in the browser site settings.";
                    } else if (err && err.name === "NotFoundError") {
                        msg = "No camera found on this device.";
                    }
                    showError(msg);
                    btnCapture.disabled = true;
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
            // Mirror like a typical selfie preview
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
                    setPreviewMode("snap");
                    stopStream();
                    btnCapture.disabled = true;
                    if (btnRetake) {
                        btnRetake.classList.remove("d-none");
                    }
                    showOk();
                },
                "image/jpeg",
                0.9
            );
        }

        function retake() {
            if (fileInput) {
                fileInput.value = "";
            }
            if (snapshot) {
                snapshot.src = "";
            }
            if (okEl) {
                okEl.classList.add("d-none");
            }
            startCamera();
        }

        if (btnStart) {
            btnStart.addEventListener("click", function (ev) {
                ev.preventDefault();
                startCamera();
            });
        }
        if (btnCapture) {
            btnCapture.addEventListener("click", function (ev) {
                ev.preventDefault();
                captureSelfie();
            });
        }
        if (btnRetake) {
            btnRetake.addEventListener("click", function (ev) {
                ev.preventDefault();
                retake();
            });
        }

        if (form) {
            form.addEventListener("submit", function (ev) {
                if (!fileInput || !fileInput.files || !fileInput.files.length) {
                    ev.preventDefault();
                    showError("Please open the camera and capture a selfie before check-in.");
                }
            });
        }

        // Stop camera if user leaves the page
        window.addEventListener("pagehide", stopStream);
        window.addEventListener("beforeunload", stopStream);
    }

    function boot() {
        initCameraSelfie();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
