import {afterEach,beforeEach,describe,expect,it,vi} from "vitest";
import {cleanup,render,screen,waitFor,fireEvent} from "@testing-library/react";
import type {ReactNode} from "react";
import Home from "@/app/page";
import {api,type Dashboard} from "@/lib/api";
vi.mock("@/components/Shell",()=>({default:({children}:{children:ReactNode})=><main>{children}</main>}));
vi.mock("@/lib/api",()=>({api:vi.fn()}));
const report:Dashboard={total_active:4,by_category:{RUKON:1,WORKER:1,ASSOCIATE:1,SUPPORTER:1},by_unit:[],by_ward:[],this_month:{increase:4,decrease:0,net:4},period:{start_date:"2020-01-01",end_date:"2020-01-31",increase:2,decrease:1,net:1},comparison:{start_date:"2019-12-01",end_date:"2019-12-31",total_active:3,increase:3,decrease:0,net:3},monthly_history:[{month:"2020-01",start_date:"2020-01-01",end_date:"2020-01-31",increase:2,decrease:1,net:1}],timezone:"Asia/Dhaka",as_of:"2020-01-31",generated_at:"2020-02-01T00:00:00Z"};
afterEach(cleanup);
beforeEach(()=>{vi.mocked(api).mockReset();vi.mocked(api).mockResolvedValue(report);});
describe("dashboard reporting flow",()=>{
  it("shows historical as-of semantics and sends selected dates",async()=>{
    render(<Home/>);
    await screen.findByText("Monthly history");
    expect(screen.getByRole("status").textContent).toContain("Asia/Dhaka");
    fireEvent.change(screen.getByLabelText("Start date"),{target:{value:"2020-01-01"}});
    fireEvent.change(screen.getByLabelText("End date"),{target:{value:"2020-01-31"}});
    fireEvent.click(screen.getByRole("button",{name:"Apply dates"}));
    await waitFor(()=>expect(api).toHaveBeenLastCalledWith("/reports/dashboard?start_date=2020-01-01&end_date=2020-01-31"));
    await screen.findByText("Monthly history");
    fireEvent.click(screen.getByRole("button",{name:"Current month"}));
    await waitFor(()=>expect(api).toHaveBeenLastCalledWith("/reports/dashboard?"));
  });
  it("shows a failed request without presenting stale report figures",async()=>{
    vi.mocked(api).mockRejectedValue(new Error("Insufficient organizational scope"));
    render(<Home/>);
    expect((await screen.findByRole("alert")).textContent).toContain("Insufficient organizational scope");
    expect(screen.queryByText("Monthly history")).toBeNull();
  });
});
