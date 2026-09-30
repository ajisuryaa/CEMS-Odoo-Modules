/** Topbar dropdowns: account menu + notifications panel */
(function () {
    function closeDrop(wrap, btn, panel) {
        if (!wrap || !btn || !panel) {
            return;
        }
        wrap.classList.remove("is-open");
        btn.setAttribute("aria-expanded", "false");
        panel.hidden = true;
    }

    function openDrop(wrap, btn, panel) {
        wrap.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
        panel.hidden = false;
    }

    function toggleDrop(wrap, btn, panel) {
        if (wrap.classList.contains("is-open")) {
            closeDrop(wrap, btn, panel);
        } else {
            openDrop(wrap, btn, panel);
        }
    }

    function bindTopbarMenus() {
        var accountWrap = document.getElementById("o_cems_hub_account_wrap");
        var accountBtn = document.getElementById("o_cems_hub_account_btn");
        var accountMenu = document.getElementById("o_cems_hub_account_menu");

        var notifyWrap = document.getElementById("o_cems_hub_notify_wrap");
        var notifyBtn = document.getElementById("o_cems_hub_notify");
        var notifyPanel = document.getElementById("o_cems_hub_notify_panel");
        var markAllBtn = document.getElementById("o_cems_hub_notify_mark_all");
        var badge = notifyWrap && notifyWrap.querySelector(".cems-hub-notify-badge");

        function closeAll() {
            closeDrop(accountWrap, accountBtn, accountMenu);
            closeDrop(notifyWrap, notifyBtn, notifyPanel);
        }

        if (accountBtn && accountWrap && accountMenu) {
            accountBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                var willOpen = !accountWrap.classList.contains("is-open");
                closeDrop(notifyWrap, notifyBtn, notifyPanel);
                if (willOpen) {
                    openDrop(accountWrap, accountBtn, accountMenu);
                } else {
                    closeDrop(accountWrap, accountBtn, accountMenu);
                }
            });
        }

        if (notifyBtn && notifyWrap && notifyPanel) {
            notifyBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                var willOpen = !notifyWrap.classList.contains("is-open");
                closeDrop(accountWrap, accountBtn, accountMenu);
                if (willOpen) {
                    openDrop(notifyWrap, notifyBtn, notifyPanel);
                } else {
                    closeDrop(notifyWrap, notifyBtn, notifyPanel);
                }
            });
        }

        if (markAllBtn && notifyPanel) {
            markAllBtn.addEventListener("click", function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                notifyPanel.querySelectorAll(".cems-hub-notify-item.is-unread").forEach(function (item) {
                    item.classList.remove("is-unread");
                });
                var meta = notifyPanel.querySelector(".cems-hub-notify-head-meta");
                if (meta) {
                    meta.textContent = "All caught up";
                }
                if (badge) {
                    badge.hidden = true;
                }
            });
        }

        document.addEventListener("click", function (ev) {
            var inAccount = accountWrap && accountWrap.contains(ev.target);
            var inNotify = notifyWrap && notifyWrap.contains(ev.target);
            if (!inAccount && !inNotify) {
                closeAll();
            }
        });

        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape") {
                closeAll();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindTopbarMenus);
    } else {
        bindTopbarMenus();
    }
})();
