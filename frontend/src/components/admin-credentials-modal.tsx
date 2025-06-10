import { useState } from "react"
import { IconCopy, IconEye, IconEyeOff, IconKey, IconLoader2 } from "@tabler/icons-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts"

interface AdminCredentialsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AdminCredentialsModal({
  open,
  onOpenChange,
}: AdminCredentialsModalProps) {
  const { getAdminCredentials } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [credentials, setCredentials] = useState<{
    username: string
    password: string
    created_at: string
    warning: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const handleRetrieveCredentials = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const creds = await getAdminCredentials()
      setCredentials(creds)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retrieve credentials")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyToClipboard = async (value: string, field: string) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopiedField(field)
      setTimeout(() => setCopiedField(null), 2000)
    } catch (err) {
      console.error("Failed to copy to clipboard:", err)
    }
  }

  const handleClose = () => {
    // Clear sensitive data when closing
    setCredentials(null)
    setError(null)
    setShowPassword(false)
    setCopiedField(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconKey className="h-5 w-5" />
            Auto-Generated Admin Credentials
          </DialogTitle>
          <DialogDescription>
            These credentials are displayed only once for security. Save them immediately.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!credentials && !error && (
            <div className="space-y-4">
              <Alert>
                <IconKey className="h-4 w-4" />
                <AlertDescription>
                  Click the button below to retrieve your auto-generated admin credentials.
                  These will only be shown once for security reasons.
                </AlertDescription>
              </Alert>

              <Button
                onClick={() => void handleRetrieveCredentials()}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading && <IconLoader2 className="mr-2 h-4 w-4 animate-spin" />}
                Retrieve Credentials
              </Button>
            </div>
          )}

          {credentials && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertDescription>{credentials.warning}</AlertDescription>
              </Alert>

              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="cred-username">Username</Label>
                  <div className="flex gap-2">
                    <Input
                      id="cred-username"
                      value={credentials.username}
                      readOnly
                      className="font-mono"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void handleCopyToClipboard(credentials.username, "username")}
                    >
                      <IconCopy className="h-4 w-4" />
                      {copiedField === "username" ? "Copied!" : "Copy"}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cred-password">Password</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        id="cred-password"
                        type={showPassword ? "text" : "password"}
                        value={credentials.password}
                        readOnly
                        className="font-mono pr-10"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
                      >
                        {showPassword ? (
                          <IconEyeOff className="h-4 w-4" />
                        ) : (
                          <IconEye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void handleCopyToClipboard(credentials.password, "password")}
                    >
                      <IconCopy className="h-4 w-4" />
                      {copiedField === "password" ? "Copied!" : "Copy"}
                    </Button>
                  </div>
                </div>

                <div className="text-xs text-muted-foreground">
                  Generated: {new Date(credentials.created_at).toLocaleString()}
                </div>
              </div>

              <Alert>
                <AlertDescription>
                  <strong>Important:</strong> Save these credentials in a secure location immediately.
                  They will not be displayed again after closing this dialog.
                </AlertDescription>
              </Alert>

              <Button onClick={handleClose} className="w-full">
                I've Saved the Credentials
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
