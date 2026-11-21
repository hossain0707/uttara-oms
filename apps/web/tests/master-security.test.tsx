import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import MasterSecurity from '@/components/MasterSecurity';
import {api} from '@/lib/api';
vi.mock('@/lib/api',()=>({api:vi.fn()}));
vi.mock('@/components/MfaChallenge',()=>({default:()=> <p>Verify authenticator</p>}));
afterEach(()=>{cleanup();vi.clearAllMocks();vi.restoreAllMocks();});
function fixture(owner=true){
 vi.spyOn(window,'confirm').mockReturnValue(true);
 vi.mocked(api).mockImplementation(async(path)=>{
 if(path==='/me')return {id:owner?'owner':'reviewer',roles:[{role:'THANA_ADMIN'}],mfa:true,is_master_admin:owner};
 if(path==='/master/security')return {is_owner:owner,items:owner?[{id:'owner',email:'owner@example.invalid',active:true,is_owner:true,roles:[{role:'THANA_ADMIN'}],policy:{id:null,exempt:false,until:null,reason:'',expired:false}},{id:'target',email:'target@example.invalid',active:true,is_owner:false,roles:[{role:'THANA_ADMIN'}],policy:{id:null,exempt:false,until:null,reason:'',expired:false}}]:[],pending:[{id:'req',user_id:'target',email:'target@example.invalid',requested_by:'owner',reason:'Phone replacement',until:null}],history:[]};
 return {status:'PENDING'};
 });
}
it('shows owner controls, keeps owner out of exemption choices, and submits a request rather than a direct exemption',async()=>{
 fixture();render(<MasterSecurity/>);await screen.findByLabelText('Account');
 const options=screen.getByLabelText('Account');expect(options.textContent).not.toContain('owner@example.invalid');
 fireEvent.change(options,{target:{value:'target'}});fireEvent.change(screen.getByLabelText('Reason'),{target:{value:'Phone replacement'}});
 expect((screen.getByRole('button',{name:'Approve'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Request exception'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/master/exceptions',expect.objectContaining({method:'POST',body:expect.stringContaining('"user_id":"target"')})));
});
it('shows independent approval only to other admins without owner controls',async()=>{
 fixture(false);render(<MasterSecurity reviewsOnly/>);await screen.findByRole('button',{name:'Approve'});
 expect(screen.queryByLabelText('Account')).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Approve'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/master/exceptions/req/decision',expect.objectContaining({method:'POST',body:'{"approve":true}'})));
});
