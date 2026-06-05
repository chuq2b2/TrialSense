import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

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
    <section className="space-y-2">
      <h3 className="text-sm font-medium">{title}</h3>
      <pre className="rounded-lg bg-muted p-4 text-sm leading-relaxed whitespace-pre-wrap wrap-break-word text-foreground">
        {text}
      </pre>
    </section>
  );
}

function EligibilityItem({ label, value }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}

export default function TrialResult({ trial }) {
  const { eligibility } = trial;

  return (
    <Card>
      <CardHeader className="border-b">
        <a
          href={trial.ctgov_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex w-fit items-center gap-1 font-mono text-sm text-primary hover:underline"
        >
          {trial.nct_id}
          <ExternalLink className="size-3.5" />
        </a>
        <CardTitle className="text-xl leading-snug">{trial.brief_title}</CardTitle>
        {trial.official_title && trial.official_title !== trial.brief_title && (
          <CardDescription>{trial.official_title}</CardDescription>
        )}
        <div className="flex flex-wrap gap-2 pt-1">
          {trial.overall_status && (
            <Badge variant="secondary">{trial.overall_status}</Badge>
          )}
          {trial.phases?.map((phase) => (
            <Badge key={phase} variant="outline">
              {phase.replace("_", " ")}
            </Badge>
          ))}
        </div>
        {trial.conditions?.length > 0 && (
          <CardDescription className="pt-1">
            {trial.conditions.join(" · ")}
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        <section className="space-y-3">
          <h3 className="text-sm font-medium">Eligibility overview</h3>
          <dl className="grid gap-4 sm:grid-cols-3">
            <EligibilityItem
              label="Age range"
              value={formatAgeRange(
                eligibility.minimum_age,
                eligibility.maximum_age,
              )}
            />
            <EligibilityItem label="Sex" value={formatSex(eligibility.sex)} />
            <EligibilityItem
              label="Healthy volunteers"
              value={formatHealthyVolunteers(eligibility.healthy_volunteers)}
            />
          </dl>
        </section>

        <Separator />

        <CriteriaBlock
          title="Inclusion criteria"
          text={eligibility.inclusion_criteria}
        />
        <CriteriaBlock
          title="Exclusion criteria"
          text={eligibility.exclusion_criteria}
        />
      </CardContent>
    </Card>
  );
}
