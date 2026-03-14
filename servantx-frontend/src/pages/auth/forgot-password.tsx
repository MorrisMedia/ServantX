import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import { Logo } from "@/components/servantx/Header";

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="flex justify-center">
          <Logo />
        </div>
        <ForgotPasswordForm />
      </div>
    </div>
  );
}



