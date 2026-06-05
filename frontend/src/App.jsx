import { useState } from "react";
import { lookupTrial } from "./api/trials";
import TrialInputForm from "./components/TrialInputForm";
import TrialResult from "./components/TrialResult";
import "./App.css";

function App() {
  const [trial, setTrial] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLookup(input) {
    setLoading(true);
    setError(null);
    setTrial(null);

    try {
      const result = await lookupTrial(input);
      setTrial(result);
    } catch (err) {
      const message =
        err.response?.data?.detail ??
        "Something went wrong while fetching the trial.";
      setError(typeof message === "string" ? message : "Unable to fetch trial.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <p className="app__eyebrow">TrialSense</p>
        <h1>Enter a clinical trial</h1>
        <p className="app__subtitle">
          Look up a study by NCT ID or ClinicalTrials.gov URL. Eligibility
          criteria are extracted automatically for patient matching.
        </p>
      </header>

      <main className="app__main">
        <TrialInputForm
          onSubmit={handleLookup}
          loading={loading}
          error={error}
        />
        {trial && <TrialResult trial={trial} />}
      </main>
    </div>
  );
}

export default App;
