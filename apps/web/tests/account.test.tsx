import {afterEach,expect,it,vi} from "vitest";
import {cleanup,render,screen,fireEvent} from "@testing-library/react";
import Shell from "@/components/Shell";
import {authClient} from "@/lib/supabase";
import {api} from "@/lib/api";
vi.mock("next/navigation",()=>({usePathname:()=>"/"}));
vi.mock("@/lib/supabase",()=>({authClient:vi.fn()}));
vi.mock("@/lib/api",()=>({api:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();vi.unstubAllEnvs();});
it("automatically registers a Google account and shows the personal workspace without organizational records",async()=>{
  vi.mocked(authClient).mockReturnValue({auth:{
    getSession:vi.fn().mockResolvedValue({data:{session:{access_token:"synthetic"}}}),
    onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}}),
  }} as never);
  vi.mocked(api).mockRejectedValueOnce(new Error("Account has not been approved for OMS"))
    .mockResolvedValueOnce({registered:true})
    .mockResolvedValueOnce({id:"synthetic",email:"normal@example.invalid",roles:[],mfa:false})
    .mockResolvedValueOnce({version:0,details:{},goals:[],reviewer_assigned:false})
    .mockResolvedValueOnce({items:[]}).mockResolvedValueOnce({items:[]}).mockResolvedValueOnce({items:[]});
  render(<Shell title="Dashboard" subtitle="Workspace"><p>Private workspace records</p></Shell>);
  await screen.findByRole("heading",{name:"My workspace"});
  await screen.findByLabelText("Full name");
  expect(api).toHaveBeenNthCalledWith(2,"/account/register",{method:"POST"});
  expect(screen.getByText("normal@example.invalid")).toBeTruthy();
  expect(screen.queryByText("Private workspace records")).toBeNull();
  expect(screen.queryByText("Access needs approval")).toBeNull();
});

it("keeps Google sign-in available while the email sender is unconfigured",async()=>{
  vi.stubEnv("NEXT_PUBLIC_EMAIL_OTP_ENABLED","false");
  vi.mocked(authClient).mockReturnValue({auth:{getSession:vi.fn().mockResolvedValue({data:{session:null}}),onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}})}} as never);
  render(<Shell title="Dashboard" subtitle="Workspace"><p>Private workspace records</p></Shell>);
  await screen.findByRole("button",{name:"Continue with Google"});
  expect(screen.queryByLabelText("Email address")).toBeNull();
  expect(screen.getByLabelText("Email")).toBeTruthy();
  expect(screen.getByLabelText("Password")).toBeTruthy();
  expect(screen.queryByRole("button",{name:"Sign in with an email code"})).toBeNull();
  vi.unstubAllEnvs();
});

it("shows email code signup alongside Google only when delivery is enabled",async()=>{
  vi.stubEnv("NEXT_PUBLIC_EMAIL_OTP_ENABLED","true");
  vi.mocked(authClient).mockReturnValue({auth:{getSession:vi.fn().mockResolvedValue({data:{session:null}}),onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}})}} as never);
  render(<Shell title="Dashboard" subtitle="Workspace"><p>Private workspace records</p></Shell>);
  await screen.findByRole("button",{name:"Sign in with an email code"});
  fireEvent.click(screen.getByRole("button",{name:"Sign in with an email code"}));
  await screen.findByLabelText("Email address");
  expect(screen.getByRole("button",{name:"Sign up / sign in with email"})).toBeTruthy();
  expect(screen.getByRole("button",{name:"Continue with Google"})).toBeTruthy();
  expect(screen.queryByText(/Email-code sign-in is awaiting email sender setup/)).toBeNull();
});

it('keeps a signed-in leader behind authenticator verification before showing private records',async()=>{
 vi.mocked(authClient).mockReturnValue({auth:{getSession:vi.fn().mockResolvedValue({data:{session:{access_token:'synthetic'}}}),onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}}),mfa:{listFactors:vi.fn().mockResolvedValue({data:{all:[{id:'synthetic-factor',factor_type:'totp',status:'verified'}]},error:null})}}} as never);
 vi.mocked(api).mockRejectedValue(new Error('Administrator MFA required'));
 render(<Shell title="Dashboard" subtitle="Workspace"><p>Private leader records</p></Shell>);
 await screen.findByRole('heading',{name:'Leader verification'});await screen.findByLabelText('Authenticator code');expect(screen.queryByText('Private leader records')).toBeNull();expect(screen.queryByRole('button',{name:'LOGIN'})).toBeNull();
});
