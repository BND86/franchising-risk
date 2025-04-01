document.addEventListener("DOMContentLoaded", function () {
    let currentPage = window.location.pathname.split("/").pop();
    let navButtons = document.querySelectorAll(".nav-button");

    navButtons.forEach(button => {
        if (button.getAttribute("href") === currentPage) {
            button.classList.add("active");
        }
    });
});
