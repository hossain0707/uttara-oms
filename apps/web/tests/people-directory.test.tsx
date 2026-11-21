import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import type {ReactNode} from 'react';
import People from '@/app/members/page';
import {api} from '@/lib/api';
vi.mock('@/components/Shell',()=>({default:({children}:{children:ReactNode})=><main>{children}</main>}));
vi.mock('@/lib/api',()=>({api:vi.fn()}));
const profile={source:'PROFILE',self_reported:true,id:'profile:synthetic',full_name:'মোঃ হোসাইন',category:'SUPPORTER',status:'ACTIVE',photo:'',member_number:'',org_node_id:'',version:0};
afterEach(cleanup);
beforeEach(()=>{vi.mocked(api).mockReset();vi.mocked(api).mockImplementation(async(path)=>path.startsWith('/directory?')?{items:[profile],total:1}:{items:[]});});
it('shows saved names unchanged with a read-only personal profile summary',async()=>{
 render(<People/>);
 await screen.findByText('মোঃ হোসাইন');
 fireEvent.click(screen.getByRole('button',{name:'View profile'}));
 expect(screen.getByRole('heading',{name:'মোঃ হোসাইন'})).toBeTruthy();
 expect(screen.getByText('PERSONAL PROFILE')).toBeTruthy();
 expect(screen.queryByRole('button',{name:'Edit profile'})).toBeNull();
 const input=screen.getByRole('textbox');
 fireEvent.change(input,{target:{value:'হো'}});
 await waitFor(()=>expect(vi.mocked(api).mock.calls.some(([path])=>path.startsWith('/directory?')&&new URLSearchParams(path.split('?')[1]).get('q')==='হো')).toBe(true));
});
it('retains edit actions for official member records',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>path.startsWith('/directory?')?{items:[{...profile,source:'MEMBER',self_reported:false,member_number:'TEST-001'}],total:1}:{items:[]});
 render(<People/>);
 fireEvent.click(await screen.findByRole('button',{name:'View profile'}));
 expect(screen.getByRole('button',{name:'Edit profile'})).toBeTruthy();
});
