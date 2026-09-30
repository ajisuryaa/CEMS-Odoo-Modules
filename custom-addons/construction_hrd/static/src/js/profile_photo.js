/** Preview selected profile photo before save. */
(function () {
    function bindPhotoPreview(root) {
        var input = root.querySelector("#o_cems_profile_photo_input");
        var img = root.querySelector("#o_cems_profile_photo_img");
        var nameEl = root.querySelector("#o_cems_profile_photo_name");
        if (!input || !img) {
            return;
        }
        input.addEventListener("change", function () {
            var file = input.files && input.files[0];
            if (!file) {
                if (nameEl) {
                    nameEl.textContent = "No file selected";
                }
                return;
            }
            if (nameEl) {
                nameEl.textContent = file.name;
            }
            var reader = new FileReader();
            reader.onload = function (ev) {
                img.src = ev.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var root = document.getElementById("o_cems_profile_photo");
        if (root) {
            bindPhotoPreview(root.closest("form") || document);
        }
    });
})();
