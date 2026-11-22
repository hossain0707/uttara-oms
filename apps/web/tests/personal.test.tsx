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
  fireEvent.click(await screen.findByRole("button", {name:"Edit profile"}));
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

function mockWorkspace() {
  let saved = {version: 1, details: {full_name: 'Saved owner', consent: true, books: []}, goals: [], reviewer_assigned: false};
  vi.mocked(api).mockImplementation(async (path, options) => {
    if (path === '/self/profile') {
      if (options?.method === 'PUT') saved = {...saved, version: saved.version + 1, details: JSON.parse(String(options.body)).details};
      return saved;
    }
    return {items: []};
  });
}
it('isolates profile saves from unfinished reading rows and ignores completely empty book rows', async () => {
  mockWorkspace(); render(<PersonalWorkspace />); fireEvent.click(await screen.findByRole('button',{name:'Edit profile'})); await screen.findByLabelText('Full name');
  fireEvent.click(screen.getByRole('tab', {name:'Targets & books'}));
  fireEvent.click(screen.getByRole('button', {name:'Add book'}));
  fireEvent.click(screen.getByRole('tab', {name:'My profile'}));
  fireEvent.change(screen.getByLabelText('Full name'), {target:{value:'Updated owner'}});
  fireEvent.click(screen.getByRole('button', {name:'Save my profile'}));
  await screen.findByText('Profile saved.');
  const put = vi.mocked(api).mock.calls.find(([,o])=>o?.method==='PUT');
  expect(JSON.parse(String(put?.[1]?.body)).details.books).toEqual([]);
  fireEvent.click(screen.getByRole('tab', {name:'Targets & books'}));
  fireEvent.click(screen.getByRole('button', {name:'Save reading progress'}));
  await screen.findByText('Reading progress saved.');
  expect(screen.queryByLabelText('Book title')).toBeNull();
});
it('requires a book title when progress has been entered', async () => {
  mockWorkspace(); render(<PersonalWorkspace />); fireEvent.click(await screen.findByRole('button',{name:'Edit profile'})); await screen.findByLabelText('Full name');
  fireEvent.click(screen.getByRole('tab', {name:'Targets & books'}));
  fireEvent.click(screen.getByRole('button', {name:'Add book'}));
  fireEvent.change(screen.getByLabelText('Pages completed'), {target:{value:'5'}});
  fireEvent.click(screen.getByRole('button', {name:'Save reading progress'}));
  await screen.findByText('Book 1: enter a title or remove the unfinished entry.');
  expect(vi.mocked(api).mock.calls.filter(([,o])=>o?.method==='PUT')).toHaveLength(0);
});
it('blocks report saving until pending daily values are included', async () => {
  mockWorkspace(); render(<PersonalWorkspace />); fireEvent.click(await screen.findByRole('button',{name:'Edit profile'})); await screen.findByLabelText('Full name');
  fireEvent.click(screen.getByRole('tab', {name:'Daily & monthly reports'}));
  fireEvent.change(screen.getByLabelText('Prayers (prayers)'), {target:{value:'5'}});
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', {name:'Save draft'}));
  await screen.findByText('Click Add / update day before saving this report so your daily entry is included.');
  expect(vi.mocked(api).mock.calls.filter(([p,o])=>p==='/self/reports' && o?.method==='PUT')).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', {name:'Add / update day'}));
  expect((screen.getByLabelText('Prayers (prayers)') as HTMLInputElement).value).toBe('');
});

it('adds a library book and saves it without overwriting unsaved profile edits',async()=>{
 mockWorkspace();render(<PersonalWorkspace/>);fireEvent.click(await screen.findByRole('button',{name:'Edit profile'})); await screen.findByLabelText('Full name');
 fireEvent.change(screen.getByLabelText('Full name'),{target:{value:'Unsaved profile name'}});
 fireEvent.click(screen.getByRole('tab',{name:'Library & syllabus'}));
 fireEvent.click(screen.getAllByRole('button',{name:'Add to my reading'})[0]);
 fireEvent.click(screen.getByRole('button',{name:'My reading list'}));
 fireEvent.click(screen.getByRole('button',{name:'Save reading progress'}));
 await screen.findByText('Reading progress saved.');
 const put=vi.mocked(api).mock.calls.find(([,o])=>o?.method==='PUT');
 const body=JSON.parse(String(put?.[1]?.body));expect(body.details.full_name).toBe('Saved owner');expect(body.details.books).toHaveLength(1);
 fireEvent.click(screen.getByRole('tab',{name:'My profile'}));expect((screen.getByLabelText('Full name') as HTMLInputElement).value).toBe('Unsaved profile name');
});

it('shows a saved profile without identity fields and allows editing or cancelling without saving', async()=>{
 mockWorkspace();render(<PersonalWorkspace/>);
 await screen.findByRole('heading',{name:'Saved owner'});
 expect(screen.queryByLabelText('Full name')).toBeNull();
 expect(screen.queryByText('Identity document')).toBeNull();
 expect(screen.queryByText('1000000000')).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Edit profile'}));
 expect(screen.queryByLabelText('NID or passport number')).toBeNull();
 fireEvent.change(screen.getByLabelText('Full name'),{target:{value:'Changed'}});
 fireEvent.click(screen.getByRole('button',{name:'Cancel editing'}));
 expect(screen.getByRole('heading',{name:'Saved owner'})).toBeTruthy();
 expect(vi.mocked(api).mock.calls.filter(([,o])=>o?.method==='PUT')).toHaveLength(0);
 fireEvent.click(screen.getByRole('button',{name:'Edit profile'}));
 expect(screen.queryByLabelText('NID or passport number')).toBeNull();
 fireEvent.change(screen.getByLabelText('Full name'),{target:{value:'Changed'}});
 fireEvent.click(screen.getByRole('button',{name:'Save my profile'}));
 await screen.findByRole('heading',{name:'Changed'});
 expect(screen.queryByLabelText('Full name')).toBeNull();
});
