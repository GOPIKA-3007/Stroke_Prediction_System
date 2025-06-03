const fileInput = document.getElementById("ct_images");
const fileLabel = document.getElementById("fileLabel");

fileInput.addEventListener("change", () => {
  const files = Array.from(fileInput.files);
  if (files.length > 0) {
    const names = files.map(f => f.name).join(", ");
    fileLabel.textContent = names;
  } else {
    fileLabel.textContent = "No files selected";
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const patientSelect = document.getElementById("patientSelect");

  fetch("get_patients.php")
    .then((res) => res.text())
    .then((data) => {
      patientSelect.innerHTML = data;
    })
    .catch((err) => {
      patientSelect.innerHTML = '<option>Error loading patients</option>';
      console.error("Error fetching patients:", err);
    });
});
