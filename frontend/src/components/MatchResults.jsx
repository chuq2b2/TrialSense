import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { cn } from "@/lib/utils";

const MATCHES_PER_PAGE = 5;

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

function exclusionStatusLabel(status) {
  if (status === "cleared") return "Cleared";
  if (status === "triggered") return "Excluded";
  return "Unverified";
}

function exclusionStatusClass(status) {
  if (status === "cleared") return "text-emerald-700";
  if (status === "triggered") return "text-destructive";
  return "text-muted-foreground";
}

function CriteriaList({ criteria, statusLabelFn, statusClassFn }) {
  if (!criteria?.length) {
    return (
      <p className="text-sm text-muted-foreground">No criteria to display.</p>
    );
  }

  return (
    <ul className="space-y-3">
      {criteria.map((criterion) => (
        <li key={criterion.description} className="rounded-md border p-3">
          <p className="text-sm font-medium text-foreground">
            {criterion.description}
          </p>
          <p
            className={cn(
              "mt-1 text-xs font-medium",
              statusClassFn(criterion.status),
            )}
          >
            {statusLabelFn(criterion.status)}
          </p>
          {criterion.reason && (
            <p className="mt-1 text-xs text-muted-foreground">
              {criterion.reason}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
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
  return patient?.city || patient?.state || "—";
}

function formatVitals(patient) {
  const parts = [];
  if (patient?.bmi != null) parts.push(`BMI ${patient.bmi}`);
  if (patient?.systolic_bp != null && patient?.diastolic_bp != null) {
    parts.push(`BP ${patient.systolic_bp}/${patient.diastolic_bp}`);
  }
  if (patient?.hba1c_pct != null) parts.push(`HbA1c ${patient.hba1c_pct}%`);
  if (patient?.glucose_mgdl != null)
    parts.push(`Glucose ${patient.glucose_mgdl} mg/dL`);
  if (patient?.cholesterol_mgdl != null) {
    parts.push(`Cholesterol ${patient.cholesterol_mgdl} mg/dL`);
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

function ViewDetailsDialog({ match }) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full sm:w-auto">
          View details
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <AlertDialogHeader>
          <AlertDialogTitle>Match details</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-6 text-left">
              <section className="space-y-3">
                <p className="text-sm font-medium text-foreground">
                  Inclusion criteria
                </p>
                <p className="text-sm text-foreground">
                  Matched{" "}
                  <span className="font-semibold">
                    {match.inclusion_summary?.met ?? 0}
                  </span>{" "}
                  of{" "}
                  <span className="font-semibold">
                    {match.inclusion_summary?.total ?? 0}
                  </span>
                </p>
                <CriteriaList
                  criteria={match.inclusion_summary?.criteria}
                  statusLabelFn={statusLabel}
                  statusClassFn={statusClass}
                />
              </section>
              <section className="space-y-3">
                <p className="text-sm font-medium text-foreground">
                  Exclusion criteria
                </p>
                <p className="text-sm text-foreground">
                  Cleared{" "}
                  <span className="font-semibold">
                    {match.exclusion_summary?.cleared ?? 0}
                  </span>{" "}
                  of{" "}
                  <span className="font-semibold">
                    {match.exclusion_summary?.total ?? 0}
                  </span>
                </p>
                <CriteriaList
                  criteria={match.exclusion_summary?.criteria}
                  statusLabelFn={exclusionStatusLabel}
                  statusClassFn={exclusionStatusClass}
                />
              </section>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogAction>Close</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function ContactPcpDialog({ match, patientId }) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full sm:w-auto">
          Contact PCP
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Primary care provider</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-left">
              <p>
                <span className="font-medium text-foreground">Patient ID:</span>{" "}
                {patientId ?? "Unavailable"}
              </p>
              <p>
                <span className="font-medium text-foreground">PCP:</span>{" "}
                {match.pcp_name ?? "PCP unavailable"}
              </p>
              <p>
                <span className="font-medium text-foreground">
                  Organization:
                </span>{" "}
                {match.hospital_name ?? "Organization unavailable"}
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
  );
}

function MatchResultCard({ match, index }) {
  const [open, setOpen] = useState(false);
  const patient = match.patient ?? {};
  const patientId = match.patient_id ?? patient.patient_id;
  const vitals = formatVitals(patient);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="rounded-lg border">
        <div className="flex flex-wrap items-start gap-4 p-4">
          <div className="flex flex-col gap-3">
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
              <Badge variant={bandVariant(match.match_band)} className="w-fit">
                {match.match_band}
              </Badge>
            </div>
            <div
              className="flex flex-col items-start gap-2"
              onClick={(event) => event.stopPropagation()}
              onKeyDown={(event) => event.stopPropagation()}
            >
              <ViewDetailsDialog match={match} />
              <ContactPcpDialog match={match} patientId={patientId} />
            </div>
          </div>

          <dl className="grid min-w-0 flex-1 gap-x-4 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-xs text-muted-foreground">Patient ID</dt>
              <dd className="font-mono text-xs break-all">
                {patientId ?? "Unavailable"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Age</dt>
              <dd>{patient.age ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Sex</dt>
              <dd>{patient.gender ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Location</dt>
              <dd>{formatLocation(patient)}</dd>
            </div>
            <div className="sm:col-span-2 lg:col-span-2">
              <dt className="text-xs text-muted-foreground">Care site</dt>
              <dd>{match.hospital_name}</dd>
            </div>
          </dl>
        </div>

        <CollapsibleTrigger className="flex w-full items-center justify-between border-t px-4 py-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/40 hover:text-foreground">
          Patient clinical details
          <ChevronDown
            className={cn(
              "size-4 shrink-0 transition-transform",
              open && "rotate-180",
            )}
          />
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 py-4 text-sm">
            <dl className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted-foreground">
                  Active conditions
                </dt>
                <dd>{patient.active_conditions ?? 0}</dd>
              </div>
              {vitals && (
                <div className="sm:col-span-2">
                  <dt className="text-xs text-muted-foreground">Vitals</dt>
                  <dd>{vitals}</dd>
                </div>
              )}
            </dl>

            {patient.conditions?.length > 0 && (
              <div>
                <p className="mb-2 text-xs text-muted-foreground">Conditions</p>
                <ul className="space-y-1 text-xs leading-relaxed">
                  {patient.conditions.map((condition) => (
                    <li key={condition}>{condition}</li>
                  ))}
                </ul>
              </div>
            )}

            {patient.medications?.length > 0 && (
              <div>
                <p className="mb-2 text-xs text-muted-foreground">
                  Medications
                </p>
                <ul className="space-y-1 text-xs leading-relaxed">
                  {patient.medications.map((medication) => (
                    <li key={medication}>{medication}</li>
                  ))}
                </ul>
              </div>
            )}

            {match.needs_manual_review && (
              <p className="text-xs text-amber-700">Needs manual review</p>
            )}
            {match.exclusion_reasons?.length > 0 && (
              <ul className="list-disc space-y-1 pl-4 text-xs text-destructive">
                {match.exclusion_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

function MatchResultsPagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  return (
    <Pagination className="mt-4">
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            href="#"
            className={cn(page <= 1 && "pointer-events-none opacity-50")}
            onClick={(event) => {
              event.preventDefault();
              onPageChange(Math.max(1, page - 1));
            }}
          />
        </PaginationItem>
        {Array.from({ length: totalPages }, (_, index) => index + 1).map(
          (pageNumber) => (
            <PaginationItem key={pageNumber}>
              <PaginationLink
                href="#"
                isActive={pageNumber === page}
                onClick={(event) => {
                  event.preventDefault();
                  onPageChange(pageNumber);
                }}
              >
                {pageNumber}
              </PaginationLink>
            </PaginationItem>
          ),
        )}
        <PaginationItem>
          <PaginationNext
            href="#"
            className={cn(
              page >= totalPages && "pointer-events-none opacity-50",
            )}
            onClick={(event) => {
              event.preventDefault();
              onPageChange(Math.min(totalPages, page + 1));
            }}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}

export default function MatchResults({ results, loading }) {
  const [page, setPage] = useState(1);
  const matches = results?.matches ?? [];
  const nctId = results?.nct_id;
  const totalPages = Math.max(1, Math.ceil(matches.length / MATCHES_PER_PAGE));

  useEffect(() => {
    setPage(1);
  }, [nctId, matches.length]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

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

  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * MATCHES_PER_PAGE;
  const paginatedMatches = matches.slice(
    pageStart,
    pageStart + MATCHES_PER_PAGE,
  );
  const rangeStart = matches.length === 0 ? 0 : pageStart + 1;
  const rangeEnd = Math.min(pageStart + MATCHES_PER_PAGE, matches.length);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranked patient matches</CardTitle>
        <CardDescription>
          {matches.length === 0
            ? "Authorized coordinator view with patient identifiers and clinical details."
            : `Showing ${rangeStart}–${rangeEnd} of ${matches.length} matches.`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {matches.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No patients passed pre-filtering for this trial.
          </p>
        ) : (
          <>
            {paginatedMatches.map((match, index) => (
              <MatchResultCard
                key={`${match.patient_id ?? match.hospital_name}-${pageStart + index}`}
                match={match}
                index={pageStart + index}
              />
            ))}
            <MatchResultsPagination
              page={safePage}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
