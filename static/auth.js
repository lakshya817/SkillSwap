
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");

    if (!form) return;

    const message = document.getElementById("authMessage");
    const button = document.getElementById("registerButton");

    const showMessage = (text, type) => {
        message.textContent = text;
        message.className = `auth-message ${type}`;
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const fullName = document.getElementById("full_name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        if (password !== confirmPassword) {
            showMessage("Your passwords do not match.", "error");
            return;
        }

        if (password.length < 8 || password.length > 128) {
            showMessage("Password must be between 8 and 128 characters.", "error");
            return;
        }

        button.disabled = true;
        button.textContent = "Creating your account...";

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(
                    data.error || "Unable to create your account. Please try again.",
                    "error"
                );
                return;
            }

            showMessage(
                "Your account has been created successfully. Redirecting to sign in...",
                "success"
            );

            form.reset();

            setTimeout(() => {
                window.location.href = "/login";
            }, 1500);

        } catch (error) {
            console.error("Registration error:", error);
            showMessage(
                "A connection error occurred. Please try again.",
                "error"
            );
        } finally {
            button.disabled = false;
            button.innerHTML = 'Create Account <span aria-hidden="true">→</span>';
        }
    });

    const year = document.querySelector("[data-current-year]");
    if (year) {
        year.textContent = new Date().getFullYear();
    }
});
