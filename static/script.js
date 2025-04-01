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
