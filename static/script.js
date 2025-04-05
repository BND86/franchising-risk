document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript загружен и работает!");

    // Подсветка активной кнопки меню
    let currentPage = window.location.pathname;
    let navButtons = document.querySelectorAll(".nav-button");

    navButtons.forEach(button => {
        let buttonPath = button.getAttribute("href");
        if (buttonPath === currentPage) {
            button.classList.add("active");
        }
    });

    // Проверка существования кнопок перед обработкой
    if (navButtons.length === 0) {
        console.warn("Кнопки навигации не найдены!");
    }
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("input[type=radio], input[type=checkbox]").forEach(input => {
        input.addEventListener("change", function() {
            let nextQuestion = this.dataset.next;
            if (nextQuestion) {
                let questionDiv = document.querySelector(`[data-id="${nextQuestion}"]`);
                if (questionDiv) questionDiv.style.display = "block";
            }
        });
    });
});

/*// Функция для скрытия/показа секций
function toggleSection(id) {
    var section = document.getElementById(id);
    if (section) {
        section.style.display = section.style.display === "none" || section.style.display === "" ? "block" : "none";
        console.log("Переключение секции:", id, "состояние:", section.style.display);
    } else {
        console.warn("Секция с id", id, "не найдена!");
    }
}*/

/*document.addEventListener("DOMContentLoaded", function () {
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
};

document.addEventListener("DOMContentLoaded", function() {
    console.log("Страница загружена, JavaScript работает!");
});*/