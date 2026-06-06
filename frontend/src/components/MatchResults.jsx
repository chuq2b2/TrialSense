import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

function bandVariant(band) {
  if (band === "Strong match") return "default";
  if (band === "Good match") return "secondary";
  if (band === "Possible match; review manually") return "outline";
  if (band === "Poor match") return "outline";
  return "destructive";
}

function percentColor(percent) {
  if (percent >= 90) return "text-emerald-600";
  if (percent >= 75) return "text-sky-600";
  if (percent >= 50) return "text-amber-600";
  if (percent > 0) return "text-orange-600";
  return "text-destructive";
}

export default function MatchResults({ results, loading }) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Matching patients…</CardTitle>
          <CardDescription>
            Extracting criteria, applying hard-rule pre-filters, and scoring
            patients.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!results) return null;

  const { matches, pool_size, prefilter_passed } = results;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranked patient matches</CardTitle>
        <CardDescription>
          HIPAA-masked results only. {prefilter_passed} of {pool_size} patients
          passed hard-rule pre-filtering
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {matches.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No patients passed pre-filtering for this trial.
          </p>
        ) : (
          matches.map((match, index) => (
            <div
              key={`${match.hospital_name}-${index}`}
              className="rounded-lg border p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Rank #{index + 1}
                  </p>
                  <p
                    className={cn(
                      "text-2xl font-semibold tabular-nums",
                      percentColor(match.match_percent),
                    )}
                  >
                    {match.match_percent}%
                  </p>
                  <Badge variant={bandVariant(match.match_band)}>
                    {match.match_band}
                  </Badge>
                </div>
                <div className="space-y-1 text-right text-sm">
                  <p className="font-medium">{match.hospital_name}</p>
                  <p className="text-muted-foreground">
                    PCP: {match.pcp_contact}
                  </p>
                </div>
              </div>
              {match.needs_manual_review && (
                <p className="mt-3 text-xs text-amber-700">
                  Needs manual review
                </p>
              )}
              {match.exclusion_reasons?.length > 0 && (
                <ul className="mt-3 list-disc space-y-1 pl-4 text-xs text-destructive">
                  {match.exclusion_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
