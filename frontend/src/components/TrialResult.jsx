import { useState } from "react";
import { ChevronDown, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

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

function CriteriaBlock({ title, text, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  if (!text) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg py-2 text-sm font-medium transition-colors hover:text-primary">
        {title}
        <ChevronDown
          className={cn(
            "size-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-2">
        <pre className="rounded-lg bg-muted p-4 text-sm leading-relaxed whitespace-pre-wrap wrap-break-word text-foreground">
          {text}
        </pre>
      </CollapsibleContent>
    </Collapsible>
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
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full cursor-pointer text-left outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <CardHeader className="border-b pb-6">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-2">
                  <a
                    href={trial.ctgov_url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(event) => event.stopPropagation()}
                    className="inline-flex w-fit items-center gap-1 font-mono text-sm text-primary hover:underline"
                  >
                    {trial.nct_id}
                    <ExternalLink className="size-3.5" />
                  </a>
                  <CardTitle className="text-xl leading-snug">
                    {trial.brief_title}
                  </CardTitle>
                  {trial.official_title &&
                    trial.official_title !== trial.brief_title && (
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
                </div>
                <ChevronDown
                  className={cn(
                    "mt-1 size-5 shrink-0 text-muted-foreground transition-transform",
                    open && "rotate-180",
                  )}
                />
              </div>
            </CardHeader>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-6 pt-8">
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
                <EligibilityItem
                  label="Sex"
                  value={formatSex(eligibility.sex)}
                />
                <EligibilityItem
                  label="Healthy volunteers"
                  value={formatHealthyVolunteers(
                    eligibility.healthy_volunteers,
                  )}
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
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
