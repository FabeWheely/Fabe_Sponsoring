const contactForm = document.querySelector(".contact-form");
const formDialog = document.querySelector(".form-dialog");
const dialogTitle = document.querySelector("#form-dialog-title");
const dialogMessage = document.querySelector(".form-dialog__message");
const dialogCloseButton = document.querySelector(".form-dialog__close");
const submitButton = contactForm.querySelector('button[type="submit"]');

function showFormMessage(success, message) {
    formDialog.classList.toggle("form-dialog--success", success);
    formDialog.classList.toggle("form-dialog--error", !success);
    dialogTitle.textContent = success ? "Nachricht gesendet" : "Senden fehlgeschlagen";
    dialogMessage.textContent = message;
    formDialog.showModal();
}

contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    submitButton.disabled = true;

    try {
        const response = await fetch("/api/contact", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(Object.fromEntries(new FormData(contactForm)))
        });

        let result;
        try {
            result = await response.json();
        } catch {
            throw new Error("Der Server hat keine gültige Antwort zurückgegeben.");
        }

        if (!result || typeof result !== "object" || !response.ok || !result.success) {
            const reason = typeof result?.message === "string"
                ? result.message
                : `Versand fehlgeschlagen (HTTP ${response.status}).`;
            throw new Error(reason);
        }

        showFormMessage(true, result.message || "Deine Nachricht wurde erfolgreich gesendet.");
        contactForm.reset();
    } catch (error) {
        const message = error instanceof TypeError
            ? "Der Server ist nicht erreichbar. Bitte starte die Anwendung mit „python server.py“ und versuche es erneut."
            : error.message;
        showFormMessage(false, message);
    } finally {
        submitButton.disabled = false;
    }
});

dialogCloseButton.addEventListener("click", () => formDialog.close());