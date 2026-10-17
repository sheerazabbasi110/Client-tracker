// Dynamic invoice builder
(function () {
    'use strict';

    var itemsBody = null;
    var subtotalEl = null;
    var taxEl = null;
    var totalEl = null;
    var taxRateInput = null;

    function toNum(v) {
        var n = parseFloat(v);
        return isNaN(n) ? 0 : n;
    }

    function formatMoney(n) {
        return n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    function recalcRow(row) {
        var qty = toNum(row.querySelector('.item-qty').value);
        var price = toNum(row.querySelector('.item-price').value);
        var sub = qty * price;
        var cell = row.querySelector('.item-subtotal');
        if (cell) cell.textContent = formatMoney(sub);
        return sub;
    }

    function recalcAll() {
        if (!itemsBody) return;
        var subtotal = 0;
        itemsBody.querySelectorAll('tr.item-row').forEach(function (row) {
            subtotal += recalcRow(row);
        });
        var taxRate = toNum(taxRateInput ? taxRateInput.value : 0);
        var tax = subtotal * (taxRate / 100);
        var total = subtotal + tax;

        if (subtotalEl) subtotalEl.textContent = formatMoney(subtotal);
        if (taxEl) taxEl.textContent = formatMoney(tax);
        if (totalEl) totalEl.textContent = formatMoney(total);
    }

    function bindRow(row) {
        row.querySelectorAll('.item-qty, .item-price').forEach(function (el) {
            el.addEventListener('input', function () {
                recalcRow(row);
                recalcAll();
            });
        });
        var removeBtn = row.querySelector('.remove-item');
        if (removeBtn) {
            removeBtn.addEventListener('click', function (e) {
                e.preventDefault();
                if (itemsBody.querySelectorAll('tr.item-row').length <= 1) {
                    // clear instead of removing last row
                    row.querySelector('.item-description').value = '';
                    row.querySelector('.item-qty').value = 1;
                    row.querySelector('.item-price').value = '0.00';
                } else {
                    row.remove();
                }
                recalcAll();
            });
        }
    }

    function createRow() {
        var tr = document.createElement('tr');
        tr.className = 'item-row';
        tr.innerHTML =
            '<td><input type="text" name="item_description[]" class="form-control form-control-sm item-description" placeholder="Description" required></td>' +
            '<td style="width:100px;"><input type="number" name="item_quantity[]" class="form-control form-control-sm item-qty" value="1" min="1" step="1"></td>' +
            '<td style="width:130px;"><input type="number" name="item_unit_price[]" class="form-control form-control-sm item-price" value="0.00" min="0" step="0.01"></td>' +
            '<td style="width:120px;" class="text-end align-middle item-subtotal">0.00</td>' +
            '<td style="width:50px;" class="text-center align-middle">' +
            '<button type="button" class="btn btn-sm btn-outline-danger remove-item" tabindex="-1">' +
            '<i class="bi bi-x-lg"></i></button></td>';
        bindRow(tr);
        return tr;
    }

    document.addEventListener('DOMContentLoaded', function () {
        itemsBody = document.getElementById('itemsBody');
        if (!itemsBody) return;

        subtotalEl = document.getElementById('calcSubtotal');
        taxEl = document.getElementById('calcTax');
        totalEl = document.getElementById('calcTotal');
        taxRateInput = document.getElementById('taxRateInput');

        // Bind existing rows
        itemsBody.querySelectorAll('tr.item-row').forEach(bindRow);

        var addBtn = document.getElementById('addItemBtn');
        if (addBtn) {
            addBtn.addEventListener('click', function (e) {
                e.preventDefault();
                var row = createRow();
                itemsBody.appendChild(row);
                var input = row.querySelector('.item-description');
                if (input) input.focus();
                recalcAll();
            });
        }

        if (taxRateInput) {
            taxRateInput.addEventListener('input', recalcAll);
        }

        recalcAll();
    });
})();