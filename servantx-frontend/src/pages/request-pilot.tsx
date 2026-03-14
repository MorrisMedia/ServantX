import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Check, ChevronLeft } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "wouter";
import * as z from "zod";

import { Footer } from "@/components/servantx/Footer";
import { Logo } from "@/components/servantx/Header";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { submitContactForm } from "@/lib/api";

const formSchema = z.object({
  // 1. Organization Information
  orgName: z.string().min(2, "Organization name is required"),
  state: z.string().min(2, "State/Region is required"),

  // 2. Contact Information
  contactName: z.string().min(2, "Contact name is required"),
  role: z.string({ required_error: "Please select a role" }),
  email: z.string().email("Invalid email address"),
  phone: z.string().optional(),

  // 3. Hospital Profile
  revenue: z.string({ required_error: "Please select annual revenue" }),
  hospitalType: z.array(z.string()).optional(),

  // 4. Pilot Interest & Scope
  interestAreas: z.array(z.string()).min(1, "Please select at least one area of interest"),
  payers: z.string().optional(),
  timeframe: z.string({ required_error: "Please select a timeframe" }),

  // 5. Governance & Readiness
  approval: z.string({ required_error: "Please select approval status" }),
  nextStep: z.string({ required_error: "Please select a preferred next step" }),

  // 6. Optional Context
  additionalInfo: z.string().optional(),
});

export default function RequestPilot() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      orgName: "",
      state: "",
      contactName: "",
      email: "",
      phone: "",
      hospitalType: [],
      interestAreas: [],
      payers: "",
      additionalInfo: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      await submitContactForm(values);
      setIsSubmitted(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      toast({
        title: "Submission Failed",
        description: error instanceof Error ? error.message : "Failed to submit your request. Please try again.",
        variant: "destructive",
      });
    }
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-[#F6F8FB] flex flex-col font-sans">
        <header className="w-full bg-white border-b border-border py-4">
          <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
            <Link href="/" className="cursor-pointer hover:opacity-90">
              <Logo />
            </Link>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center p-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-xl w-full bg-white rounded-lg shadow-sm border border-border p-12 text-center"
          >
            <div className="w-16 h-16 bg-servant-gradient rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-[#0B2A4A] mb-4">Thank you.</h1>
            <p className="text-lg text-muted-foreground mb-8">
              A member of the ServantX team will review your request and follow up with next steps.
            </p>
            <p className="text-sm text-muted-foreground bg-[#F6F8FB] p-4 rounded-md inline-block border border-border">
              This review is exploratory and does not obligate participation.
            </p>
            <div className="mt-8">
              <Link href="/" className="text-[#143A66] font-medium hover:underline">
                Return to Home
              </Link>
            </div>
          </motion.div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F8FB] flex flex-col font-sans text-[#0B2A4A]">
      {/* Simple Header */}
      <header className="w-full bg-white border-b border-border py-4 sticky top-0 z-50">
        <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-muted-foreground hover:text-[#0B2A4A] transition-colors text-sm font-medium"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <div className="opacity-50 pointer-events-none grayscale">
            <Logo />
          </div>
        </div>
      </header>

      <main className="flex-1 py-16 px-4 md:px-6">
        <div className="max-w-2xl mx-auto">
          {/* Page Header */}
          <div className="mb-12 text-center">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Request a Limited-Scope Pilot
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Evaluate ServantX Intelligence on a focused, contract-backed underpayment review — with no upfront cost.
            </p>
          </div>

          {/* Intro Copy */}
          <div className="bg-white rounded-lg border border-border p-6 mb-10 shadow-sm">
            <p className="text-muted-foreground leading-relaxed">
              This pilot is designed to validate whether deterministic underpayment recovery applies to your organization. Scope is limited, findings are auditable, and participation does not require changes to your billing workflows.
            </p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-12 bg-white p-8 md:p-10 rounded-xl border border-border shadow-sm">

              {/* 1. Organization Information */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">1. Organization Information</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="orgName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Hospital / Health System Name <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. Saint Jude Medical Center" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="state"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>State / Region <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. California" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* 2. Contact Information */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">2. Contact Information</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="contactName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Primary Contact Name <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="role"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Title / Role <span className="text-red-500">*</span></FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {["CFO", "VP Finance", "Revenue Integrity Director", "Revenue Cycle Leader", "Compliance", "Other"].map((role) => (
                              <SelectItem key={role} value={role}>{role}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Work Email Address <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <Input type="email" {...field} />
                        </FormControl>
                        <FormDescription>We do not use personal email addresses.</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="phone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Phone Number <span className="text-muted-foreground font-normal">(Optional)</span></FormLabel>
                        <FormControl>
                          <Input type="tel" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* 3. Hospital Profile */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">3. Hospital Profile</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="revenue"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Approximate Annual Net Patient Revenue <span className="text-red-500">*</span></FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select revenue range" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {["Under $20M", "$20M–$40M", "$40M–$75M", "$75M+"].map((rev) => (
                              <SelectItem key={rev} value={rev}>{rev}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="hospitalType"
                    render={() => (
                      <FormItem>
                        <FormLabel className="mb-4 block">Hospital Type <span className="text-muted-foreground font-normal">(Select all that apply)</span></FormLabel>
                        <div className="grid gap-3">
                          {["Rural", "Critical Access", "Community Hospital", "Regional Health System"].map((item) => (
                            <FormField
                              key={item}
                              control={form.control}
                              name="hospitalType"
                              render={({ field }) => {
                                return (
                                  <FormItem
                                    key={item}
                                    className="flex flex-row items-start space-x-3 space-y-0"
                                  >
                                    <FormControl>
                                      <Checkbox
                                        checked={field.value?.includes(item)}
                                        onCheckedChange={(checked) => {
                                          return checked
                                            ? field.onChange([...(field.value || []), item])
                                            : field.onChange(
                                              field.value?.filter(
                                                (value) => value !== item
                                              )
                                            )
                                        }}
                                      />
                                    </FormControl>
                                    <FormLabel className="font-normal cursor-pointer">
                                      {item}
                                    </FormLabel>
                                  </FormItem>
                                )
                              }}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* 4. Pilot Interest & Scope */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">4. Pilot Interest & Scope</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="interestAreas"
                    render={() => (
                      <FormItem>
                        <FormLabel className="mb-4 block">Primary Area of Interest <span className="text-red-500">*</span></FormLabel>
                        <div className="grid gap-3">
                          {[
                            "Outpatient facility claims",
                            "Modifier-related underpayments",
                            "Contract misapplication",
                            "Not sure (seeking assessment)"
                          ].map((item) => (
                            <FormField
                              key={item}
                              control={form.control}
                              name="interestAreas"
                              render={({ field }) => {
                                return (
                                  <FormItem
                                    key={item}
                                    className="flex flex-row items-start space-x-3 space-y-0"
                                  >
                                    <FormControl>
                                      <Checkbox
                                        checked={field.value?.includes(item)}
                                        onCheckedChange={(checked) => {
                                          return checked
                                            ? field.onChange([...field.value, item])
                                            : field.onChange(
                                              field.value?.filter(
                                                (value) => value !== item
                                              )
                                            )
                                        }}
                                      />
                                    </FormControl>
                                    <FormLabel className="font-normal cursor-pointer">
                                      {item}
                                    </FormLabel>
                                  </FormItem>
                                )
                              }}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="payers"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Primary Payer(s) of Interest <span className="text-muted-foreground font-normal">(Optional)</span></FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormDescription>e.g., commercial payer or dominant plan</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="timeframe"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Timeframe for Pilot Review <span className="text-red-500">*</span></FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select timeframe" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {["Last 90 days", "Last 180 days", "Open to recommendation"].map((opt) => (
                              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* 5. Governance & Readiness */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">5. Governance & Readiness</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="approval"
                    render={({ field }) => (
                      <FormItem className="space-y-3">
                        <FormLabel>Do you have internal approval to explore a limited-scope pilot? <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="flex flex-col space-y-1"
                          >
                            {["Yes", "Not yet", "In progress"].map((opt) => (
                              <FormItem key={opt} className="flex items-center space-x-3 space-y-0">
                                <FormControl>
                                  <RadioGroupItem value={opt} />
                                </FormControl>
                                <FormLabel className="font-normal cursor-pointer">
                                  {opt}
                                </FormLabel>
                              </FormItem>
                            ))}
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="nextStep"
                    render={({ field }) => (
                      <FormItem className="space-y-3">
                        <FormLabel>Preferred Next Step <span className="text-red-500">*</span></FormLabel>
                        <FormControl>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="flex flex-col space-y-1"
                          >
                            {["Introductory conversation", "Technical overview", "Written pilot outline"].map((opt) => (
                              <FormItem key={opt} className="flex items-center space-x-3 space-y-0">
                                <FormControl>
                                  <RadioGroupItem value={opt} />
                                </FormControl>
                                <FormLabel className="font-normal cursor-pointer">
                                  {opt}
                                </FormLabel>
                              </FormItem>
                            ))}
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* 6. Optional Context */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold border-b border-border pb-2">6. Optional Context</h2>
                <div className="grid gap-6">
                  <FormField
                    control={form.control}
                    name="additionalInfo"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Anything else we should know? <span className="text-muted-foreground font-normal">(Optional)</span></FormLabel>
                        <FormControl>
                          <Textarea className="min-h-[100px]" {...field} />
                        </FormControl>
                        <FormDescription>This may include payer behavior, prior audits, or internal priorities.</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* Submit Section */}
              <div className="pt-6 border-t border-border text-center space-y-4">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full md:w-auto px-8 bg-servant-gradient hover:opacity-90 transition-opacity text-white font-semibold text-lg h-14"
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting ? "Submitting..." : "Request Pilot Review"}
                </Button>

                <div className="text-sm text-muted-foreground space-y-1">
                  <p>No upfront cost. No obligation.</p>
                  <p>All findings are contract-backed and require your approval before any submission.</p>
                </div>
              </div>

            </form>
          </Form>
        </div>
      </main>

      <Footer />
    </div>
  );
}
