import React, { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [heatmapImage, setHeatmapImage] = useState(null);

  useEffect(() => {
    // Fetch data from the FastAPI backend to confirm it's running
    fetch("http://127.0.0.1:8000/")
      .then((response) => response.json())
      .then((data) => setMessage(data.message))
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      // POST to the /api/heatmap route
      const response = await fetch("http://127.0.0.1:8000/api/heatmap", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        return;
      }

      // Convert the response to a Blob (PNG image)
      const imageBlob = await response.blob();
      const imageObjectURL = URL.createObjectURL(imageBlob);

      setHeatmapImage(imageObjectURL);
    } catch (error) {
      console.error("Error generating heatmap:", error);
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>React + FastAPI</h1>
      <p>{message || "Loading..."}</p>
  
      {/* Add a label for accessibility */}
      <label htmlFor="file-upload" style={{ display: "block", marginBottom: "10px" }}>
        Upload a JSON File
      </label>
      <input
        type="file"
        id="file-upload"
        onChange={handleFileUpload}
        aria-label="Upload a JSON file to generate a heatmap"
      />
  
      {/* Render heatmap if available */}
      {heatmapImage && (
        <div>
          <h2>Generated Heatmap</h2>
          <img src={heatmapImage} alt="Heatmap" style={{ maxWidth: "600px" }} />
        </div>
      )}
    </div>
  );
}

export default App;
