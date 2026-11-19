import {afterEach,expect,it,vi} from "vitest";
import {cleanup,render,screen,fireEvent,waitFor} from "@testing-library/react";
import MfaChallenge from "@/components/MfaChallenge";
import {authClient} from "@/lib/supabase";
vi.mock("@/lib/supabase",()=>({authClient:vi.fn()}));
afterEach(cleanup);
it("challenges an enrolled factor and displays verification errors",async()=>{
  const verify=vi.fn().mockResolvedValue({error:new Error("Invalid authenticator code")});
  vi.mocked(authClient).mockReturnValue({auth:{mfa:{listFactors:vi.fn().mockResolvedValue({data:{totp:[{id:"synthetic-factor"}],all:[]},error:null}),challengeAndVerify:verify}}} as never);
  render(<MfaChallenge/>);
  const input=await screen.findByLabelText("Authenticator code");
  fireEvent.change(input,{target:{value:"123456"}});
  fireEvent.click(screen.getByRole("button",{name:"Verify code"}));
  await waitFor(()=>expect(verify).toHaveBeenCalledWith({factorId:"synthetic-factor",code:"123456"}));
  expect((await screen.findByRole("alert")).textContent).toBe("Invalid authenticator code");
});
