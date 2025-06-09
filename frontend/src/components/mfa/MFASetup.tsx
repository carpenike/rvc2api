import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, AlertTriangle, Copy, RefreshCw, Shield, Smartphone, Key } from 'lucide-react';
import { toast } from 'sonner';

interface MFAStatus {
  user_id: string;
  mfa_enabled: boolean;
  setup_initiated: boolean;
  created_at?: string;
  last_used?: string;
  backup_codes_remaining: number;
  backup_codes_total: number;
  available: boolean;
}

interface MFASetupData {
  secret: string;
  qr_code: string;
  provisioning_uri: string;
  backup_codes: string[];
  issuer: string;
}

interface BackupCodesResponse {
  backup_codes: string[];
  warning: string;
}

const MFASetup: React.FC = () => {
  const [totpCode, setTotpCode] = useState('');
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [setupData, setSetupData] = useState<MFASetupData | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  // Query MFA status
  const { data: mfaStatus, refetch: refetchStatus } = useQuery<MFAStatus>({
    queryKey: ['mfa-status'],
    queryFn: async () => {
      const response = await fetch('/api/auth/mfa/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch MFA status');
      }
      return response.json();
    },
  });

  // Setup MFA mutation
  const setupMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/auth/mfa/setup', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to setup MFA');
      }
      return response.json();
    },
    onSuccess: (data: MFASetupData) => {
      setSetupData(data);
      toast.success('MFA setup initiated. Scan the QR code with your authenticator app.');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Verify setup mutation
  const verifySetupMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('/api/auth/mfa/verify-setup', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ totp_code: code }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to verify MFA setup');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('MFA has been successfully enabled!');
      setShowBackupCodes(true);
      setBackupCodes(setupData?.backup_codes || []);
      refetchStatus();
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Disable MFA mutation
  const disableMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/auth/mfa/disable', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to disable MFA');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('MFA has been disabled');
      setSetupData(null);
      setTotpCode('');
      refetchStatus();
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Get backup codes mutation
  const getBackupCodesMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/auth/mfa/backup-codes', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get backup codes');
      }
      return response.json();
    },
    onSuccess: (data: BackupCodesResponse) => {
      setBackupCodes(data.backup_codes);
      setShowBackupCodes(true);
      toast.success('Backup codes retrieved');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Regenerate backup codes mutation
  const regenerateBackupCodesMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/auth/mfa/regenerate-backup-codes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to regenerate backup codes');
      }
      return response.json();
    },
    onSuccess: (data: BackupCodesResponse) => {
      setBackupCodes(data.backup_codes);
      setShowBackupCodes(true);
      toast.success('New backup codes generated');
      refetchStatus();
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const handleSetupMFA = () => {
    setupMutation.mutate();
  };

  const handleVerifySetup = () => {
    if (!totpCode.trim()) {
      toast.error('Please enter the verification code');
      return;
    }
    verifySetupMutation.mutate(totpCode);
  };

  const handleDisableMFA = () => {
    if (confirm('Are you sure you want to disable MFA? This will reduce your account security.')) {
      disableMutation.mutate();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const copyAllBackupCodes = () => {
    const allCodes = backupCodes.join('\n');
    navigator.clipboard.writeText(allCodes);
    toast.success('All backup codes copied to clipboard');
  };

  if (!mfaStatus?.available) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Multi-Factor Authentication
          </CardTitle>
          <CardDescription>
            MFA is not available on this system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Multi-factor authentication is not available. Please contact your administrator.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Multi-Factor Authentication
          </CardTitle>
          <CardDescription>
            Add an extra layer of security to your account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* MFA Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-medium">Status:</span>
              {mfaStatus?.mfa_enabled ? (
                <Badge variant="default" className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Enabled
                </Badge>
              ) : (
                <Badge variant="secondary">Disabled</Badge>
              )}
            </div>
            {mfaStatus?.mfa_enabled && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisableMFA}
                disabled={disableMutation.isPending}
              >
                Disable MFA
              </Button>
            )}
          </div>

          {mfaStatus?.mfa_enabled && (
            <div className="space-y-4">
              {/* MFA Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Backup codes remaining:</span>
                  <div className="mt-1">
                    {mfaStatus.backup_codes_remaining} of {mfaStatus.backup_codes_total}
                  </div>
                </div>
                {mfaStatus.last_used && (
                  <div>
                    <span className="font-medium">Last used:</span>
                    <div className="mt-1">
                      {new Date(mfaStatus.last_used).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>

              {/* Backup Codes Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => getBackupCodesMutation.mutate()}
                  disabled={getBackupCodesMutation.isPending}
                >
                  <Key className="h-4 w-4 mr-2" />
                  View Backup Codes
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => regenerateBackupCodesMutation.mutate()}
                  disabled={regenerateBackupCodesMutation.isPending}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate Codes
                </Button>
              </div>
            </div>
          )}

          {/* Setup MFA */}
          {!mfaStatus?.mfa_enabled && !setupData && (
            <div className="space-y-4">
              <Alert>
                <Smartphone className="h-4 w-4" />
                <AlertDescription>
                  MFA uses an authenticator app like Google Authenticator, Authy, or 1Password to generate time-based codes.
                </AlertDescription>
              </Alert>
              <Button
                onClick={handleSetupMFA}
                disabled={setupMutation.isPending}
                className="w-full"
              >
                {setupMutation.isPending ? 'Setting up...' : 'Set Up MFA'}
              </Button>
            </div>
          )}

          {/* QR Code and Verification */}
          {setupData && !mfaStatus?.mfa_enabled && (
            <div className="space-y-6">
              <div className="text-center space-y-4">
                <h3 className="font-medium">Scan QR Code</h3>
                <div className="flex justify-center">
                  <img
                    src={setupData.qr_code}
                    alt="MFA QR Code"
                    className="border rounded-lg"
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  Scan this QR code with your authenticator app, then enter the 6-digit code below.
                </p>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="totp-code">Verification Code</Label>
                  <Input
                    id="totp-code"
                    type="text"
                    placeholder="000000"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    maxLength={6}
                    className="text-center text-lg tracking-widest"
                  />
                </div>
                <Button
                  onClick={handleVerifySetup}
                  disabled={verifySetupMutation.isPending || totpCode.length !== 6}
                  className="w-full"
                >
                  {verifySetupMutation.isPending ? 'Verifying...' : 'Verify and Enable MFA'}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backup Codes Dialog */}
      <Dialog open={showBackupCodes} onOpenChange={setShowBackupCodes}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Backup Codes</DialogTitle>
            <DialogDescription>
              Save these backup codes in a secure location. You can use them to access your account if you lose your authenticator device.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                These codes will only be shown once. Make sure to save them securely.
              </AlertDescription>
            </Alert>
            <div className="grid grid-cols-2 gap-2 p-4 bg-muted rounded-lg font-mono text-sm">
              {backupCodes.map((code, index) => (
                <div key={index} className="flex items-center justify-between p-2 hover:bg-background rounded">
                  <span>{code}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(code)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={copyAllBackupCodes} className="flex-1">
                <Copy className="h-4 w-4 mr-2" />
                Copy All
              </Button>
              <Button onClick={() => setShowBackupCodes(false)} className="flex-1">
                Done
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default MFASetup;
