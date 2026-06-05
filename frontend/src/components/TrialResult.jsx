function formatSex(sex) {
  if (!sex) return "Not specified";
  const labels = { ALL: "All", MALE: "Male", FEMALE: "Female" };
  return labels[sex] ?? sex;
}

function formatHealthyVolunteers(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "Not specified";
}

function formatAgeRange(minimumAge, maximumAge) {
  if (!minimumAge && !maximumAge) return "Not specified";
  if (minimumAge && maximumAge) return `${minimumAge} – ${maximumAge}`;
  return minimumAge ?? maximumAge;
}

function CriteriaBlock({ title, text }) {
  if (!text) return null;

  return (
    <section className="criteria-block">
      <h3>{title}</h3>
      <pre className="criteria-block__text">{text}</pre>
    </section>
  );
}

export default function TrialResult({ trial }) {
  const { eligibility } = trial;

  return (
    <article className="trial-result">
      <header className="trial-result__header">
        <p className="trial-result__nct">
          <a href={trial.ctgov_url} target="_blank" rel="noreferrer">
            {trial.nct_id}
          </a>
        </p>
        <h2>{trial.brief_title}</h2>
        {trial.official_title && trial.official_title !== trial.brief_title && (
          <p className="trial-result__official">{trial.official_title}</p>
        )}
        <div className="trial-result__meta">
          {trial.overall_status && (
            <span className="trial-result__badge">{trial.overall_status}</span>
          )}
          {trial.phases?.map((phase) => (
            <span key={phase} className="trial-result__badge">
              {phase.replace("_", " ")}
            </span>
          ))}
        </div>
        {trial.conditions?.length > 0 && (
          <p className="trial-result__conditions">
            {trial.conditions.join(" · ")}
          </p>
        )}
      </header>

      <section className="eligibility-summary">
        <h3>Eligibility overview</h3>
        <dl className="eligibility-summary__grid">
          <div>
            <dt>Age range</dt>
            <dd>
              {formatAgeRange(
                eligibility.minimum_age,
                eligibility.maximum_age,
              )}
            </dd>
          </div>
          <div>
            <dt>Sex</dt>
            <dd>{formatSex(eligibility.sex)}</dd>
          </div>
          <div>
            <dt>Healthy volunteers</dt>
            <dd>{formatHealthyVolunteers(eligibility.healthy_volunteers)}</dd>
          </div>
        </dl>
      </section>

      <CriteriaBlock
        title="Inclusion criteria"
        text={eligibility.inclusion_criteria}
      />
      <CriteriaBlock
        title="Exclusion criteria"
        text={eligibility.exclusion_criteria}
      />
    </article>
  );
}
