// Toast for success/error notifications
function showToast(toastId) {
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
}

// Update video feed when camera is selected
document.getElementById('cameraSelect').addEventListener('change', function () {
    const selectedCameraIndex = this.value;
    const videoFeedElement = document.getElementById('videoFeed');
    videoFeedElement.src = `/video_feed/${selectedCameraIndex}?t=${new Date().getTime()}`;
});

// Refresh video feed on button click
document.getElementById('refreshButton').addEventListener('click', function () {
    const selectedCameraIndex = document.getElementById('cameraSelect').value;
    const videoFeedElement = document.getElementById('videoFeed');
    const timestamp = new Date().getTime();
    videoFeedElement.src = `/video_feed/${selectedCameraIndex}?t=${timestamp}`;
});

// Capture image and upload to backend
document.getElementById('captureButton').addEventListener('click', function () {
    const selectedCameraIndex = document.getElementById('cameraSelect').value;
    // Capture image and user data
    fetch('/capture_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: document.getElementById('name').value,
                gender: document.getElementById('gender').value,
                domicile: document.getElementById('domicile').value,
                selected_camera_index: selectedCameraIndex
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Handle successful response
                showToast('successToast');
                document.getElementById('image').value = '';
                document.getElementById('gender').value = '';
                document.getElementById('name').value = '';
                document.getElementById('domicile').value = '';
            } else {
                showToast('errorToast');
                document.getElementById('image').value = '';
                document.getElementById('gender').value = '';
                document.getElementById('name').value = '';
                document.getElementById('domicile').value = '';
            }
        })
        .catch(() => showToast('errorToast'));
});

// Upload image from file input and submit form
document.getElementById('uploadButton').addEventListener('click', function () {
    const imageFile = document.querySelector('input[name="image"]').files[0];
    if (!imageFile) {
        showToast('errorToast'); // Show error if no image selected
        return;
    }
    const formData = new FormData(document.getElementById('userForm'));
    fetch('/upload_user_image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === 'User added successfully!') {
                showToast('successToast');
                document.getElementById('image').value = '';
                document.getElementById('gender').value = '';
                document.getElementById('name').value = '';
                document.getElementById('domicile').value = '';
            } else {
                showToast('errorToast');
                document.getElementById('image').value = '';
                document.getElementById('gender').value = '';
                document.getElementById('name').value = '';
                document.getElementById('domicile').value = '';
            }
        })
        .catch(() => showToast('errorToast'));
    document.getElementById('image').value = '';
    document.getElementById('gender').value = '';
    document.getElementById('name').value = '';
    document.getElementById('domicile').value = '';
});

// Debug table button redirect
document.getElementById('debugTableButton').addEventListener('click', function () {
    window.location.href = "/debug_table";
});

// Redirect to car_count
document.getElementById('carCountDirect').addEventListener('click', function () {
    window.location.href = "/car_count";
});


let autoRefreshEnabled = true;  // Flag to enable or disable automatic refresh

// Function to fetch recognized data and update the table
function fetchRecognizedData() {
    $.ajax({
        url: '/recognize_face',  // Endpoint that processes the captured face
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ name: capturedName }),  // Pass the captured name to the server
        success: function (response) {
            var tableBody = $('#user_data_body');
            tableBody.empty();  // Clear current table rows

            // Add new rows with the data from the response
            response.forEach(function (user) {
                var row = `<tr>
                    <td class="text-center mb-2">${user.name}</td>
                    <td class="text-center mb-2">${user.gender}</td>
                    <td class="text-center mb-2">${user.domicile}</td>
                    <td class="text-center mb-2">${user.confidence}%</td>
                </tr>`;
                tableBody.append(row);
            });
        },
        error: function (xhr, status, error) {
            console.error("Error fetching user data: " + error);
        }
    });
}

// Event listener for the switch to toggle auto-refresh and fetch data manually
document.getElementById('captureButtonML').addEventListener('change', function () {
    autoRefreshEnabled = this.checked;  // Update autoRefreshEnabled based on switch state

    // Update the label text to reflect the current state
    const switchLabel = document.getElementById('switchLabel');
    if (autoRefreshEnabled) {
        switchLabel.textContent = "Auto-Refresh: On";
        document.getElementById('captureFaceButton').style.display = 'none';  // Hide capture button
    } else {
        switchLabel.textContent = "Auto-Refresh: Off";
        document.getElementById('captureFaceButton').style.display = 'inline-block';  // Show capture button
        fetchRecognizedData();  // Fetch data manually when auto-refresh is turned off
    }
});

// Event listener for the Capture Face button (manual data capture)
document.getElementById('captureFaceButton').addEventListener('click', function () {
    fetchRecognizedData();  // Fetch data manually when the button is clicked
});

// Set interval for automatic refresh every 5 seconds if enabled
setInterval(function() {
    if (autoRefreshEnabled) {
        fetchRecognizedData();  // Fetch data automatically
    }
}, 5000);

// Function to fetch recognized data
function fetchRecognizedData() {
    fetch('/get_recognized_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.log(data.error);
            } else {
                updateUserDataTable(data);
            }
        })
        .catch(error => console.error('Error fetching recognized data:', error));
}

// Function to update the table with the fetched user data
function updateUserDataTable(data) {
    const tableBody = document.getElementById('user_data_body');
    tableBody.innerHTML = ''; // Clear any previous data

    // Create a new row for the user data
    const row = document.createElement('tr');

    const nameCell = document.createElement('td');
    nameCell.classList.add('text-center');
    nameCell.textContent = data.name;
    row.appendChild(nameCell);

    const genderCell = document.createElement('td');
    genderCell.classList.add('text-center');
    genderCell.textContent = data.gender;
    row.appendChild(genderCell);

    const domicileCell = document.createElement('td');
    domicileCell.classList.add('text-center');
    domicileCell.textContent = data.domicile;
    row.appendChild(domicileCell);

    const confidenceCell = document.createElement('td');
    confidenceCell.classList.add('text-center');
    confidenceCell.textContent = data.confidence;
    row.appendChild(confidenceCell);

    // Append the new row to the table
    tableBody.appendChild(row);
}

// Event listener to capture face and fetch recognized data
document.getElementById('captureButtonML').addEventListener('click', fetchRecognizedData);

// Handle YOLOv8 image classification form submission
document.getElementById('yoloForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    fetch('/classify_image', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast('errorToast');
        } else {
            const resultDiv = document.getElementById('yoloResult');
            resultDiv.innerHTML = `
                <h5>Classification Result:</h5>
                <img src="data:image/jpeg;base64,${data.image}" class="img-fluid" alt="Classified Image">
                <ul>
                    ${data.classifications.map(c => `<li>Name: ${c.name}, Confidence: ${c.confidence}%</li>`).join('')}
                </ul>
            `;
            showToast('successToast');
        }
    })
    .catch(() => showToast('errorToast'));
});
