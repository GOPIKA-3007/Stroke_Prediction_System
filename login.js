document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
  
    const id = document.getElementById("id").value;
    const name = document.getElementById("name").value;
    const age = document.getElementById("age").value;
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const dob = document.getElementById("dob").value;
    const phone = document.getElementById("phone").value;
    const address = document.getElementById("address").value;
    const symptoms = document.getElementById("symptoms").value;
    const doctor = document.getElementById("doctor").value;
  
    alert(`Form submitted:\n\nID: ${id}\nName: ${name}\nAge: ${age}\nGender: ${gender}\nDOB: ${dob}\nPhone: ${phone}\nAddress: ${address}\nSymptoms: ${symptoms}\nDoctor: ${doctor}`);
  });
  