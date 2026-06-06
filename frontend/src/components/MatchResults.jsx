import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
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

function formatPhone(phone) {
  const digits = String(phone).replace(/\D/g, "");
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  return phone;
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
        <CardDescription>HIPAA-masked results only.</CardDescription>
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
                <div className="space-y-2 text-right text-sm">
                  <p className="font-medium">{match.hospital_name}</p>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        Contact PCP
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>
                          Primary care provider
                        </AlertDialogTitle>
                        <AlertDialogDescription asChild>
                          <div className="space-y-2 text-left">
                            <p>
                              <span className="font-medium text-foreground">
                                PCP:
                              </span>{" "}
                              {match.pcp_name ?? "PCP unavailable"}
                            </p>
                            <p>
                              <span className="font-medium text-foreground">
                                Organization:
                              </span>{" "}
                              {match.hospital_name ??
                                "Organization unavailable"}
                            </p>
                            <p>
                              <span className="font-medium text-foreground">
                                Organization phone:
                              </span>{" "}
                              {formatPhone(
                                match.organization_phone ??
                                  match.pcp_contact ??
                                  "Contact unavailable",
                              )}
                            </p>
                          </div>
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogAction>Close</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
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
