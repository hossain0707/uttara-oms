import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import AccessPage from '@/app/access/page';
import {api} from '@/lib/api';
vi.mock('@/lib/api',()=>({api:vi.fn()}));
vi.mock('@/lib/supabase',()=>({authClient:()=>({auth:{onAuthStateChange:()=>({data:{subscription:{unsubscribe:vi.fn()}}})}})}));
vi.mock('@/components/Shell',()=>({default:({children}:{children:React.ReactNode})=><main>{children}</main>}));
vi.mock('@/components/PersonalAssignments',()=>({default:()=>null}));
afterEach(()=>{cleanup();vi.clearAllMocks();vi.restoreAllMocks();});
function fixture(own=false,fail=false){
 let requests=[{id:'request',auth_sub:'subject',email:'member@example.invalid',role:'WARD_ADMIN',scope_node_id:'ward',operation:'GRANT',status:'PENDING',requested_by:own?'admin':'applicant',requested_at:'2026-11-21',reviewed_at:null}];
 let grants:{role:string;scope_node_id:string|null}[]=[];
 vi.spyOn(window,'confirm').mockReturnValue(true);
 vi.mocked(api).mockImplementation(async(path,options)=>{
  if(path==='/me')return {id:'admin',email:'admin@example.invalid',roles:[{role:'THANA_ADMIN',scope_node_id:null}],mfa:true};
  if(path==='/organization/nodes')return {items:[{id:'ward',kind:'WARD',name:'Ward 01',active:true}]};
  if(path==='/access/users')return {items:[{id:'target',auth_sub:'subject',email:'member@example.invalid',active:true,roles:grants}]};
  if(path==='/access/requests'&&options?.method==='POST'){const row={...requests[0],...JSON.parse(String(options.body)),id:'removal',status:'PENDING',requested_by:'admin'};requests=[row,...requests];return row;}
  if(path==='/access/requests')return {items:requests.map(r=>({...r}))};
  if(path==='/access/requests/request/decision'){
   if(fail)throw new Error('Review failed. Try again.');
   const approve=JSON.parse(String(options?.body)).approve;requests=requests.map(r=>r.id==='request'?{...r,status:approve?'APPROVED':'REJECTED'}:r);
   if(approve)grants=[{role:'WARD_ADMIN',scope_node_id:'ward'}];return requests.find(r=>r.id==='request');
  }
  throw new Error('Unexpected test path '+path);
 });
}
it('approves once, shows only Remove on the granted permission, and keeps the result after reloading',async()=>{
 fixture();const view=render(<AccessPage/>);await screen.findByRole('button',{name:'Approve'});fireEvent.click(screen.getByRole('button',{name:'Approve'}));await screen.findByText('APPROVED');expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();await screen.findByRole('button',{name:'Remove WARD_ADMIN for member@example.invalid in Ward 01'});view.unmount();render(<AccessPage/>);await screen.findByRole('button',{name:'Remove WARD_ADMIN for member@example.invalid in Ward 01'});expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();
});
it('explains self-review restrictions but lets the requesting administrator reject their own request',async()=>{
 fixture(true);render(<AccessPage/>);await screen.findByText(/You created this request/);expect((screen.getByRole('button',{name:'Approve'}) as HTMLButtonElement).disabled).toBe(true);fireEvent.click(screen.getByRole('button',{name:'Reject'}));await screen.findByText('REJECTED');expect(screen.queryByRole('button',{name:'Reject'})).toBeNull();
});
it('shows a failed decision beside the row and leaves it pending',async()=>{
 fixture(false,true);render(<AccessPage/>);await screen.findByRole('button',{name:'Approve'});fireEvent.click(screen.getByRole('button',{name:'Approve'}));await waitFor(()=>expect(screen.getAllByText('Review failed. Try again.').length).toBe(2));expect(screen.getByRole('button',{name:'Approve'})).toBeTruthy();expect(screen.queryByText('APPROVED')).toBeNull();
});
it('Remove requests review without deleting the account or silently removing a grant',async()=>{
 fixture();render(<AccessPage/>);await screen.findByRole('button',{name:'Approve'});fireEvent.click(screen.getByRole('button',{name:'Approve'}));const remove=await screen.findByRole('button',{name:'Remove WARD_ADMIN for member@example.invalid in Ward 01'});fireEvent.click(remove);await screen.findByText('Removal pending');expect(api).toHaveBeenCalledWith('/access/requests',expect.objectContaining({method:'POST',body:expect.stringContaining('"operation":"REVOKE"')}));expect(vi.mocked(api).mock.calls.some(([,o])=>o?.method==='DELETE')).toBe(false);
});
