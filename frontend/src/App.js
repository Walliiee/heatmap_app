import React, { useState } from "react";
import Plot from 'react-plotly.js';

function App() {
  const [selectedYear, setSelectedYear] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files.length) return;

    const formData = new FormData();
    const fileArray = Array.from(files);
    fileArray.forEach((file) => {
      formData.append("files", file);
    });

    setUploadedFiles(fileArray);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/heatmap", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        return;
      }

      const data = await response.json();
      setHeatmapData(data);

    } catch (error) {
      console.error("Error generating heatmap:", error);
    }
  };

  const handleYearChange = async (event) => {
    const year = parseInt(event.target.value);
    setSelectedYear(year);
    await updateHeatmap(year);
  };

  const updateHeatmap = async (year) => {
    if (uploadedFiles.length === 0) {
      console.error("No files uploaded to update heatmap.");
      return;
    }

    const formData = new FormData();
    uploadedFiles.forEach((file) => {
      formData.append("files", file);
    });
    formData.append("year", year);

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/heatmap?year=${year}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error on year update:", errorData);
        return;
      }

      const data = await response.json();
      setHeatmapData(data);

    } catch (error) {
      console.error("Error updating heatmap:", error);
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>React + FastAPI</h1>
      
      <label htmlFor="file-upload" style={{ display: "block", marginBottom: "10px" }}>
        Upload JSON Files
      </label>
      <input
        type="file"
        id="file-upload"
        onChange={handleFileUpload}
        aria-label="Upload JSON files to generate a heatmap"
        multiple
      />

      <div style={{ margin: "20px 0" }}>
        <label htmlFor="year-select">Select Year: </label>
        <select id="year-select" onChange={handleYearChange} value={selectedYear || ""}>
          <option value="" disabled>Select a year</option>
          <option value="2022">2022</option>
          <option value="2023">2023</option>
          <option value="2024">2024</option>
          <option value="2025">2025</option>
        </select>
      </div>

      {heatmapData && (
        <Plot
          data={[
            {
              x: heatmapData.months,
              y: heatmapData.y,
              z: heatmapData.z,
              type: 'heatmap',
              colorscale: 'Viridis',
            },
          ]}
          layout={{ title: `Heatmap for ${selectedYear || 'all years'}` }}
        />
      )}
    </div>
  );
}

export default App;
