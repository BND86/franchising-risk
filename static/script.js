/*document.addEventListener("DOMContentLoaded", function () {
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

// Функция для скрытия/показа секций
function toggleSection(id) {
    var section = document.getElementById(id);
    if (section) {
        section.style.display = section.style.display === "none" || section.style.display === "" ? "block" : "none";
        console.log("Переключение секции:", id, "состояние:", section.style.display);
    } else {
        console.warn("Секция с id", id, "не найдена!");
    }
}

// Инициализация - скрываем все секции при загрузке
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.survey-section').forEach(function(section) {
        section.style.display = 'none';
    });
});*/

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

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('survey-form');
    const errorMessage = document.getElementById('error-message');
    const submitButton = document.getElementById('submit-button');

    // Функция для проверки видимости вопроса
    function isQuestionVisible(question) {
        return window.getComputedStyle(question).display !== 'none';
    }

    // Обработка условных вопросов
    document.querySelectorAll('.survey-options input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const nextQuestionId = this.getAttribute('data-next');
            if (nextQuestionId) {
                // Скрыть все следующие условные вопросы
                document.querySelectorAll('.survey-question[data-conditional="true"]').forEach(q => {
                    q.style.display = 'none';
                });
                
                // Показать следующий вопрос, если он есть
                const nextQuestion = document.getElementById(`question-${nextQuestionId}`);
                if (nextQuestion) {
                    nextQuestion.style.display = 'block';
                }
            }
        });
    });

    // Валидация формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        errorMessage.style.display = 'none';
        
        const requiredQuestions = Array.from(document.querySelectorAll('.survey-question[data-required="true"]'));
        let allAnswered = true;
        
        // Сбросить все отметки о неотвеченных вопросах
        document.querySelectorAll('.survey-question').forEach(q => {
            q.classList.remove('unanswered');
        });
        
        // Проверить каждый обязательный вопрос (только видимые)
        requiredQuestions.forEach(question => {
            if (isQuestionVisible(question)) {
                const questionId = question.getAttribute('data-id');
                // Исправлено: ищем радио-кнопки с именем, начинающимся с q[questionId]
                const selectedOption = form.querySelector(`input[name^="q${questionId}_"]:checked`);
                
                if (!selectedOption) {
                    allAnswered = false;
                    question.classList.add('unanswered');
                }
            }
        });

        if (!allAnswered) {
            errorMessage.style.display = 'block';
            
            // Прокрутить к первому неотвеченному вопросу
            const firstUnanswered = document.querySelector('.survey-question.unanswered');
            if (firstUnanswered) {
                firstUnanswered.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            // Если все ответы есть, отправить форму
            form.submit();
        }
    });
});