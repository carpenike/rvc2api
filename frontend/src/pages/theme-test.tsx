import { AppLayout } from "@/components/app-layout";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useTheme } from "@/hooks/use-theme";
import {
    AlertTriangle,
    CheckCircle,
    Info,
    Lightbulb,
    Moon,
    Palette,
    Settings,
    Sun,
    XCircle
} from "lucide-react";
import { useState } from "react";

export default function ThemeTest() {
  const { theme, setTheme } = useTheme();
  const [demoProgress, setDemoProgress] = useState(65);
  const [demoSlider, setDemoSlider] = useState([50]);
  const [demoInput, setDemoInput] = useState("Sample text");
  const [demoCheckboxes, setDemoCheckboxes] = useState({
    option1: true,
    option2: false,
    option3: true,
  });
  const [demoRadio, setDemoRadio] = useState("option1");
  const [demoSwitch, setDemoSwitch] = useState(true);
  const [demoSelect, setDemoSelect] = useState("option1");

  const colorPalette = [
    { name: "Background", class: "bg-background", textClass: "text-background" },
    { name: "Foreground", class: "bg-foreground", textClass: "text-foreground" },
    { name: "Card", class: "bg-card", textClass: "text-card" },
    { name: "Card Foreground", class: "bg-card-foreground", textClass: "text-card-foreground" },
    { name: "Popover", class: "bg-popover", textClass: "text-popover" },
    { name: "Popover Foreground", class: "bg-popover-foreground", textClass: "text-popover-foreground" },
    { name: "Primary", class: "bg-primary", textClass: "text-primary" },
    { name: "Primary Foreground", class: "bg-primary-foreground", textClass: "text-primary-foreground" },
    { name: "Secondary", class: "bg-secondary", textClass: "text-secondary" },
    { name: "Secondary Foreground", class: "bg-secondary-foreground", textClass: "text-secondary-foreground" },
    { name: "Muted", class: "bg-muted", textClass: "text-muted" },
    { name: "Muted Foreground", class: "bg-muted-foreground", textClass: "text-muted-foreground" },
    { name: "Accent", class: "bg-accent", textClass: "text-accent" },
    { name: "Accent Foreground", class: "bg-accent-foreground", textClass: "text-accent-foreground" },
    { name: "Destructive", class: "bg-destructive", textClass: "text-destructive" },
    { name: "Destructive Foreground", class: "bg-destructive-foreground", textClass: "text-destructive-foreground" },
    { name: "Border", class: "bg-border", textClass: "text-border" },
    { name: "Input", class: "bg-input", textClass: "text-input" },
    { name: "Ring", class: "bg-ring", textClass: "text-ring" },
  ];

  return (
    <AppLayout>
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Theme Test</h1>
            <p className="text-muted-foreground">
              Test and preview all UI components with different theme configurations
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
              <span className="ml-2">
                Switch to {theme === "dark" ? "Light" : "Dark"}
              </span>
            </Button>
          </div>
        </div>

        <Tabs defaultValue="components" className="space-y-6">
          <TabsList>
            <TabsTrigger value="components">
              <Settings className="mr-2 h-4 w-4" />
              Components
            </TabsTrigger>
            <TabsTrigger value="colors">
              <Palette className="mr-2 h-4 w-4" />
              Colors
            </TabsTrigger>
            <TabsTrigger value="typography">
              <Lightbulb className="mr-2 h-4 w-4" />
              Typography
            </TabsTrigger>
          </TabsList>

          {/* Components Tab */}
          <TabsContent value="components" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Buttons */}
              <Card>
                <CardHeader>
                  <CardTitle>Buttons</CardTitle>
                  <CardDescription>
                    All button variants and states
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Button Variants</Label>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="default">Default</Button>
                      <Button variant="destructive">Destructive</Button>
                      <Button variant="outline">Outline</Button>
                      <Button variant="secondary">Secondary</Button>
                      <Button variant="ghost">Ghost</Button>
                      <Button variant="link">Link</Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Button Sizes</Label>
                    <div className="flex flex-wrap gap-2 items-center">
                      <Button size="sm">Small</Button>
                      <Button size="default">Default</Button>
                      <Button size="lg">Large</Button>
                      <Button size="icon">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Button States</Label>
                    <div className="flex flex-wrap gap-2">
                      <Button>Normal</Button>
                      <Button disabled>Disabled</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Form Controls */}
              <Card>
                <CardHeader>
                  <CardTitle>Form Controls</CardTitle>
                  <CardDescription>
                    Input fields, checkboxes, radio buttons, and switches
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="demo-input">Text Input</Label>
                    <Input
                      id="demo-input"
                      value={demoInput}
                      onChange={(e) => setDemoInput(e.target.value)}
                      placeholder="Enter text here..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Textarea</Label>
                    <Textarea placeholder="Enter longer text here..." rows={3} />
                  </div>

                  <div className="space-y-3">
                    <Label>Checkboxes</Label>
                    {Object.entries(demoCheckboxes).map(([key, checked]) => (
                      <div key={key} className="flex items-center space-x-2">
                        <Checkbox
                          id={key}
                          checked={checked}
                          onCheckedChange={(checked) =>
                            setDemoCheckboxes(prev => ({ ...prev, [key]: !!checked }))
                          }
                        />
                        <Label htmlFor={key}>Option {key.slice(-1)}</Label>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-3">
                    <Label>Radio Group</Label>
                    <RadioGroup value={demoRadio} onValueChange={setDemoRadio}>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="option1" id="r1" />
                        <Label htmlFor="r1">Option 1</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="option2" id="r2" />
                        <Label htmlFor="r2">Option 2</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="option3" id="r3" />
                        <Label htmlFor="r3">Option 3</Label>
                      </div>
                    </RadioGroup>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="demo-switch"
                      checked={demoSwitch}
                      onCheckedChange={setDemoSwitch}
                    />
                    <Label htmlFor="demo-switch">Toggle Switch</Label>
                  </div>

                  <div className="space-y-2">
                    <Label>Select</Label>
                    <Select value={demoSelect} onValueChange={setDemoSelect}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an option" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="option1">Option 1</SelectItem>
                        <SelectItem value="option2">Option 2</SelectItem>
                        <SelectItem value="option3">Option 3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Progress and Sliders */}
              <Card>
                <CardHeader>
                  <CardTitle>Progress & Sliders</CardTitle>
                  <CardDescription>
                    Progress bars and range sliders
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Label>Progress Bar</Label>
                      <span className="text-sm text-muted-foreground">{demoProgress}%</span>
                    </div>
                    <Progress value={demoProgress} className="w-full" />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDemoProgress(Math.random() * 100)}
                    >
                      Randomize
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Label>Slider</Label>
                      <span className="text-sm text-muted-foreground">{demoSlider[0]}</span>
                    </div>
                    <Slider
                      value={demoSlider}
                      onValueChange={setDemoSlider}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Badges and Loading */}
              <Card>
                <CardHeader>
                  <CardTitle>Badges & Loading</CardTitle>
                  <CardDescription>
                    Status badges and loading states
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Badge Variants</Label>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="default">Default</Badge>
                      <Badge variant="secondary">Secondary</Badge>
                      <Badge variant="destructive">Destructive</Badge>
                      <Badge variant="outline">Outline</Badge>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Log Badge Variants</Label>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="log-debug">Debug</Badge>
                      <Badge variant="log-info">Info</Badge>
                      <Badge variant="log-warning">Warning</Badge>
                      <Badge variant="log-error">Error</Badge>
                      <Badge variant="log-critical">Critical</Badge>
                      <Badge variant="log-notice">Notice</Badge>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Loading Skeletons</Label>
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-[250px]" />
                      <Skeleton className="h-4 w-[200px]" />
                      <Skeleton className="h-4 w-[150px]" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Alerts */}
            <Card>
              <CardHeader>
                <CardTitle>Alerts</CardTitle>
                <CardDescription>
                  Different alert types and styles
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertTitle>Information</AlertTitle>
                  <AlertDescription>
                    This is an informational alert with additional context.
                  </AlertDescription>
                </Alert>

                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>
                    This is an error alert indicating something went wrong.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle>Success</AlertTitle>
                  <AlertDescription>
                    This indicates a successful operation or positive outcome.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Warning</AlertTitle>
                  <AlertDescription>
                    This is a warning alert to draw attention to important information.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            {/* Table */}
            <Card>
              <CardHeader>
                <CardTitle>Table</CardTitle>
                <CardDescription>
                  Data table with various content types
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Light 1</TableCell>
                      <TableCell>
                        <Badge variant="default">Online</Badge>
                      </TableCell>
                      <TableCell>LED</TableCell>
                      <TableCell className="text-right">100%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Light 2</TableCell>
                      <TableCell>
                        <Badge variant="secondary">Offline</Badge>
                      </TableCell>
                      <TableCell>Incandescent</TableCell>
                      <TableCell className="text-right">0%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Tank 1</TableCell>
                      <TableCell>
                        <Badge variant="outline">Monitoring</Badge>
                      </TableCell>
                      <TableCell>Fresh Water</TableCell>
                      <TableCell className="text-right">75%</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Colors Tab */}
          <TabsContent value="colors" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Color Palette</CardTitle>
                <CardDescription>
                  Complete theme color palette with CSS custom properties
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {colorPalette.map((color) => (
                    <div
                      key={color.name}
                      className="space-y-2"
                    >
                      <div
                        className={`h-16 w-full rounded-lg border ${color.class} flex items-center justify-center`}
                      >
                        <span className={`text-xs font-medium ${
                          color.name.includes('Foreground') ? color.textClass :
                          color.name === 'Background' ? 'text-foreground' :
                          color.name === 'Foreground' ? 'text-background' :
                          'text-white mix-blend-difference'
                        }`}>
                          Sample
                        </span>
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium">{color.name}</p>
                        <code className="text-xs text-muted-foreground">
                          {color.class.replace('bg-', '')}
                        </code>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Theme Switching */}
            <Card>
              <CardHeader>
                <CardTitle>Theme Controls</CardTitle>
                <CardDescription>
                  Switch between light and dark themes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Current Theme</Label>
                    <p className="text-sm text-muted-foreground">
                      {theme === "dark" ? "Dark mode" : "Light mode"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={theme === "light" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("light")}
                    >
                      <Sun className="mr-2 h-4 w-4" />
                      Light
                    </Button>
                    <Button
                      variant={theme === "dark" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("dark")}
                    >
                      <Moon className="mr-2 h-4 w-4" />
                      Dark
                    </Button>
                    <Button
                      variant={theme === "system" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("system")}
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      System
                    </Button>
                  </div>
                </div>

                <Separator />

                <div className="text-sm text-muted-foreground">
                  <p>
                    The theme system uses CSS custom properties that automatically adapt
                    to light and dark modes. Colors are defined using HSL values for
                    better consistency and easier customization.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Typography Tab */}
          <TabsContent value="typography" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Typography Scale</CardTitle>
                <CardDescription>
                  Heading and text styles across different sizes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <h1 className="text-4xl font-bold">Heading 1 - Main Page Title</h1>
                  <h2 className="text-3xl font-bold">Heading 2 - Section Title</h2>
                  <h3 className="text-2xl font-bold">Heading 3 - Subsection</h3>
                  <h4 className="text-xl font-semibold">Heading 4 - Card Title</h4>
                  <h5 className="text-lg font-semibold">Heading 5 - Small Title</h5>
                  <h6 className="text-base font-semibold">Heading 6 - Micro Title</h6>
                </div>

                <Separator />

                <div className="space-y-3">
                  <p className="text-base">
                    This is regular body text (text-base). It should be easy to read and
                    have good contrast against the background. This is the most common
                    text size used throughout the interface.
                  </p>

                  <p className="text-sm text-muted-foreground">
                    This is small text (text-sm) with muted coloring. It's commonly used
                    for descriptions, captions, and secondary information.
                  </p>

                  <p className="text-xs text-muted-foreground">
                    This is extra small text (text-xs) for fine print, timestamps,
                    and minimal annotations.
                  </p>

                  <p className="text-lg">
                    This is large text (text-lg) for emphasis or important statements
                    that need to stand out from regular body text.
                  </p>
                </div>

                <Separator />

                <div className="space-y-3">
                  <p className="font-bold">Bold text for emphasis</p>
                  <p className="font-semibold">Semi-bold text for headings</p>
                  <p className="font-medium">Medium weight text</p>
                  <p className="font-normal">Normal weight text</p>
                  <p className="font-light">Light weight text</p>
                </div>

                <Separator />

                <div className="space-y-3">
                  <p className="font-mono text-sm bg-muted p-2 rounded">
                    This is monospace text used for code snippets and technical content.
                    It has fixed-width characters for better alignment.
                  </p>

                  <code className="bg-muted px-2 py-1 rounded text-sm font-mono">
                    inline code
                  </code>
                </div>
              </CardContent>
            </Card>

            {/* Text Colors */}
            <Card>
              <CardHeader>
                <CardTitle>Text Colors</CardTitle>
                <CardDescription>
                  Different text color utilities and their usage
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-foreground">Primary text (text-foreground)</p>
                  <p className="text-muted-foreground">Muted text (text-muted-foreground)</p>
                  <p className="text-primary">Primary colored text (text-primary)</p>
                  <p className="text-secondary-foreground">Secondary text (text-secondary-foreground)</p>
                  <p className="text-destructive">Destructive/error text (text-destructive)</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </div>
    </AppLayout>
  );
}
