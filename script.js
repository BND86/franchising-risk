document.addEventListener("DOMContentLoaded", function () {
    let currentPage = window.location.pathname.split("/").pop();
    let navButtons = document.querySelectorAll(".nav-button");

    navButtons.forEach(button => {
        if (button.getAttribute("href") === currentPage) {
            button.classList.add("active");
        }
    });
});

function toggleSection(id) {
    var section = document.getElementById(id);
    if (section.style.display === "none" || section.style.display === "") {
        section.style.display = "block"; // Показываем секцию
    } else {
        section.style.display = "none"; // Скрываем секцию
    }
}