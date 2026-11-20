import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import EmailOtpSignIn from "@/components/EmailOtpSignIn";
import { authClient } from "@/lib/supabase";
vi.mock("@/lib/supabase", () => ({ authClient: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("sends an email OTP then verifies the entered code without requiring a password", async () => {
  const send = vi.fn().mockResolvedValue({ error: null }),
    verify = vi.fn().mockResolvedValue({ error: null });
  vi.mocked(authClient).mockReturnValue({
    auth: { signInWithOtp: send, verifyOtp: verify },
  } as never);
  render(<EmailOtpSignIn />);
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "synthetic@example.invalid" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Sign up / sign in with email" }),
  );
  await screen.findByLabelText("Email verification code");
  expect(send).toHaveBeenCalledWith({
    email: "synthetic@example.invalid",
    options: { shouldCreateUser: true },
  });
  fireEvent.change(screen.getByLabelText("Email verification code"), {
    target: { value: "123456" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Verify and sign in" }));
  await waitFor(() =>
    expect(verify).toHaveBeenCalledWith({
      email: "synthetic@example.invalid",
      token: "123456",
      type: "email",
    }),
  );
  expect(screen.queryByLabelText("Password")).toBeNull();
});
it("shows delivery failures rather than claiming a code was sent", async () => {
  vi.mocked(authClient).mockReturnValue({
    auth: {
      signInWithOtp: vi
        .fn()
        .mockResolvedValue({ error: new Error("Email provider disabled") }),
    },
  } as never);
  render(<EmailOtpSignIn />);
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "synthetic@example.invalid" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Sign up / sign in with email" }),
  );
  await screen.findByText("Email provider disabled");
  expect(screen.queryByLabelText("Email verification code")).toBeNull();
});
