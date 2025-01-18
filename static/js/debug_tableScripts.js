let userIdToDelete = null;

// Open the edit modal with pre-filled data
function openEditModal(id, name, gender, domicile) {
    document.getElementById('editName').value = name;
    document.getElementById('editGender').value = gender;
    document.getElementById('editDomicile').value = domicile;

    const form = document.getElementById('editForm');
    form.onsubmit = function (event) {
        event.preventDefault();
        updateUser(id);
    };

    new bootstrap.Modal(document.getElementById('editModal')).show();
}

// Update user information
function updateUser(userId) {
    const name = document.getElementById('editName').value;
    const gender = document.getElementById('editGender').value;
    const domicile = document.getElementById('editDomicile').value;

    fetch(`/update_user/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                gender,
                domicile
            })
        })
        .then(response => response.json())
        .then(data => {
            showToast(data.message);
            location.reload();
        })
        .catch(error => showToast('Error updating user: ' + error, 'danger'));
}

// Open the delete confirmation modal
function openDeleteModal(userId) {
    userIdToDelete = userId;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

// Confirm deletion of user
document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
    fetch(`/delete_user/${userIdToDelete}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            showToast(data.message);
            location.reload();
        })
        .catch(error => showToast('Error deleting user: ' + error, 'danger'));
});

// Start face recognition
function startFaceRecognition() {
    fetch('/trigger_recognition', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error('Error:', error));
}

// Show toast notification
function showToast(message, type = 'success') {
    const toastTitle = document.getElementById('toast-title');
    const toastBody = document.getElementById('toast-body');
    const toast = new bootstrap.Toast(document.getElementById('toast'));

    toastTitle.textContent = type === 'success' ? 'Success' : 'Error';
    toastBody.textContent = message;

    const toastElement = document.getElementById('toast');
    toastElement.classList.toggle('bg-success', type === 'success');
    toastElement.classList.toggle('bg-danger', type === 'danger');

    toast.show();
}