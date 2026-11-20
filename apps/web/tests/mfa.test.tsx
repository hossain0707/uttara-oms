import {afterEach,expect,it,vi} from "vitest";
import {cleanup,render,screen,fireEvent,waitFor} from "@testing-library/react";
import MfaChallenge from "@/components/MfaChallenge";
import {authClient} from "@/lib/supabase";
vi.mock("@/lib/supabase",()=>({authClient:vi.fn()}));
afterEach(cleanup);
it("challenges an enrolled factor and displays verification errors",async()=>{
  const verify=vi.fn().mockResolvedValue({error:new Error("Invalid authenticator code")});
  vi.mocked(authClient).mockReturnValue({auth:{mfa:{listFactors:vi.fn().mockResolvedValue({data:{totp:[{id:"synthetic-factor",status:"verified"}],all:[{id:"synthetic-factor",factor_type:"totp",status:"verified"}]},error:null}),challengeAndVerify:verify}}} as never);
  render(<MfaChallenge/>);
  const input=await screen.findByLabelText("Authenticator code");
  fireEvent.change(input,{target:{value:"123456"}});
  fireEvent.click(screen.getByRole("button",{name:"Verify code"}));
  await waitFor(()=>expect(verify).toHaveBeenCalledWith({factorId:"synthetic-factor",code:"123456"}));
  expect((await screen.findByRole("alert")).textContent).toBe("Invalid authenticator code");
});


it("lets a refreshed unfinished enrollment reset before requesting a new QR",async()=>{
  const pending={id:"pending-factor",factor_type:"totp",status:"unverified"};
  const unenroll=vi.fn().mockResolvedValue({error:null});
  const listFactors=vi.fn().mockResolvedValue({data:{totp:[],all:[pending]},error:null});
  const enroll=vi.fn();
  vi.mocked(authClient).mockReturnValue({auth:{mfa:{listFactors,unenroll,enroll}}} as never);
  render(<MfaChallenge/>);
  fireEvent.click(await screen.findByRole("button",{name:"Reset unfinished setup"}));
  await screen.findByRole("button",{name:"Set up authenticator"});
  expect(unenroll).toHaveBeenCalledWith({factorId:"pending-factor"});
  expect(enroll).not.toHaveBeenCalled();
  expect(screen.queryByLabelText("Authenticator code")).toBeNull();
});

it("preserves a factor verified in another tab before unfinished reset",async()=>{
  const pending={id:"pending-factor",factor_type:"totp",status:"unverified"};
  const verified={...pending,status:"verified"};
  const listFactors=vi.fn()
    .mockResolvedValueOnce({data:{totp:[],all:[pending]},error:null})
    .mockResolvedValueOnce({data:{totp:[verified],all:[verified]},error:null});
  const unenroll=vi.fn();
  vi.mocked(authClient).mockReturnValue({auth:{mfa:{listFactors,unenroll}}} as never);
  render(<MfaChallenge/>);
  fireEvent.click(await screen.findByRole("button",{name:"Reset unfinished setup"}));
  await screen.findByLabelText("Authenticator code");
  expect(unenroll).not.toHaveBeenCalled();
  expect(screen.queryByRole("button",{name:"Set up authenticator"})).toBeNull();
});
