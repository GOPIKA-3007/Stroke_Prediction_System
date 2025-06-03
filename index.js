document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault(); // prevent default form submission

    const role = document.querySelector('input[name="role"]:checked')?.value;

    if (role === 'admin') {
      window.location.href = 'admin.html';
    } else if (role === 'doctor') {
      window.location.href = 'doctor.html';
    } else if (role === 'patient') {
      window.location.href = 'patient.html';
    } else {
      alert('Please select a role.');
    }
});
