import React, { useEffect, useCallback, useState } from "react";
import { Document, Page } from "react-pdf";
import PageLinkBtn from "components/PageLinkBtn";
import FileDropZone from "components/FileDropZone";
import { GridLoader } from "react-spinners";
import "pages/pageStyles.css";

const Home = () => {
  const fileUploadUrl = "http://localhost:8000/upload/file";
  const getTotalDollarUrl = "http://localhost:8000/total-requests";
  const [totalDollarSaved, setTotalDollarSaved] = useState("");
  const [file, setFile] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [isFilePicked, setIsFilePicked] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [responseReceived, setResponseReceived] = useState(false);

  useEffect(() => {
    const getTD = async () => {
      const response = await fetch(getTotalDollarUrl);
      const td = await response.json();
      console.log(td);
      setTotalDollarSaved(td);
    };
    getTD();
  }, []);

  const handleFileSubmission = async (event) => {
    setWaiting(true);
    const formData = new FormData();

    formData.append("file", file);
    formData.append("type", "application/pdf");

    console.dir(formData);
    // Post request to fastapi server to upload file
    const response = await fetch(fileUploadUrl, {
      method: "POST",
      body: formData,
    }).then((response) => {
      response.json();
      console.log(response);

      setWaiting(false);
      setResponseReceived(true);
    });
  };

  const handleReDo = () => {
    setResponseReceived(false);
  };

  const onDrop = useCallback((acceptedFiles) => {
    const currFile = acceptedFiles[0]; // Allow only one file upload
    console.dir(currFile);
    setFile(currFile);
    setIsFilePicked(true);

    return currFile;
  }, []);

  return (
    <section className="home">
      <div className="description">
        <h1>Unofficial Transcript Generator</h1>
        <h2>Upload your UBC SSC grade summary here</h2>
        <h2>
          Then this generator will parse your grade summary to good looking
          unofficial transcript with full course name
        </h2>
        <h3>
          So that reader can understand what you actually studied instead of
          some random abbreviation🫡
        </h3>
      </div>
      <section className="total-saved">
        <p className="total-saved-text">💵Total Student Money Saved:</p>
        <p className="total-saved-dollar">${totalDollarSaved}</p>
      </section>
      <section className="main">
        {!waiting && !responseReceived && (
          <>
            <PageLinkBtn pageName="User Guide" pageLink="/guide" />
            <div className="preview">
              {file != null && (
                <Document
                  file={file}
                  options={{ workerSrc: "pdf.worker.js" }}
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                >
                  {Array.apply(null, Array(numPages))
                    .map((x, i) => i + 1)
                    .map((page) => (
                      <Page pageNumber={page} />
                    ))}
                </Document>
              )}
            </div>
            <FileDropZone onDrop={onDrop} />
            <button className="submit-btn" onClick={handleFileSubmission}>
              🚀 Submit
            </button>
          </>
        )}
        {waiting && <GridLoader color="#002145" />}
        {responseReceived && (
          <button className="submit-btn" onClick={handleReDo}>
            🔄 Re-do
          </button>
        )}
      </section>
    </section>
  );
};

export default Home;
