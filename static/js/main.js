/**
 * SmartLoan - Client-Side Enhancements
 * Handles table search, responsive mobile sidebar, input chip helpers,
 * and confirmation dialogs.
 * 
 * NOTE: All core financial math is processed strictly on the Python backend!
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const mobileToggleBtn = document.getElementById('mobileSidebarToggle');
    const appSidebar = document.getElementById('appSidebar');

    if (mobileToggleBtn && appSidebar) {
        mobileToggleBtn.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 992) {
                if (!appSidebar.contains(e.target) && !mobileToggleBtn.contains(e.target)) {
                    appSidebar.classList.remove('show');
                }
            }
        });
    }

    // 2. Input Quick-Chips for Calculator
    const chipButtons = document.querySelectorAll('.chip-btn');
    chipButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const targetInputId = this.getAttribute('data-target');
            const targetVal = this.getAttribute('data-value');
            const inputField = document.getElementById(targetInputId);
            if (inputField) {
                inputField.value = targetVal;
                inputField.focus();
            }
        });
    });

    // 3. Search and Filter in Amortization Table
    const tableSearchInput = document.getElementById('amortTableSearch');
    const amortTable = document.getElementById('amortizationTable');

    if (tableSearchInput && amortTable) {
        tableSearchInput.addEventListener('keyup', function () {
            const query = this.value.toLowerCase().trim();
            const rows = amortTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 4. History Table Search Filter
    const historySearchInput = document.getElementById('historyTableSearch');
    const historyTable = document.getElementById('historyTable');

    if (historySearchInput && historyTable) {
        historySearchInput.addEventListener('keyup', function () {
            const query = this.value.toLowerCase().trim();
            const rows = historyTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

// Confirmation Dialog Helper
function confirmAction(message) {
    return confirm(message || "Are you sure you want to proceed with this action?");
}
