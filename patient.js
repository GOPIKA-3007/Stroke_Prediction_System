document.addEventListener("DOMContentLoaded", function () {
    fetch("/api/patient/scans", { credentials: 'include' })
      .then((res) => res.json())
      .then((scans) => {
        if (scans && scans.length > 0) {
          const scan = scans[0]; // Show latest scan
          document.querySelector(".analysis-card img").src = scan.image_path || "image-placeholder.jpg";
          document.querySelector(".result-box").innerHTML = `
            <p><strong>Analysis Result:</strong> ${scan.analysis_result || ''}</p>
            <p><strong>Stroke Probability:</strong> ${scan.stroke_probability || ''}%</p>
            <p><strong>Model Confidence:</strong> ${scan.model_confidence || ''}%</p>
          `;
          document.querySelector(".card:nth-of-type(2)").innerHTML = `
            <h3>Doctor's Notes</h3>
            <p><strong>Recommendations:</strong> ${scan.recommendations || ''}</p>
            <p><strong>Additional Notes:</strong> ${scan.doctor_notes || ''}</p>
          `;
        }
      });
  });
