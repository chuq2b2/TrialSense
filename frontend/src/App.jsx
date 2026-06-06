import { useState } from "react";
import { lookupTrial, matchPatients } from "./api/trials";
import MatchResults from "./components/MatchResults";
import TrialInputForm from "./components/TrialInputForm";
import TrialResult from "./components/TrialResult";
import logo from "./assets/logo.png";

function App() {
  const [trial, setTrial] = useState(null);
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState(null);
  const [matchError, setMatchError] = useState(null);

  async function handleLookup(input) {
    setLoading(true);
    setMatching(false);
    setError(null);
    setMatchError(null);
    setTrial(null);
    setMatches(null);

    let fetchedTrial = null;
    try {
      fetchedTrial = await lookupTrial(input);
      setTrial(fetchedTrial);
    } catch (err) {
      const message =
        err.response?.data?.detail ??
        "Something went wrong while fetching the trial.";
      setError(
        typeof message === "string" ? message : "Unable to fetch trial.",
      );
    } finally {
      setLoading(false);
    }

    if (!fetchedTrial) return;

    setMatching(true);
    try {
      const matchResult = await matchPatients(fetchedTrial);
      setMatches(matchResult);
    } catch (err) {
      const message =
        err.response?.data?.detail ??
        "Something went wrong while matching patients.";
      setMatchError(
        typeof message === "string" ? message : "Unable to match patients.",
      );
    } finally {
      setMatching(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-svh w-full max-w-3xl flex-col px-6 py-12 sm:px-8">
      <header className="mb-10 space-y-3 text-center align-center">
        <img src={logo} alt="Logo" className="w-auto h-30 mx-auto" />
        <h1 className="text-3xl font-medium tracking-tight sm:text-4xl">
          Enter a clinical trial and match patients
        </h1>
        <p className="mx-auto max-w-lg text-muted-foreground">
          Look up a study by NCT ID or ClinicalTrials.gov URL. Eligibility
          criteria are extracted automatically for patient matching.
        </p>
      </header>

      <main className="space-y-8">
        <TrialInputForm
          onSubmit={handleLookup}
          loading={loading}
          error={error}
        />
        {trial && <TrialResult key={trial.nct_id} trial={trial} />}
        {(matching || matches || matchError) && (
          <>
            {matchError && (
              <p className="text-sm text-destructive" role="alert">
                {matchError}
              </p>
            )}
            <MatchResults results={matches} loading={matching} />
          </>
        )}
      </main>
    </div>
  );
}

export default App;
