import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Check, ChevronLeft, Mail, MessageSquare, Send } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "wouter";
import * as z from "zod";

import { Footer } from "@/components/servantx/Footer";
import { Logo } from "@/components/servantx/Header";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { submitGeneralContactForm } from "@/lib/api";


const contactSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  subject: z.string().min(2, "Subject must be at least 2 characters"),
  message: z.string().min(10, "Message must be at least 10 characters"),
});

type ContactFormData = z.infer<typeof contactSchema>;

export default function ContactPage() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { toast } = useToast();

  const form = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      name: "",
      email: "",
      subject: "",
      message: "",
    },
  });

  async function onSubmit(values: ContactFormData) {
    try {
      await submitGeneralContactForm(values);
      setIsSubmitted(true);
      form.reset();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      toast({
        title: "Submission Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to submit your message. Please try again.",
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
            <h1 className="text-3xl font-bold text-[#0B2A4A] mb-4">
              Thank you for contacting us!
            </h1>
            <p className="text-lg text-muted-foreground mb-8">
              We've received your message and will get back to you as soon as
              possible.
            </p>
            <div className="flex gap-4 justify-center">
              <Button asChild variant="outline">
                <Link href="/">Return to Home</Link>
              </Button>
              <Button
                onClick={() => setIsSubmitted(false)}
                className="bg-servant-gradient text-white"
              >
                Send Another Message
              </Button>
            </div>
          </motion.div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F8FB] flex flex-col font-sans text-[#0B2A4A]">
      {/* Header */}
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
            <div className="inline-flex items-center justify-center w-16 h-16 bg-servant-gradient rounded-full mb-6">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Contact Us
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Have a question or want to learn more? We'd love to hear from you.
            </p>
          </div>

          {/* Contact Form */}
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-6 bg-white p-8 md:p-10 rounded-xl border border-border shadow-sm"
            >
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Name <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Your name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Email <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="your.email@example.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Subject <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="What is this regarding?" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="message"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Message <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        className="min-h-[150px]"
                        placeholder="Tell us more about your inquiry..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="pt-4">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full md:w-auto px-8 bg-servant-gradient hover:opacity-90 transition-opacity text-white font-semibold"
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting ? (
                    "Sending..."
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Send Message
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>

          {/* Additional Contact Info */}
          <div className="mt-12 bg-white rounded-lg border border-border p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Other Ways to Reach Us</h2>
            <div className="space-y-3 text-muted-foreground">
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5" />
                <span>
                  For pilot requests, visit our{" "}
                  <Link href="/request-pilot" className="text-[#143A66] hover:underline font-medium">
                    Request a Pilot
                  </Link>{" "}
                  page
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}



