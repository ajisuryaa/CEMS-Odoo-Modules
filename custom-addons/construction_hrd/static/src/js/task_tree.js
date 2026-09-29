/** CEMS My Tasks — collapse / expand project groups. */
(function () {
    "use strict";

    function initTaskTree() {
        var root = document.getElementById("o_cems_task_tree");
        if (!root) {
            return;
        }

        root.querySelectorAll(".cems-task-project-toggle").forEach(function (btn) {
            btn.addEventListener("click", function (ev) {
                ev.preventDefault();
                var group = btn.closest(".cems-task-group");
                if (!group) {
                    return;
                }
                var collapsed = group.classList.toggle("is-collapsed");
                btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
            });
        });
    }

    function boot() {
        initTaskTree();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
