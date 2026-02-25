"use client";

import { ArrowRight, Bot, MessageSquare, BarChart3, CheckCircle2, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { createClient } from "@supabase/supabase-js";

// Initialize Supabase. Note: You will need these env vars in your .env.local
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder-project.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder-key";
const supabase = createClient(supabaseUrl, supabaseAnonKey);

export default function Home() {
  const [isWaitlistOpen, setIsWaitlistOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [feedback, setFeedback] = useState("");
  const [step, setStep] = useState<'email' | 'feedback' | 'success' | 'combined'>('email');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const openWaitlist = (e: React.MouseEvent) => {
    e.preventDefault();
    setStep('email');
    setIsWaitlistOpen(true);
  };

  const openFeedback = (e: React.MouseEvent) => {
    e.preventDefault();
    setStep('combined');
    setIsWaitlistOpen(true);
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      if (supabaseUrl === "https://placeholder-project.supabase.co") {
        throw new Error("Missing Supabase configuration. Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to your .env file.");
      }

      // 1. Send email to Supabase waitlist table
      const { error } = await supabase
        .from("waitlist")
        .insert([{ email }]);

      // NOTE: We don't care about a unique constraint violation (code 23505),
      // we still let them proceed to give feedback.
      if (error && error.code !== '23505') {
        setErrorMsg(error.message || "Failed to join waitlist. Please check your connection.");
        setIsSubmitting(false);
        return;
      }

      // Move to feedback step
      setStep('feedback');
    } catch (err: any) {
      console.error("Waitlist error:", err);
      setErrorMsg(err?.message || "An unexpected error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      if (feedback.trim()) {
        const { error } = await supabase
          .from("waitlist")
          .update({ feedback })
          .eq('email', email);

        if (error) {
          console.error("Failed to save feedback", error);
        }
      }

      showSuccessAndClose();
    } catch (err: any) {
      console.error("Feedback error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCombinedSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      if (supabaseUrl === "https://placeholder-project.supabase.co") {
        throw new Error("Missing Supabase configuration. Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to your .env file.");
      }

      // Try insert first
      const { error: insertError } = await supabase
        .from("waitlist")
        .insert([{ email, feedback: feedback || null }]);

      if (insertError) {
        if (insertError.code === '23505') {
          // Already exists, just update feedback
          if (feedback.trim()) {
            const { error: updateError } = await supabase
              .from("waitlist")
              .update({ feedback })
              .eq('email', email);

            if (updateError) throw updateError;
          }
        } else {
          throw insertError;
        }
      }

      showSuccessAndClose();
    } catch (err: any) {
      console.error("Waitlist error:", err);
      setErrorMsg(err?.message || "An unexpected error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const skipFeedback = () => {
    showSuccessAndClose();
  };

  const showSuccessAndClose = () => {
    setStep('success');
    setTimeout(() => {
      setIsWaitlistOpen(false);
      setStep('email');
      setEmail("");
      setFeedback("");
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      {/* Waitlist Modal */}
      {isWaitlistOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setIsWaitlistOpen(false)}
          />
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/50 rounded-2xl shadow-2xl shadow-indigo-500/10 overflow-hidden">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-slate-800">
              <h3 className="text-xl font-bold">Join the Waitlist</h3>
              <button
                onClick={() => setIsWaitlistOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              {step === 'success' ? (
                <div className="text-center py-8 animate-in fade-in duration-300">
                  <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 animate-in zoom-in duration-300 delay-150">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <h4 className="text-lg font-semibold mb-2">You're on the list!</h4>
                  <p className="text-slate-400">We'll notify you as soon as a spot opens up.</p>
                </div>
              ) : step === 'combined' ? (
                <form onSubmit={handleCombinedSubmit} className="space-y-4 animate-in slide-in-from-bottom duration-300 fade-in">
                  <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 mb-4">
                      <MessageSquare className="w-6 h-6" />
                    </div>
                    <h4 className="text-lg font-semibold text-white mb-2">Leave Feedback</h4>
                    <p className="text-slate-300 text-sm">
                      We're building this for you. Let us know what you want to see.
                    </p>
                  </div>

                  {errorMsg && (
                    <div className="p-3 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl">
                      {errorMsg}
                    </div>
                  )}

                  <div className="space-y-4">
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-slate-400 mb-1.5">Email address <span className="text-red-400">*</span></label>
                      <input
                        type="email"
                        id="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@company.com"
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-50 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                      />
                    </div>

                    <div>
                      <label htmlFor="feedback-combined" className="block text-sm font-medium text-slate-400 mb-1.5 flex justify-between">
                        <span>What feature would you love to see?</span>
                        <span className="text-slate-600 text-xs">Optional</span>
                      </label>
                      <textarea
                        id="feedback-combined"
                        rows={3}
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="e.g. Shopify integration, custom bot personalities..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-50 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-800 disabled:text-slate-400 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_-5px_rgba(79,70,229,0.5)] disabled:shadow-none flex items-center justify-center gap-2 mt-4"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                        Submitting...
                      </>
                    ) : (
                      "Submit Feedback"
                    )}
                  </button>
                </form>
              ) : step === 'email' ? (
                <form onSubmit={handleEmailSubmit} className="space-y-4 animate-in slide-in-from-left duration-300 fade-in">
                  <p className="text-slate-300 mb-6">
                    AIOTake is currently in early access. Enter your email to secure your spot in line.
                  </p>

                  {errorMsg && (
                    <div className="p-3 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl">
                      {errorMsg}
                    </div>
                  )}

                  <div className="space-y-4">
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-slate-400 mb-1.5">Email address <span className="text-red-400">*</span></label>
                      <input
                        type="email"
                        id="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@company.com"
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-50 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-800 disabled:text-slate-400 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_-5px_rgba(79,70,229,0.5)] disabled:shadow-none flex items-center justify-center gap-2 mt-4"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                        Joining...
                      </>
                    ) : (
                      "Join Waitlist"
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleFeedbackSubmit} className="space-y-4 animate-in slide-in-from-right duration-300 fade-in">
                  <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 mb-4">
                      <MessageSquare className="w-6 h-6" />
                    </div>
                    <h4 className="text-lg font-semibold text-white mb-2">Thanks for joining!</h4>
                    <p className="text-slate-300 text-sm">
                      We're building this for you. One quick question before you go:
                    </p>
                  </div>

                  {errorMsg && (
                    <div className="p-3 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl">
                      {errorMsg}
                    </div>
                  )}

                  <div className="space-y-4">
                    <div>
                      <label htmlFor="feedback" className="block text-sm font-medium text-slate-400 mb-1.5 flex justify-between">
                        <span>What feature would you love to see?</span>
                        <span className="text-slate-600 text-xs">Optional</span>
                      </label>
                      <textarea
                        id="feedback"
                        rows={3}
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="e.g. Shopify integration, custom bot personalities..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-50 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none"
                        autoFocus
                      />
                    </div>
                  </div>

                  <div className="flex gap-3 mt-4">
                    <button
                      type="button"
                      onClick={skipFeedback}
                      disabled={isSubmitting}
                      className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-medium py-3 rounded-xl transition-all disabled:opacity-50"
                    >
                      Skip
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-[2] bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-800 disabled:text-slate-400 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_-5px_rgba(79,70,229,0.5)] disabled:shadow-none flex items-center justify-center gap-2"
                    >
                      {isSubmitting ? (
                        <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        "Submit Feedback"
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Decorative Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px]" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center font-bold text-lg">
              AI
            </div>
            <span className="text-xl font-bold tracking-tight">AIOTake</span>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-slate-300">
            <Link href="#features" className="hover:text-white transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-white transition-colors">How it Works</Link>
            <Link href="#demo" className="hover:text-white transition-colors">Demo</Link>
          </div>
          <div className="flex gap-4 items-center">
            <button onClick={openWaitlist} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Log in
            </button>
            <button onClick={openWaitlist} className="hidden md:flex text-sm font-medium bg-white text-slate-950 px-5 py-2.5 rounded-full hover:bg-slate-200 transition-colors">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-20">
        {/* Hero Section */}
        <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-40 flex flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/20 text-indigo-300 font-medium mb-8 backdrop-blur-sm border border-indigo-500/30">
            <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
            AIOTake is in Early Access — Only 50 free spots available!
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tighter max-w-4xl mb-8 leading-[1.1]">
            Automate Your Sales on <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-600">WhatsApp</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
            Close deals while you rest. AIOTake provides a 24/7 AI-powered Orderbot perfectly integrated with a powerful CRM built natively for WhatsApp. <br />
            <strong className="text-white font-medium mt-2 block">🌍 Free Early Access for the first 50 users (includes 1,000 free AI messages/mo) in exchange for feedback!</strong>
          </p>
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <button onClick={openWaitlist} className="flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-blue-600 text-white px-8 py-4 rounded-full font-medium hover:scale-105 transition-transform shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)]">
              Claim Free Access <ArrowRight className="w-4 h-4" />
            </button>
            <Link href="#how-it-works" className="flex items-center justify-center gap-2 bg-white/5 border border-white/10 hover:bg-white/10 text-white px-8 py-4 rounded-full font-medium transition-colors">
              Learn More
            </Link>
          </div>

          {/* Abstract Dashboard Preview */}
          <div className="mt-20 w-full max-w-5xl relative">
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent z-10"></div>
            <div className="rounded-2xl border border-white/10 bg-slate-900/50 backdrop-blur-xl p-2 shadow-2xl overflow-hidden aspect-video">
              <div className="w-full h-full rounded-xl border border-white/5 bg-slate-950/80 flex">
                <div className="w-64 border-r border-white/5 p-4 hidden md:block">
                  <div className="w-32 h-4 sm:h-5 bg-white/10 rounded mb-8"></div>
                  <div className="space-y-4">
                    {[1, 2, 3, 4].map(i => <div key={i} className="w-full h-4 sm:h-8 bg-white/5 rounded"></div>)}
                  </div>
                </div>
                <div className="flex-1 p-8">
                  <div className="flex justify-between mb-8">
                    <div className="w-48 h-6 sm:h-8 bg-white/10 rounded"></div>
                    <div className="w-24 h-6 sm:h-8 bg-white/5 rounded"></div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
                    {[1, 2, 3].map(i => <div key={i} className="h-24 sm:h-32 rounded-xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/5 p-4 flex flex-col justify-between">
                      <div className="w-8 h-8 rounded-lg bg-white/10"></div>
                      <div>
                        <div className="w-16 h-3 bg-white/10 rounded mb-2"></div>
                        <div className="w-24 h-6 bg-white/20 rounded"></div>
                      </div>
                    </div>)}
                  </div>
                  <div className="h-64 rounded-xl border border-white/5 bg-white/[0.02]"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 max-w-7xl mx-auto px-6 relative">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Everything you need to sell smarter</h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">Stop missing messages. Turn your WhatsApp business channel into an automated revenue-generating machine.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors group">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Bot strokeWidth={1.5} />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Orderbot</h3>
              <p className="text-slate-400 leading-relaxed">Intelligent conversation flows that guide your customers from browsing to checkout, completely autonomously 24/7.</p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors group">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageSquare strokeWidth={1.5} />
              </div>
              <h3 className="text-xl font-semibold mb-3">Native WhatsApp</h3>
              <p className="text-slate-400 leading-relaxed">Meet your customers where they already are. Provide frictionless experiences without requiring app downloads or web portals.</p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors group">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <BarChart3 strokeWidth={1.5} />
              </div>
              <h3 className="text-xl font-semibold mb-3">Powerful CRM</h3>
              <p className="text-slate-400 leading-relaxed">Track every order, manage customer profiles, and review AI conversations from a state-of-the-art dashboard.</p>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="py-24 relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="md:w-1/2 mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">How AIOTake Works</h2>
              <p className="text-slate-400 text-lg">Three simple steps to transform your WhatsApp business presence.</p>
            </div>

            <div className="flex flex-col gap-12 relative">
              <div className="absolute left-8 top-0 bottom-0 w-px bg-white/10 md:hidden"></div>

              {[
                { title: "Connect your WhatsApp number", desc: "Scan a QR code or use the official Business API to link your number securely in seconds.", icon: <MessageSquare /> },
                { title: "Train your AI assistant", desc: "Upload your product catalog and business FAQs. Our AI learns your inventory instantly.", icon: <Bot /> },
                { title: "Watch the orders roll in", desc: "The bot handles inquiries and processes orders. You manage fulfillment via the CRM.", icon: <CheckCircle2 /> }
              ].map((step, index) => (
                <div key={index} className="flex gap-6 md:gap-12 items-start relative">
                  <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-indigo-400 shrink-0 relative z-10">
                    {step.icon}
                  </div>
                  <div className="pt-3">
                    <h3 className="text-2xl font-semibold mb-2">Step {index + 1}: {step.title}</h3>
                    <p className="text-slate-400 text-lg max-w-xl">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 relative">
          <div className="max-w-5xl mx-auto px-6">
            <div className="rounded-3xl bg-gradient-to-br from-indigo-900/40 to-blue-900/40 border border-white/10 p-12 md:p-20 text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-[url('/favicon.ico')] opacity-5 bg-center bg-repeat mix-blend-overlay"></div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 relative z-10">Help us shape the future of sales.</h2>
              <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto relative z-10">We are offering full, free access to the first 50 early adopters who are willing to share their feedback and help us build the best WhatsApp CRM. (Includes 1,000 free AI interactions per month)</p>
              <div className="flex justify-center relative z-10">
                <button onClick={openWaitlist} className="bg-white text-slate-950 px-8 py-4 rounded-full font-medium hover:scale-105 transition-transform text-lg flex items-center gap-2 shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)]">
                  Claim Your Free Access <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Pricing Section */}
      <div id="pricing" className="py-24 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Simple, transparent pricing</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">Start for free and upgrade when you need more volume.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">

          {/* Free Tier */}
          <div className="bg-slate-900/50 border border-slate-700/50 rounded-2xl p-8 backdrop-blur-sm">
            <h3 className="text-2xl font-bold mb-2">Early Access Free</h3>
            <p className="text-slate-400 mb-6">Perfect for trying out the platform.</p>
            <div className="text-4xl font-bold mb-8">$0<span className="text-lg text-slate-500 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8">
              <li className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> 1,000 AI Messages / month</li>
              <li className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> Full CRM Access</li>
              <li className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> Webhook Integration</li>
            </ul>
            <button onClick={openWaitlist} className="block w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-center rounded-lg font-medium transition-colors">Start Free</button>
          </div>

          {/* Pro Tier */}
          <div className="bg-indigo-600/10 border border-indigo-500/50 rounded-2xl p-8 backdrop-blur-sm relative shadow-2xl shadow-indigo-500/10">
            <div className="absolute top-0 right-8 -translate-y-1/2 px-3 py-1 bg-indigo-500 text-xs font-bold uppercase tracking-wider rounded-full text-white">Most Popular</div>
            <h3 className="text-2xl font-bold mb-2 text-white">Pro</h3>
            <p className="text-indigo-200 mb-6">For growing businesses automating sales.</p>
            <div className="text-4xl font-bold mb-8 text-white">$49<span className="text-lg text-indigo-300 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8">
              <li className="flex items-center gap-3 text-white"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> 10,000 AI Messages / month</li>
              <li className="flex items-center gap-3 text-white"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> Unlimited CRM Users</li>
              <li className="flex items-center gap-3 text-white"><CheckCircle2 className="w-5 h-5 text-indigo-400" /> Priority Support</li>
            </ul>
            <button onClick={openWaitlist} className="block w-full py-3 px-4 bg-indigo-500 hover:bg-indigo-600 text-white text-center rounded-lg font-medium transition-colors shadow-lg shadow-indigo-500/25">Upgrade to Pro</button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 relative z-10 mt-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center font-bold text-xs">AI</div>
            <span className="font-semibold text-slate-200">AIOTake</span>
          </div>
          <div className="text-sm text-slate-500">
            © {new Date().getFullYear()} AIOTake. All rights reserved.
          </div>
          <div className="flex gap-6 text-sm text-slate-400">
            <Link href="/terms" className="hover:text-white transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
          </div>
        </div>
      </footer>

      {/* Floating Feedback Button */}
      <button
        onClick={openFeedback}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-5 py-3 shadow-lg shadow-indigo-600/30 transition-all hover:-translate-y-1 hover:shadow-indigo-600/50 border border-indigo-500/50"
      >
        <MessageSquare className="w-5 h-5" />
        <span className="font-medium">Feedback</span>
      </button>
    </div>
  );
}
