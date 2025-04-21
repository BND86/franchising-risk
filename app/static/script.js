document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('survey-form');
    const errorMessage = document.getElementById('error-message');

    // 1. Инициализация категорий (теперь можно открывать несколько)
    function initCategories() {
        const categoryHeaders = document.querySelectorAll('.category-header');
        
        categoryHeaders.forEach(header => {
            const categoryGroup = header.closest('.category-group');
            const questions = categoryGroup.querySelectorAll('.survey-question:not([data-conditional="true"])');
            
            header.style.cursor = 'pointer';
            
            header.addEventListener('click', function() {
                const isOpening = !categoryGroup.classList.contains('category-opened');
                
                // Переключаем только текущую категорию (не затрагивая другие)
                if (isOpening) {
                    openCategory(categoryGroup);
                } else {
                    closeCategory(categoryGroup);
                }
            });
            
            // По умолчанию все категории закрыты
            closeCategory(categoryGroup);
        });
    }

    function openCategory(categoryGroup) {
        categoryGroup.classList.add('category-opened');
        categoryGroup.querySelectorAll('.survey-question:not([data-conditional="true"])').forEach(q => {
            q.style.display = 'block';
        });
    }

    function closeCategory(categoryGroup) {
        categoryGroup.classList.remove('category-opened');
        // Скрываем все вопросы в категории, включая условные
        categoryGroup.querySelectorAll('.survey-question').forEach(q => {
            q.style.display = 'none';
        });
        // Сбрасываем выбранные ответы в условных вопросах
        categoryGroup.querySelectorAll('.survey-question[data-conditional="true"] input[type="radio"]').forEach(radio => {
            radio.checked = false;
        });
    }

    // 2. Управление условными вопросами
    // 2. Управление условными вопросами
    function initConditionalQuestions() {
        document.querySelectorAll('.survey-options input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const nextQuestionId = this.getAttribute('data-next');
                const currentQuestion = this.closest('.survey-question');
                const categoryGroup = currentQuestion.closest('.category-group');
                
                // Скрываем только те условные вопросы, которые связаны с текущим вопросом
                // (а не все в категории)
                if (nextQuestionId) {
                    const previouslyShown = categoryGroup.querySelectorAll('.survey-question[data-conditional="true"]');
                    previouslyShown.forEach(q => {
                        // Скрываем только если это не следующий вопрос и не другие уже отвеченные вопросы
                        if (q.id !== `question-${nextQuestionId}` && !hasAnswer(q)) {
                            q.style.display = 'none';
                        }
                    });
                }
                
                // Если есть следующий вопрос и категория открыта - показываем его
                if (nextQuestionId && categoryGroup.classList.contains('category-opened')) {
                    const nextQuestion = document.getElementById(`question-${nextQuestionId}`);
                    
                    // Проверяем, что следующий вопрос находится в той же категории
                    if (nextQuestion && nextQuestion.closest('.category-group') === categoryGroup) {
                        nextQuestion.style.display = 'block';
                        nextQuestion.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }
            });
        });
        
        // Функция для проверки, есть ли ответ на вопрос
        function hasAnswer(question) {
            const inputs = question.querySelectorAll('input[type="radio"]');
            for (let input of inputs) {
                if (input.checked) return true;
            }
            return false;
        }
    }

    // 3. Валидация формы
    function initFormValidation() {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            errorMessage.style.display = 'none';
            
            let allAnswered = true;
            let unansweredQuestions = [];
            
            document.querySelectorAll('.survey-question').forEach(q => {
                q.classList.remove('unanswered');
            });
            
            // Проверяем ВСЕ обязательные вопросы, независимо от того, открыта категория или нет
            document.querySelectorAll('.survey-question[data-required="true"]').forEach(question => {
                const questionId = question.getAttribute('data-id');
                const selectedOption = form.querySelector(`input[name="q${questionId}"]:checked`); // <--- тут
            
                
                if (!selectedOption) {
                    allAnswered = false;
                    question.classList.add('unanswered');
                    unansweredQuestions.push(question);
                    
                    // Если категория закрыта - открываем её
                    const categoryGroup = question.closest('.category-group');
                    if (!categoryGroup.classList.contains('category-opened')) {
                        openCategory(categoryGroup);
                    }
                }
            });

            if (!allAnswered) {
                errorMessage.style.display = 'block';
                errorMessage.textContent = 'Пожалуйста, ответьте на все обязательные вопросы (отмечены красным)';
                
                if (unansweredQuestions.length > 0) {
                    // Прокручиваем к первому неотвеченному вопросу
                    unansweredQuestions[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    // Подсвечиваем все неотвеченные вопросы
                    unansweredQuestions.forEach(q => {
                        q.classList.add('unanswered');
                    });
                }
            } else {
                // Все обязательные вопросы отвечены - отправляем форму
                form.submit();
            }
        });
    }

    function isQuestionVisible(question) {
        return window.getComputedStyle(question).display !== 'none';
    }

    // Инициализация
    initCategories();
    initConditionalQuestions();
    initFormValidation();
});

