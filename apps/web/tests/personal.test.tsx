import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import PersonalWorkspace from "@/components/PersonalWorkspace";
import { api } from "@/lib/api";
vi.mock("@/lib/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("saves only the owner's self-reported profile and allows a separate leader application", async () => {
  vi.mocked(api).mockImplementation(async (path) =>
    path === "/self/profile"
      ? {
          version: 1,
          details: { full_name: "Synthetic owner", consent: true },
          goals: [],
          reviewer_assigned: false,
        }
      : { items: [] },
  );
  render(<PersonalWorkspace />);
  await screen.findByLabelText("Full name");
  fireEvent.change(screen.getByLabelText("Full name"), {
    target: { value: "Updated owner" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save my profile" }));
  await waitFor(() =>
    expect(api).toHaveBeenCalledWith(
      "/self/profile",
      expect.objectContaining({
        method: "PUT",
        body: expect.stringContaining('"full_name":"Updated owner"'),
      }),
    ),
  );
  expect(api).not.toHaveBeenCalledWith("/members", expect.anything());
  fireEvent.click(screen.getByRole("tab", { name: "Request permissions" }));
  await screen.findByRole("heading", {
    name: "Request a responsible-person role",
  });
  const roles = screen.getByLabelText("Requested role");
  expect(roles.textContent).not.toContain("Master");
  expect(roles.textContent).not.toContain("THANA_ADMIN");
});
