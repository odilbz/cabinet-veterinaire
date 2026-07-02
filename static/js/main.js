document.addEventListener('DOMContentLoaded', () => {
    // 1. Alert auto-dismiss
    document.querySelectorAll('.alert').forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) closeBtn.addEventListener('click', () => alert.remove());
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        }, 5000);
    });
    // 2. Modal management
    const openButtons = document.querySelectorAll('[data-modal-target]');
    const closeButtons = document.querySelectorAll('[data-modal-close]');
    const modals = document.querySelectorAll('.modal');
    openButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = document.getElementById(button.getAttribute('data-modal-target'));
            if (modal) {
                modal.classList.add('active');
                const form = modal.querySelector('form');
                if (button.hasAttribute('data-med-id')) {
                    if (form) {
                        form.querySelector('[name="med_id"]').value = button.getAttribute('data-med-id');
                        form.querySelector('[name="name"]').value = button.getAttribute('data-med-name');
                        form.querySelector('[name="category"]').value = button.getAttribute('data-med-cat') || 'Général';
                        form.querySelector('[name="buy_price"]').value = button.getAttribute('data-med-buy');
                        form.querySelector('[name="sell_price"]').value = button.getAttribute('data-med-sell');
                        form.querySelector('[name="quantity"]').value = button.getAttribute('data-med-qty');
                    }
                } else if (form && form.querySelector('[name="med_id"]')) {
                    form.querySelector('[name="med_id"]').value = '';
                    form.reset();
                }
            }
        });
    });
    closeButtons.forEach(button => button.addEventListener('click', () => modals.forEach(m => m.classList.remove('active'))));
    window.addEventListener('click', (e) => modals.forEach(m => { if (e.target === m) m.classList.remove('active'); }));
    // 3. Stock entry auto-fill prices
    const stockEntrySelect = document.getElementById('medicine_select');
    if (stockEntrySelect) {
        stockEntrySelect.addEventListener('change', (e) => {
            const opt = e.target.options[e.target.selectedIndex];
            const buy = document.getElementById('entry_buy_price');
            const sell = document.getElementById('entry_sell_price');
            const newName = document.getElementById('new_name');
            if (opt && opt.value !== "") {
                if (buy) buy.value = opt.getAttribute('data-buy') || '';
                if (sell) sell.value = opt.getAttribute('data-sell') || '';
                if (newName) { newName.value = ''; newName.disabled = true; }
            } else {
                if (buy) buy.value = '';
                if (sell) sell.value = '';
                if (newName) newName.disabled = false;
            }
        });
    }
    // 4. Live search for stock table
    const instantSearch = document.getElementById('instant_search');
    if (instantSearch) {
        instantSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.table tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
            });
        });
    }
});