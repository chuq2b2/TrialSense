import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function TrialInputForm({ onSubmit, loading, error }) {
  const [input, setInput] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(input.trim());
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Look up a trial</CardTitle>
        <CardDescription>
          Paste an NCT ID or full CT.gov study URL. Eligibility criteria will be
          extracted automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <div className="flex flex-col gap-3 sm:flex-row">
              <Input
                id="trial-input"
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="NCT05123456 or https://clinicaltrials.gov/study/NCT05123456"
                disabled={loading}
                autoComplete="off"
                spellCheck={false}
              />
              <Button
                type="submit"
                size="lg"
                disabled={loading || !input.trim()}
                className="shrink-0"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" />
                    Fetching…
                  </>
                ) : (
                  "Fetch trial"
                )}
              </Button>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
