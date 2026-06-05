import { useState } from "react";

export default function TrialInputForm({ onSubmit, loading, error }) {
  const [input, setInput] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(input.trim());
  }

  return (
    <form className="trial-form" onSubmit={handleSubmit}>
      <label className="trial-form__label" htmlFor="trial-input">
        NCT ID or ClinicalTrials.gov URL
      </label>
      <div className="trial-form__row">
        <input
          id="trial-input"
          className="trial-form__input"
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="NCT05123456 or https://clinicaltrials.gov/study/NCT05123456"
          disabled={loading}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          className="trial-form__button"
          type="submit"
          disabled={loading || !input.trim()}
        >
          {loading ? "Fetching…" : "Fetch trial"}
        </button>
      </div>
      <p className="trial-form__hint">
        Paste an NCT ID or full CT.gov study URL. Eligibility criteria will be
        extracted automatically.
      </p>
      {error && (
        <p className="trial-form__error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
