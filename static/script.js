console.log("NKV Hospital website loaded successfully.");

document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll("a, button");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            console.log(
                "NKV Hospital action:",
                button.textContent.trim()
            );

        });

    });

});