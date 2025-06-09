import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useMutation } from '@tanstack/react-query';
import { Key, Shield, Smartphone } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'sonner';

interface MFAVerificationProps {
  onSuccess: () => void;
  onCancel?: () => void;
  userId: string;
}

const MFAVerification: React.FC<MFAVerificationProps> = ({
  onSuccess,
  onCancel,
  userId: _userId,
}) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);

  // Verify MFA code mutation
  const verifyMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('/api/auth/mfa/verify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ totp_code: code }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Invalid verification code');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('MFA verification successful');
      onSuccess();
    },
    onError: (error: Error) => {
      toast.error(error.message);
      setVerificationCode('');
    },
  });

  const handleVerify = () => {
    if (!verificationCode.trim()) {
      toast.error('Please enter a verification code');
      return;
    }
    verifyMutation.mutate(verificationCode);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && verificationCode.trim()) {
      handleVerify();
    }
  };

  const toggleBackupCode = () => {
    setUseBackupCode(!useBackupCode);
    setVerificationCode('');
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2">
          <Shield className="h-5 w-5" />
          Two-Factor Authentication
        </CardTitle>
        <CardDescription>
          {useBackupCode
            ? 'Enter one of your backup codes'
            : 'Enter the 6-digit code from your authenticator app'
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="verification-code">
              {useBackupCode ? 'Backup Code' : 'Verification Code'}
            </Label>
            <Input
              id="verification-code"
              type="text"
              placeholder={useBackupCode ? 'Enter backup code' : '000000'}
              value={verificationCode}
              onChange={(e) => {
                const value = useBackupCode
                  ? e.target.value.toUpperCase()
                  : e.target.value.replace(/\D/g, '').slice(0, 6);
                setVerificationCode(value);
              }}
              onKeyPress={handleKeyPress}
              maxLength={useBackupCode ? 16 : 6}
              className={useBackupCode ? '' : 'text-center text-lg tracking-widest'}
              autoComplete="off"
            />
          </div>

          <Button
            onClick={handleVerify}
            disabled={
              verifyMutation.isPending ||
              !verificationCode.trim() ||
              (!useBackupCode && verificationCode.length !== 6)
            }
            className="w-full"
          >
            {verifyMutation.isPending ? 'Verifying...' : 'Verify'}
          </Button>
        </div>

        <Separator />

        <div className="space-y-4">
          <Button
            variant="outline"
            onClick={toggleBackupCode}
            className="w-full"
            disabled={verifyMutation.isPending}
          >
            {useBackupCode ? (
              <>
                <Smartphone className="h-4 w-4 mr-2" />
                Use Authenticator App
              </>
            ) : (
              <>
                <Key className="h-4 w-4 mr-2" />
                Use Backup Code
              </>
            )}
          </Button>

          {onCancel && (
            <Button
              variant="ghost"
              onClick={onCancel}
              className="w-full"
              disabled={verifyMutation.isPending}
            >
              Cancel
            </Button>
          )}
        </div>

        {!useBackupCode && (
          <Alert>
            <Smartphone className="h-4 w-4" />
            <AlertDescription>
              Open your authenticator app and enter the 6-digit code for your CoachIQ account.
            </AlertDescription>
          </Alert>
        )}

        {useBackupCode && (
          <Alert>
            <Key className="h-4 w-4" />
            <AlertDescription>
              Enter one of your 8-character backup codes. Each code can only be used once.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default MFAVerification;
