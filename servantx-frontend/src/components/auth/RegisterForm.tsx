import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { register as registerUser } from "@/lib/api/auth";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const registerSchema = z
  .object({
    name: z.string().min(2, "Full name is required"),
    hospitalName: z.string().min(2, "Hospital name is required"),
    email: z.string().email("Please enter a valid email address"),
    phone: z.string().min(10, "Phone number is required"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const [, setLocation] = useLocation();
  const { login: setAuthUser } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const registerMutation = useMutation({
    mutationFn: async (data: RegisterFormData) => {
      console.log("🟡 [MUTATION] mutationFn called with:", data);
      try {
        console.log("🟡 [MUTATION] About to call registerUser function...");
        const result = await registerUser(data);
        console.log("🟡 [MUTATION] registerUser function returned:", result);
        return result;
      } catch (error) {
        console.error("🔴 [MUTATION] Error in mutationFn:", error);
        throw error;
      }
    },
    onSuccess: async (data) => {
      console.log("🟢 [MUTATION] onSuccess called with:", data);
      setAuthUser(data.user);
      toast.success("Registration successful! Please upload your contract to continue.");
      // Redirect to contracts page after registration
      setLocation("/dashboard/contracts");
    },
    onError: (err: Error) => {
      console.error("🔴 [MUTATION] onError called with:", err);
      console.error("🔴 [MUTATION] Error message:", err.message);
      console.error("🔴 [MUTATION] Error stack:", err.stack);
      setError(err.message || "Registration failed");
      toast.error(err.message || "Registration failed");
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    console.log("🟣 [FORM] Form submitted with data:", data);
    console.log("🟣 [FORM] Form data types:", {
      name: typeof data.name,
      hospitalName: typeof data.hospitalName,
      email: typeof data.email,
      phone: typeof data.phone,
      password: typeof data.password,
      confirmPassword: typeof data.confirmPassword,
    });
    setError(null);
    try {
      console.log("🟣 [FORM] Calling registerMutation.mutate...");
      registerMutation.mutate(data);
      console.log("🟣 [FORM] registerMutation.mutate called successfully");
    } catch (error) {
      console.error("🔴 [FORM] Error calling mutation:", error);
      setError(error instanceof Error ? error.message : "Failed to submit form");
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Register</CardTitle>
        <CardDescription>Create your hospital account</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">Full Name *</Label>
            <Input
              id="name"
              type="text"
              placeholder="John Doe"
              {...register("name")}
              disabled={isSubmitting}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="hospitalName">Hospital Name *</Label>
            <Input
              id="hospitalName"
              type="text"
              placeholder="General Hospital"
              {...register("hospitalName")}
              disabled={isSubmitting}
            />
            {errors.hospitalName && (
              <p className="text-sm text-destructive">{errors.hospitalName.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register("email")}
              disabled={isSubmitting}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone *</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="(555) 123-4567"
              {...register("phone")}
              disabled={isSubmitting}
            />
            {errors.phone && (
              <p className="text-sm text-destructive">{errors.phone.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password *</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              {...register("password")}
              disabled={isSubmitting}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password *</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              {...register("confirmPassword")}
              disabled={isSubmitting}
            />
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={isSubmitting || registerMutation.isPending}>
            {isSubmitting || registerMutation.isPending ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating account...
              </>
            ) : (
              "Register"
            )}
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-muted-foreground">Already have an account? </span>
          <button
            type="button"
            onClick={() => setLocation("/login")}
            className="text-primary hover:underline"
          >
            Login
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
