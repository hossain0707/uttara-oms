import {afterEach,expect,it,vi} from "vitest";
import {cleanup,render,screen,fireEvent,waitFor} from "@testing-library/react";
import type {ReactNode} from "react";
import OrgPage from "@/app/organization/page";
import {api} from "@/lib/api";
vi.mock("@/components/Shell",()=>({default:({children}:{children:ReactNode})=><main>{children}</main>}));
vi.mock("@/lib/api",()=>({api:vi.fn()}));
afterEach(cleanup);
it("allows an administrator to rename and deactivate an existing unit",async()=>{
  vi.mocked(api).mockImplementation(async(path)=>{
    if(path==="/me")return {id:"admin",email:"test@example.invalid",mfa:true,roles:[{role:"THANA_ADMIN",scope_node_id:null}]} as never;
    if(path==="/organization/nodes")return {items:[{id:"unit-id",parent_id:"ward-id",kind:"UNIT",code:"unit-01",name:"Test Unit",active:true}]} as never;
    return {} as never;
  });
  render(<OrgPage/>);
  fireEvent.click(await screen.findByRole("button",{name:"Edit / change status"}));
  fireEvent.change(screen.getByLabelText("Name"),{target:{value:"Updated Unit"}});
  fireEvent.click(screen.getByLabelText("Active"));
  fireEvent.click(screen.getByRole("button",{name:"Save organization"}));
  await waitFor(()=>expect(api).toHaveBeenCalledWith("/organization/nodes/unit-id",{method:"PATCH",body:JSON.stringify({name:"Updated Unit",active:false})}));
  await screen.findByText("Organization updated; historical records preserved.");
});
