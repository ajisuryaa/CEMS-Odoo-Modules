/** CEMS My Projects — project detail dialog. */
(function () {
    "use strict";

    function $(id) {
        return document.getElementById(id);
    }

    function text(el, value) {
        if (!el) {
            return;
        }
        el.textContent = value && String(value).trim() ? value : "—";
    }

    function initProjectDialog() {
        var list = $("o_cems_project_list");
        var dialog = $("o_cems_project_dialog");
        if (!list || !dialog) {
            return;
        }

        var backdrop = $("o_cems_project_dialog_backdrop");
        var closeBtn = $("o_cems_project_dialog_close");
        var dismissBtn = $("o_cems_project_dialog_dismiss");
        var titleEl = $("o_cems_project_dialog_title");
        var tasksLink = $("o_cems_project_dialog_tasks");

        function openDialog(btn) {
            var name = btn.getAttribute("data-name") || "Project";
            var lat = btn.getAttribute("data-lat");
            var lon = btn.getAttribute("data-lon");
            var radius = btn.getAttribute("data-radius");
            var location = "Not configured";
            if (lat && lon) {
                location =
                    Number(lat).toFixed(5) +
                    ", " +
                    Number(lon).toFixed(5) +
                    (radius ? " · radius " + radius + " m" : "");
            }

            if (titleEl) {
                titleEl.textContent = name;
            }
            text($("o_cems_proj_manager"), btn.getAttribute("data-manager"));
            text($("o_cems_proj_customer"), btn.getAttribute("data-customer"));
            text(
                $("o_cems_proj_tasks"),
                btn.getAttribute("data-tasks") != null
                    ? btn.getAttribute("data-tasks") + " tasks"
                    : ""
            );
            text(
                $("o_cems_proj_progress"),
                btn.getAttribute("data-progress")
                    ? btn.getAttribute("data-progress") + "%"
                    : ""
            );
            text($("o_cems_proj_location"), location);
            text($("o_cems_proj_members"), btn.getAttribute("data-members"));
            text($("o_cems_proj_engineers"), btn.getAttribute("data-engineers"));

            if (tasksLink) {
                var canOpen = btn.getAttribute("data-can-open-tasks") === "1";
                var id = btn.getAttribute("data-id");
                if (canOpen && id) {
                    tasksLink.href = "/my/projects/" + id;
                    tasksLink.classList.remove("d-none");
                } else {
                    tasksLink.href = "#";
                    tasksLink.classList.add("d-none");
                }
            }

            dialog.hidden = false;
            dialog.setAttribute("aria-hidden", "false");
            document.body.classList.add("cems-project-dialog-open");
        }

        function closeDialog() {
            dialog.hidden = true;
            dialog.setAttribute("aria-hidden", "true");
            document.body.classList.remove("cems-project-dialog-open");
        }

        list.querySelectorAll(".cems-project-row").forEach(function (btn) {
            btn.addEventListener("click", function (ev) {
                ev.preventDefault();
                openDialog(btn);
            });
        });

        if (closeBtn) {
            closeBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                closeDialog();
            });
        }
        if (dismissBtn) {
            dismissBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                closeDialog();
            });
        }
        if (backdrop) {
            backdrop.addEventListener("click", closeDialog);
        }
        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape" && !dialog.hidden) {
                closeDialog();
            }
        });
    }

    function boot() {
        initProjectDialog();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
