import {afterEach,expect,it,vi} from "vitest";
import {cleanup,render,screen} from "@testing-library/react";
import Shell from "@/components/Shell";
import {authClient} from "@/lib/supabase";
import {api} from "@/lib/api";
vi.mock("next/navigation",()=>({usePathname:()=>"/"}));
vi.mock("@/lib/supabase",()=>({authClient:vi.fn()}));
vi.mock("@/lib/api",()=>({api:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it("automatically registers a Google account and shows its own home without workspace records",async()=>{
  vi.mocked(authClient).mockReturnValue({auth:{
    getSession:vi.fn().mockResolvedValue({data:{session:{access_token:"synthetic"}}}),
    onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}}),
  }} as never);
  vi.mocked(api).mockRejectedValueOnce(new Error("Account has not been approved for OMS"))
    .mockResolvedValueOnce({registered:true})
    .mockResolvedValueOnce({id:"synthetic",email:"normal@example.invalid",roles:[],mfa:false});
  render(<Shell title="Dashboard" subtitle="Workspace"><p>Private workspace records</p></Shell>);
  await screen.findByRole("heading",{name:"Your account is ready"});
  expect(api).toHaveBeenNthCalledWith(2,"/account/register",{method:"POST"});
  expect(screen.getByText("normal@example.invalid")).toBeTruthy();
  expect(screen.queryByText("Private workspace records")).toBeNull();
  expect(screen.queryByText("Access needs approval")).toBeNull();
});
