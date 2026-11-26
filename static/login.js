
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const emailInput = document.getElementById("loginEmail");
    const passwordInput = document.getElementById("loginPassword");
    const messageBox = document.getElementById("loginMessage");
    const loginButton = document.getElementById("loginButton");
    const togglePassword = document.getElementById("togglePassword");

    if (!loginForm) return;

    function showMessage(message, type = "error") {
        messageBox.textContent = message;
        messageBox.style.display = "block";
        messageBox.style.background =
            type === "success" ? "#e8f6ef" : "#fff0f0";
        messageBox.style.color =
            type === "success" ? "#16865b" : "#c0392b";
        messageBox.style.border =
            type === "success"
                ? "1px solid #b8e4ce"
                : "1px solid #f2c4c4";
    }

    // Show or hide password
    if (togglePassword) {
        togglePassword.addEventListener("change", () => {
            passwordInput.type = togglePassword.checked
                ? "text"
                : "password";
        });
    }

    // Handle login submission
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        messageBox.textContent = "";
        messageBox.style.display = "none";

        const email = emailInput.value.trim().toLowerCase();
        const password = passwordInput.value;

        if (!email || !password) {
            showMessage("Please enter your email address and password.");
            return;
        }

        loginButton.disabled = true;
        loginButton.textContent = "Signing in...";

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(
                    data.error || "Unable to sign in. Please try again."
                );
                return;
            }

            showMessage("Login successful! Welcome back.", "success");

            loginButton.textContent = "Signed in successfully";

            setTimeout(() => {
                window.location.href = "/";
            }, 1000);

        } catch (error) {
            showMessage(
                "Unable to connect to SkillSwap. Please try again."
            );
        } finally {
            if (!loginButton.textContent.includes("successfully")) {
                loginButton.disabled = false;
                loginButton.innerHTML = 'Sign In <span aria-hidden="true">→</span>';
            }
        }
    });
});
