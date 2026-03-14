import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ContractUpload } from "@/components/contracts/ContractUpload";
import { ContractList } from "@/components/contracts/ContractList";
import { ChangePasswordForm } from "@/components/auth/ChangePasswordForm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { getHospital, updateHospital } from "@/lib/api/hospitals";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const hospitalSchema = z.object({
  name: z.string().min(2, "Hospital name is required"),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  phone: z.string().optional(),
  address: z.string().optional(),
  state: z.string().optional(),
});

type HospitalFormData = z.infer<typeof hospitalSchema>;

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: hospital, isLoading } = useQuery({
    queryKey: ["/hospitals/me"],
    queryFn: getHospital,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<HospitalFormData>({
    resolver: zodResolver(hospitalSchema),
    values: hospital
      ? {
          name: hospital.name,
          email: hospital.email || "",
          phone: hospital.phone || "",
          address: hospital.address || "",
          state: hospital.state || "",
        }
      : undefined,
  });

  const updateMutation = useMutation({
    mutationFn: updateHospital,
    onSuccess: () => {
      toast.success("Hospital settings updated successfully");
      queryClient.invalidateQueries({ queryKey: ["/hospitals/me"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update settings");
    },
  });

  const onSubmit = (data: HospitalFormData) => {
    updateMutation.mutate({
      name: data.name,
      email: data.email || undefined,
      phone: data.phone || undefined,
      address: data.address || undefined,
      state: data.state || undefined,
    });
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage your hospital profile and contracts
          </p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile">Hospital Profile</TabsTrigger>
            <TabsTrigger value="password">Change Password</TabsTrigger>
            <TabsTrigger value="contracts">Contracts</TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Hospital Information</CardTitle>
                <CardDescription>
                  Update your hospital details and contact information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Hospital Name *</Label>
                    <Input
                      id="name"
                      {...register("name")}
                      placeholder="General Hospital"
                    />
                    {errors.name && (
                      <p className="text-sm text-destructive">{errors.name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      {...register("email")}
                      placeholder="contact@hospital.com"
                    />
                    {errors.email && (
                      <p className="text-sm text-destructive">{errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      type="tel"
                      {...register("phone")}
                      placeholder="(555) 123-4567"
                    />
                    {errors.phone && (
                      <p className="text-sm text-destructive">{errors.phone.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      {...register("address")}
                      placeholder="123 Main St"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      {...register("state")}
                      placeholder="CA"
                    />
                  </div>

                  <Button type="submit" disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? "Saving..." : "Save Changes"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="password" className="space-y-6">
            <ChangePasswordForm />
          </TabsContent>

          <TabsContent value="contracts" className="space-y-6">
            <ContractUpload />
            <div>
              <h2 className="text-2xl font-semibold mb-4">Uploaded Contracts</h2>
              <ContractList />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

