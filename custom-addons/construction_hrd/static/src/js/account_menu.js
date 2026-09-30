/** Topbar dropdowns: account menu + real notification panel */
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

    function cemsJsonRpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
                id: Date.now(),
            }),
        }).then(function (response) {
            return response.json();
        }).then(function (payload) {
            if (payload && payload.error) {
                throw payload.error;
            }
            return (payload && payload.result) || {};
        });
    }

    function updateBadge(badge, count) {
        if (!badge) {
            return;
        }
        if (count > 0) {
            badge.hidden = false;
            badge.textContent = String(count);
        } else {
            badge.hidden = true;
            badge.textContent = "";
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
        var meta = notifyPanel && notifyPanel.querySelector(".cems-hub-notify-head-meta");

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
                cemsJsonRpc("/my/cems/notifications/mark_all_read", {}).then(function (result) {
                    notifyPanel.querySelectorAll(".cems-hub-notify-item.is-unread").forEach(function (item) {
                        item.classList.remove("is-unread");
                    });
                    if (meta) {
                        meta.textContent = "All caught up";
                    }
                    updateBadge(badge, (result && result.unread_count) || 0);
                }).catch(function () {
                    /* keep UI as-is on failure */
                });
            });
        }

        if (notifyPanel) {
            notifyPanel.querySelectorAll("a.cems-hub-notify-item-link[data-notify-id]").forEach(function (link) {
                link.addEventListener("click", function () {
                    var id = parseInt(link.getAttribute("data-notify-id"), 10);
                    if (!id) {
                        return;
                    }
                    var item = link.closest(".cems-hub-notify-item");
                    cemsJsonRpc("/my/cems/notifications/mark_read", {
                        notification_ids: [id],
                    }).then(function (result) {
                        if (item) {
                            item.classList.remove("is-unread");
                        }
                        var unread = result && typeof result.unread_count === "number"
                            ? result.unread_count
                            : 0;
                        updateBadge(badge, unread);
                        if (meta) {
                            meta.textContent = unread > 0 ? unread + " new" : "All caught up";
                        }
                    }).catch(function () {
                        /* navigation still proceeds */
                    });
                });
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
