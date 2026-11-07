document.addEventListener('DOMContentLoaded', () => {
    // Generic FormData helper if needed for uploads
    const forms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            // Placeholder: functionality handled by browser default for FormData usually
            // but we ensure it's standard.
        });
    });
});

// Shared Visibility Toggle Function
function togglePublish(itemId, checkbox) {
    fetch(`/toggle_publish/${itemId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Visibility updated:', data.new_state);
                // Optional: Update UI classes if needed (e.g. gray out card)
                // For Dashboard: If it's turned OFF, it might disappear or fade
                if (checkbox.closest('.news-card') && !data.is_published) {
                    checkbox.closest('.news-card').style.opacity = '0.5';
                }
                if (checkbox.closest('.news-card') && data.is_published) {
                    checkbox.closest('.news-card').style.opacity = '1';
                }
            } else {
                alert('Error updating status');
                checkbox.checked = !checkbox.checked; // Revert
            }
        })
        .catch(err => {
            console.error(err);
            alert('Network error');
            checkbox.checked = !checkbox.checked;
        });
}
