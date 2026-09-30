/** Account chip dropdown: My Profile + Logout */
(function () {
    function closeMenu(wrap, btn, menu) {
        wrap.classList.remove("is-open");
        btn.setAttribute("aria-expanded", "false");
        menu.hidden = true;
    }

    function openMenu(wrap, btn, menu) {
        wrap.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
        menu.hidden = false;
    }

    function bindAccountMenu() {
        var wrap = document.getElementById("o_cems_hub_account_wrap");
        var btn = document.getElementById("o_cems_hub_account_btn");
        var menu = document.getElementById("o_cems_hub_account_menu");
        if (!wrap || !btn || !menu) {
            return;
        }

        btn.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            if (wrap.classList.contains("is-open")) {
                closeMenu(wrap, btn, menu);
            } else {
                openMenu(wrap, btn, menu);
            }
        });

        document.addEventListener("click", function (ev) {
            if (!wrap.contains(ev.target)) {
                closeMenu(wrap, btn, menu);
            }
        });

        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape") {
                closeMenu(wrap, btn, menu);
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindAccountMenu);
    } else {
        bindAccountMenu();
    }
})();
