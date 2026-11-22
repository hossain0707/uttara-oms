import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import MasterSecurity from '@/components/MasterSecurity';
import {api} from '@/lib/api';
vi.mock('@/lib/api',()=>({api:vi.fn()}));
vi.mock('@/components/MfaChallenge',()=>({default:()=> <p>Verify authenticator</p>}));
afterEach(()=>{cleanup();vi.clearAllMocks();vi.restoreAllMocks();});
function fixture(owner=true){
 const policy={id:null,exempt:false,until:null,reason:'',expired:false};
 const accounts=[{id:'owner',email:'owner@example.invalid',full_name:'Owner',active:true,is_owner:true,deleted:false,roles:[{id:'g-owner',role:'THANA_ADMIN',scope_node_id:null}],roles_version:'a'.repeat(64),policy},{id:'target',email:'target@example.invalid',full_name:'Target Person',active:true,is_owner:false,deleted:false,roles:[{id:'g-target',role:'THANA_ADMIN',scope_node_id:null}],roles_version:'b'.repeat(64),policy}];
 vi.mocked(api).mockImplementation(async(path)=>{
  if(path==='/me')return {id:owner?'owner':'reviewer',roles:[{role:'THANA_ADMIN'}],mfa:true,is_master_admin:owner};
  if(path==='/master/security')return {is_owner:owner,items:[],pending:[{id:'req',user_id:'target',email:'target@example.invalid',requested_by:'owner',reason:'Phone replacement',until:null}],history:[]};
  if(path.startsWith('/master/accounts?'))return {items:accounts,total:1001,stats:{registered:1001,active:1001,suspended:0,deleted:0}};
  if(path.startsWith('/master/confirmation-queue?'))return {items:[],total:0};
  if(path.startsWith('/master/requests?')||path.startsWith('/master/activity?'))return {items:[],total:0};
  if(path.endsWith('/deletion-preview'))return {id:'target',email:'target@example.invalid',revision:'c'.repeat(64),profile:true,reports:2,permissions:1};
  if(path.startsWith('/access/personal/'))return {version:1,reviewer_id:null,member_id:null,goals:[]};
  if(path==='/organization/nodes'||path.startsWith('/members?'))return {items:[]};
  return {status:'APPLIED'};
 });
}
it('lets the owner apply an exception directly after explicit confirmation',async()=>{
 fixture();render(<MasterSecurity/>);await screen.findByText('All registered accounts');
 fireEvent.click((await screen.findAllByRole('button',{name:'Manage account'}))[1]);
 fireEvent.change(screen.getByLabelText('Reason'),{target:{value:'Phone replacement'}});
 fireEvent.click(screen.getByRole('button',{name:'Apply exception directly'}));
 expect(screen.getByRole('dialog').textContent).toContain('No other approval is required');
 expect(vi.mocked(api).mock.calls.some(([p])=>p==='/master/exceptions')).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'Confirm direct action'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/master/exceptions',expect.objectContaining({method:'POST',body:expect.stringContaining('"user_id":"target"')})));
});
it('requires the exact email before irreversible workspace deletion and permits cancellation',async()=>{
 fixture();render(<MasterSecurity/>);await screen.findByText('All registered accounts');
 fireEvent.click((await screen.findAllByRole('button',{name:'Manage account'}))[1]);
 fireEvent.click(screen.getByRole('button',{name:'Delete workspace data'}));
 const dialog=await screen.findByRole('dialog');expect(dialog.textContent).toContain('Supabase login identity are retained');
 const confirm=screen.getAllByRole('button',{name:'Delete workspace data'}).find(b=>dialog.contains(b)) as HTMLButtonElement;
 expect(confirm.disabled).toBe(true);
 fireEvent.change(screen.getByLabelText('Type this account email to confirm deletion'),{target:{value:'wrong@example.invalid'}});expect(confirm.disabled).toBe(true);
 fireEvent.change(screen.getByLabelText('Type this account email to confirm deletion'),{target:{value:'target@example.invalid'}});expect(confirm.disabled).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'Cancel action'}));
 expect(vi.mocked(api).mock.calls.some(([p])=>p.endsWith('/delete-workspace'))).toBe(false);
});
it('searches and pages owner accounts beyond the legacy 500-row window',async()=>{
 fixture();render(<MasterSecurity/>);await screen.findByText('Target Person');
 fireEvent.click(screen.getByRole('button',{name:'Next accounts'}));
 await waitFor(()=>expect(vi.mocked(api).mock.calls.some(([p])=>p.startsWith('/master/accounts?')&&p.includes('offset=20'))).toBe(true));
 fireEvent.change(screen.getByLabelText('Search name or email'),{target:{value:'হো'}});
 await waitFor(()=>expect(vi.mocked(api).mock.calls.some(([p])=>p.startsWith('/master/accounts?')&&new URLSearchParams(p.split('?')[1]).get('q')==='হো')).toBe(true));
});
it('shows independent review to ordinary admins without owner management controls',async()=>{
 fixture(false);render(<MasterSecurity reviewsOnly/>);fireEvent.click(await screen.findByRole('button',{name:'Approve'}));
 expect(screen.queryByText('All registered accounts')).toBeNull();expect(screen.getByRole('dialog')).toBeTruthy();
 expect(vi.mocked(api).mock.calls.some(([p])=>p==='/master/exceptions/req/decision')).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'Confirm approval'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/master/exceptions/req/decision',expect.objectContaining({method:'POST',body:'{"approve":true}'})));
});
it('can cancel an ordinary approval without submitting a decision',async()=>{
 fixture(false);render(<MasterSecurity reviewsOnly/>);fireEvent.click(await screen.findByRole('button',{name:'Approve'}));
 fireEvent.click(screen.getByRole('button',{name:'Cancel decision'}));expect(screen.queryByRole('dialog')).toBeNull();
 expect(vi.mocked(api).mock.calls.some(([p])=>p==='/master/exceptions/req/decision')).toBe(false);
});
