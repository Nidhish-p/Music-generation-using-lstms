document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM fully loaded!");

    const selectButtons = document.querySelectorAll(".select-btn");
    const selectedText = document.getElementById("selected-text");
    const sampleNoInput = document.getElementById("sample_no");
    const musicForm = document.getElementById("musicForm");

    // Check if sampleNoInput exists in the DOM
    if (!sampleNoInput) {
        console.error("⚠️ Error: Hidden input #sample_no not found in the DOM!");
        return;
    }

    selectButtons.forEach(button => {
        button.addEventListener("click", function () {
            console.log("🎵 Select button clicked:", this);

            // Find closest music-box and get dataset ID
            const musicBox = this.closest(".music-box");
            if (!musicBox) {
                console.error("⚠️ Error: Music box not found for button:", this);
                return;
            }

            const sampleNo = musicBox.dataset.id; // More reliable than getAttribute("data-id")
            if (!sampleNo) {
                console.error("⚠️ Error: Missing data-id on music-box:", musicBox);
                return;
            }

            console.log("✅ Retrieved Sample ID:", sampleNo);

            // Debugging: Check input field before setting value
            console.log("Before updating sample_noInput:", sampleNoInput.value);

            // Update the hidden input field
            sampleNoInput.value = sampleNo;

            // Check if value is updated
            console.log("After updating sample_noInput:", sampleNoInput.value);

            // Update UI text
            selectedText.textContent = `Sample ${sampleNo}`;
            console.log("✅ Updated UI text:", selectedText.textContent);

            // Highlight selected box
            document.querySelectorAll(".music-box").forEach(box => box.classList.remove("selected"));
            musicBox.classList.add("selected");
        });
    });

    // Prevent form submission if sample_no is empty
    if (musicForm) {
        musicForm.addEventListener("submit", function (event) {
            console.log("📨 Form submitted with sample_no:", sampleNoInput.value);

            if (!sampleNoInput.value) {
                event.preventDefault();
                alert("⚠️ Please select a sample before submitting!");
                console.warn("⚠️ Form submission prevented due to missing sample_no.");
            }
        });
    } else {
        console.warn("⚠️ Warning: Form #musicForm not found in the DOM.");
    }
});
