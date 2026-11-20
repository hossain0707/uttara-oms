"use client";
import { useEffect, useState, type FormEvent } from "react";
import { authClient } from "@/lib/supabase";
export default function EmailOtpSignIn() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!seconds) return;
    const timer = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [seconds]);
  async function send() {
    setBusy(true);
    setNotice("");
    try {
      const { error } = await authClient().auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true },
      });
      if (error) throw error;
      setSent(true);
      setSeconds(60);
      setNotice(
        "Check your email for the verification code, including your spam folder.",
      );
    } catch (e) {
      setNotice(
        e instanceof Error
          ? e.message
          : "Unable to send a code. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!sent) {
      await send();
      return;
    }
    setBusy(true);
    setNotice("");
    try {
      const { error } = await authClient().auth.verifyOtp({
        email: email.trim(),
        token: code.trim(),
        type: "email",
      });
      if (error) throw error;
    } catch (e) {
      setNotice(
        e instanceof Error
          ? e.message
          : "Verification failed. Request a new code.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit} className="otp-form">
      <div className="form-field">
        <label htmlFor="login-email">Email address</label>
        <input
          id="login-email"
          className="input"
          type="email"
          autoComplete="email"
          required
          disabled={sent || busy}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      {sent && (
        <div className="form-field">
          <label htmlFor="email-code">Email verification code</label>
          <input
            id="email-code"
            className="input"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6,10}"
            maxLength={10}
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          />
        </div>
      )}
      {notice && <p role="status">{notice}</p>}
      <button className="primary-btn wide" disabled={busy}>
        {busy
          ? "Please wait…"
          : sent
            ? "Verify and sign in"
            : "Sign up / sign in with email"}
      </button>
      {sent && (
        <div className="form-actions">
          <button
            type="button"
            disabled={busy || seconds > 0}
            onClick={() => void send()}
          >
            Resend{seconds > 0 ? ` (${seconds}s)` : ""}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setSent(false);
              setCode("");
              setNotice("");
            }}
          >
            Change email
          </button>
        </div>
      )}
    </form>
  );
}
