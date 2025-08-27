document.addEventListener("DOMContentLoaded", () => {
    const counters = document.querySelectorAll(".counter");

    counters.forEach((counter) => {
        counter.innerText = "0"; // Start from 0

        const updateCounter = () => {
            const target = parseInt(counter.getAttribute("data-target")); // Get final number
            let current = parseInt(counter.innerText); // Get current number
            const increment = Math.ceil(target / 100); // Speed adjustment

            if (current < target) {
                counter.innerText = current + increment;
                setTimeout(updateCounter, 50); // Adjust speed
            } else {
                counter.innerText = target; // Ensure exact value
            }
        };

        updateCounter();
    });
});
