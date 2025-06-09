import { useState } from "react"
import { AppLayout } from "@/components/app-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { IconUser, IconShield, IconKey, IconEdit } from "@tabler/icons-react"
import { useAuth } from "@/contexts"

export default function ProfilePage() {
  const { user, authStatus } = useAuth()
  const [isEditing, setIsEditing] = useState(false)

  if (!user) {
    return (
      <AppLayout pageTitle="Profile">
        <div className="flex items-center justify-center min-h-[50vh]">
          <p>Please log in to view your profile.</p>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout pageTitle="Profile">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
            <p className="text-muted-foreground">Manage your account settings and preferences</p>
          </div>
          <Button
            variant="outline"
            onClick={() => setIsEditing(!isEditing)}
            disabled={authStatus?.mode === "none"}
          >
            <IconEdit className="mr-2 h-4 w-4" />
            {isEditing ? "Cancel" : "Edit Profile"}
          </Button>
        </div>

        <div className="grid gap-6 max-w-2xl">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconUser className="h-5 w-5" />
              Basic Information
            </CardTitle>
            <CardDescription>
              Your account details and authentication information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={user.username || ""}
                  disabled={!isEditing}
                  placeholder="Enter username"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={user.email || ""}
                  disabled={!isEditing}
                  placeholder="Enter email address"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-id">User ID</Label>
              <Input
                id="user-id"
                value={user.user_id || ""}
                disabled
                className="bg-muted"
              />
            </div>
          </CardContent>
        </Card>

        {/* Account Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconShield className="h-5 w-5" />
              Account Details
            </CardTitle>
            <CardDescription>
              Account status and authentication mode
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Role</span>
              <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                {user.role}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Authentication Mode</span>
              <Badge variant="outline">
                {authStatus?.mode === 'none' && 'Disabled'}
                {authStatus?.mode === 'single' && 'Single User'}
                {authStatus?.mode === 'multi' && 'Multi User'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Account Status</span>
              <Badge variant={user.authenticated ? 'default' : 'destructive'}>
                {user.authenticated ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        {authStatus?.mode !== 'none' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <IconKey className="h-5 w-5" />
                Security Settings
              </CardTitle>
              <CardDescription>
                Manage your password and security preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Change Password</p>
                  <p className="text-sm text-muted-foreground">
                    Update your account password
                  </p>
                </div>
                <Button variant="outline" disabled>
                  Change Password
                </Button>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Two-Factor Authentication</p>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security to your account
                  </p>
                </div>
                <Button variant="outline" disabled>
                  Configure MFA
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        {isEditing && (
          <div className="flex gap-3">
            <Button onClick={() => setIsEditing(false)}>
              Save Changes
            </Button>
            <Button variant="outline" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
        )}
        </div>
      </div>
    </AppLayout>
  )
}
