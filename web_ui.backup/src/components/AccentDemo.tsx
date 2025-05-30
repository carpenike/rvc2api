import { useTheme } from "@/hooks/useTheme";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AccentDemo() {
  const { accent } = useTheme(); // just to prove re-render works

  return (
    <Card>
      <CardHeader>
        <CardTitle>Accent demo</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* shadcn button uses bg-primary / text-primary-foreground */}
        <Button className="w-full">Primary button</Button>

        {/* ring-primary shows focus colour */}
        <input
          placeholder="Input with primary ring"
          className="w-full rounded-md border px-3 py-2 ring-offset-background
                     focus-visible:outline-none focus-visible:ring-2
                     focus-visible:ring-ring focus-visible:ring-offset-2"
        />

        {/* progress bar coloured via bg-primary */}
        <div className="h-2 w-full overflow-hidden rounded bg-muted">
          <div className="h-full w-2/3 bg-primary" />
        </div>

        <p className="text-sm text-muted-foreground">
          Current accent: <span className="font-medium text-primary">{accent}</span>
        </p>
      </CardContent>
    </Card>
  );
}
