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
  if (percent >= 70) return "text-emerald-600";
  if (percent >= 55) return "text-sky-600";
  if (percent >= 35) return "text-amber-600";
  if (percent > 0) return "text-orange-600";
  return "text-destructive";
}

function statusLabel(status) {
  if (status === "met") return "Met";
  if (status === "partial") return "Partially met";
  if (status === "unmet") return "Not met";
  return "Unverified";
}

function statusClass(status) {
  if (status === "met") return "text-emerald-700";
  if (status === "partial") return "text-sky-700";
  if (status === "unmet") return "text-destructive";
  return "text-muted-foreground";
}

function formatPhone(phone) {
  const digits = String(phone).replace(/\D/g, "");
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  return phone;
}

function formatLocation(patient) {
  if (patient?.city && patient?.state) {
    return `${patient.city}, ${patient.state}`;
  }
  return patient?.city || patient?.state || "Location unavailable";
}

function formatVitals(patient) {
  const parts = [];
  if (patient?.bmi != null) parts.push(`BMI ${patient.bmi}`);
  if (patient?.systolic_bp != null && patient?.diastolic_bp != null) {
    parts.push(`BP ${patient.systolic_bp}/${patient.diastolic_bp}`);
  }
  if (patient?.hba1c_pct != null) parts.push(`HbA1c ${patient.hba1c_pct}%`);
  if (patient?.glucose_mgdl != null)
    parts.push(`Glucose ${patient.glucose_mgdl}`);
  return parts.length > 0 ? parts.join(" · ") : null;
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

  const { matches } = results;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranked patient matches</CardTitle>
        <CardDescription>
          Authorized coordinator view with patient identifiers and clinical
          details.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {matches.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No patients passed pre-filtering for this trial.
          </p>
        ) : (
          matches.map((match, index) => {
            const patient = match.patient ?? {};
            const patientId = match.patient_id ?? patient.patient_id;
            const vitals = formatVitals(patient);

            return (
              <div
                key={`${patientId ?? match.hospital_name}-${index}`}
                className="rounded-lg border p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
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

                  <div className="min-w-0 flex-1 space-y-3 text-sm">
                    <div>
                      <p className="font-mono text-xs text-muted-foreground">
                        Patient ID: {patientId ?? "Unavailable"}
                      </p>
                    </div>

                    <dl className="grid gap-2 sm:grid-cols-2">
                      <div>
                        <dt className="text-xs text-muted-foreground">Age</dt>
                        <dd>{patient.age ?? "—"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground">Sex</dt>
                        <dd>{patient.gender ?? "—"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground">
                          Location
                        </dt>
                        <dd>{formatLocation(patient)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground">
                          Care site
                        </dt>
                        <dd>{match.hospital_name}</dd>
                      </div>
                      <div className="sm:col-span-2">
                        <dt className="text-xs text-muted-foreground">
                          Active conditions
                        </dt>
                        <dd>{patient.active_conditions ?? 0}</dd>
                      </div>
                      {vitals && (
                        <div className="sm:col-span-2">
                          <dt className="text-xs text-muted-foreground">
                            Vitals
                          </dt>
                          <dd>{vitals}</dd>
                        </div>
                      )}
                      {patient.conditions?.length > 0 && (
                        <div className="sm:col-span-2">
                          <dt className="mb-1 text-xs text-muted-foreground">
                            Conditions
                          </dt>
                          <dd className="space-y-1 text-xs leading-relaxed">
                            {patient.conditions.slice(0, 5).map((condition) => (
                              <p key={condition}>{condition}</p>
                            ))}
                            {patient.conditions.length > 5 && (
                              <p className="text-muted-foreground">
                                +{patient.conditions.length - 5} more
                              </p>
                            )}
                          </dd>
                        </div>
                      )}
                      {patient.medications?.length > 0 && (
                        <div className="sm:col-span-2">
                          <dt className="mb-1 text-xs text-muted-foreground">
                            Medications
                          </dt>
                          <dd className="space-y-1 text-xs leading-relaxed">
                            {patient.medications
                              .slice(0, 3)
                              .map((medication) => (
                                <p key={medication}>{medication}</p>
                              ))}
                            {patient.medications.length > 3 && (
                              <p className="text-muted-foreground">
                                +{patient.medications.length - 3} more
                              </p>
                            )}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </div>

                  <div className="flex flex-wrap justify-end gap-2">
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          View details
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
                        <AlertDialogHeader>
                          <AlertDialogTitle>Match details</AlertDialogTitle>
                          <AlertDialogDescription asChild>
                            <div className="space-y-4 text-left">
                              <p className="text-sm text-foreground">
                                Matched{" "}
                                <span className="font-semibold">
                                  {match.inclusion_summary?.met ?? 0}
                                </span>{" "}
                                of{" "}
                                <span className="font-semibold">
                                  {match.inclusion_summary?.total ?? 0}
                                </span>{" "}
                                inclusion criteria
                              </p>
                              <ul className="space-y-3">
                                {match.inclusion_summary?.criteria?.map(
                                  (criterion) => (
                                    <li
                                      key={criterion.description}
                                      className="rounded-md border p-3"
                                    >
                                      <p className="text-sm font-medium text-foreground">
                                        {criterion.description}
                                      </p>
                                      <p
                                        className={cn(
                                          "mt-1 text-xs font-medium",
                                          statusClass(criterion.status),
                                        )}
                                      >
                                        {statusLabel(criterion.status)}
                                      </p>
                                      {criterion.reason && (
                                        <p className="mt-1 text-xs text-muted-foreground">
                                          {criterion.reason}
                                        </p>
                                      )}
                                    </li>
                                  ),
                                )}
                              </ul>
                            </div>
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogAction>Close</AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
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
                                  Patient ID:
                                </span>{" "}
                                {patientId ?? "Unavailable"}
                              </p>
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
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
