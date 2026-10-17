// Global utilities for Client Tracker
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash alerts after 4s
    document.querySelectorAll('.alert-auto-dismiss').forEach(function (el) {
      setTimeout(function () {
        if (window.bootstrap && bootstrap.Alert) {
          try {
            var alert = bootstrap.Alert.getOrCreateInstance(el);
            alert.close();
          } catch (e) {
            el.remove();
          }
        } else {
          el.remove();
        }
      }, 4000);
    });

    // Delete confirmation modal wiring
    var deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
      deleteModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        if (!button) return;
        var action = button.getAttribute('data-delete-url');
        var name = button.getAttribute('data-delete-name') || 'this record';
        var form = deleteModal.querySelector('#deleteModalForm');
        var nameEl = deleteModal.querySelector('#deleteModalName');
        if (form) form.setAttribute('action', action || '#');
        if (nameEl) nameEl.textContent = name;
      });
    }

    // Client-side live search on client list page
    var searchInput = document.getElementById('clientSearchInput');
    if (searchInput) {
      var rows = document.querySelectorAll('[data-client-row]');
      searchInput.addEventListener('input', function () {
        var term = this.value.toLowerCase().trim();
        var visible = 0;
        rows.forEach(function (row) {
          var text = (row.getAttribute('data-client-search') || '').toLowerCase();
          var match = !term || text.indexOf(term) !== -1;
          row.style.display = match ? '' : 'none';
          if (match) visible++;
        });
        var empty = document.getElementById('clientSearchEmpty');
        if (empty) empty.style.display = (visible === 0 && term) ? '' : 'none';
      });
    }
  });
})();