
/* =========================================
   SKILLSWAP — FRONTEND INTERACTIONS
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    // Sidebar navigation active state
    const navLinks = document.querySelectorAll(
        ".sidebar-nav .nav-link"
    );

    navLinks.forEach(link => {
        link.addEventListener("click", () => {
            navLinks.forEach(item => item.classList.remove("active"));
            link.classList.add("active");
        });
    });

    // Smooth scrolling for internal navigation
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener("click", event => {
            const targetId = link.getAttribute("href");

            if (!targetId || targetId === "#") {
                event.preventDefault();
                return;
            }

            const target = document.querySelector(targetId);

            if (target) {
                event.preventDefault();
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });

    // Reliable logout handler
    const logoutButtons = document.querySelectorAll(
        "#logoutBtn, .logout-btn, [data-action='logout']"
    );

    logoutButtons.forEach(button => {
        button.addEventListener("click", async event => {
            event.preventDefault();

            if (button.dataset.loggingOut === "true") return;

            const confirmed = window.confirm(
                "Are you sure you want to log out?"
            );

            if (!confirmed) return;

            button.dataset.loggingOut = "true";

            try {
                const response = await fetch("/api/logout", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                if (response.ok) {
                    window.location.replace("/login");
                    return;
                }

                button.dataset.loggingOut = "false";
                alert("Unable to log out. Please try again.");

            } catch (error) {
                console.error("Logout error:", error);
                button.dataset.loggingOut = "false";
                alert("A network error occurred. Please try again.");
            }
        });
    });

    // Update the current year automatically
    const yearElement = document.querySelector("[data-current-year]");

    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    console.log("SkillSwap frontend initialized successfully.");

});
