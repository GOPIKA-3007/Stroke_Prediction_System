document.addEventListener("DOMContentLoaded", function () {
    fetch("get_patient_data.php")
      .then((res) => res.json())
      .then((data) => {
        if (data.scan_image) {
          document.querySelector(".analysis-card img").src = data.scan_image;
          document.querySelector(".result-box").innerHTML = `
            <p><strong>Analysis Result:</strong> ${data.analysis_result}</p>
            <p><strong>Stroke Probability:</strong> ${data.stroke_probability}%</p>
            <p><strong>Model Confidence:</strong> ${data.model_confidence}</p>
          `;
  
          document.querySelector(".card:nth-of-type(2)").innerHTML = `
            <h3>Doctor's Notes</h3>
            <p><strong>Recommendations:</strong> ${data.recommendations}</p>
            <p><strong>Additional Notes:</strong> ${data.doctor_notes}</p>
          `;
        }
      });
  });
  