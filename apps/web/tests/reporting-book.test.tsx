import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import PersonalWorkspace from '@/components/PersonalWorkspace';
import {api,downloadPersonalReport} from '@/lib/api';
import {reportToday,type PersonalReport} from '@/lib/report-book';
vi.mock('@/lib/api',()=>({api:vi.fn(),downloadPersonalReport:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
function fixture(status='',reviewer=true){
 const day=reportToday(),month=day.slice(0,7)+'-01';
 let reports:PersonalReport[]=status?[{id:'r1',month,version:1,status,entries:[{day,prayers:0,quran:null,hadith:null,literature:20,organization:45,notes:'Saved note'}],summary:'Saved evaluation',totals:{prayers:0,quran:0,hadith:0,literature:20,organization:45},review_note:status==='RETURNED'?'Please correct the dates':null,entered_days:1,goals:[{metric:'literature',target:30}]}]:[];
 vi.mocked(api).mockImplementation(async(path,options)=>{
  if(path==='/self/profile')return {version:1,details:{full_name:'Synthetic Owner',consent:true,books:[]},goals:[{metric:'literature',target:30}],reviewer_assigned:reviewer};
  if(path==='/self/reports'){
   if(options?.method==='PUT'){const b=JSON.parse(String(options.body));const r={...b,id:'r1',version:b.expected_version+1,status:b.submit?'SUBMITTED':'DRAFT',totals:{prayers:5,literature:10,quran:0,hadith:0,organization:30},review_note:null,entered_days:b.entries.length,goals:[{metric:'literature',target:30}]};reports=[r];return r;}
   return {items:reports};
  }
  return {items:[]};
 });return day;
}
async function open(){render(<PersonalWorkspace/>);await screen.findByRole('heading',{name:'Synthetic Owner'});fireEvent.click(screen.getByRole('tab',{name:'Daily & monthly reports'}));await screen.findByRole('region',{name:'Personal reporting book'});}
function reportWrites(){return vi.mocked(api).mock.calls.filter(([p,o])=>p==='/self/reports'&&o?.method==='PUT');}
it('saves the book entries and monthly evaluation to the real report payload',async()=>{
 const day=fixture();await open();fireEvent.change(screen.getByLabelText('Prayers (prayers)'),{target:{value:'5'}});fireEvent.change(screen.getByLabelText('Literature (pages)'),{target:{value:'10'}});fireEvent.change(screen.getByLabelText('Organizational work (minutes)'),{target:{value:'30'}});fireEvent.click(screen.getByRole('button',{name:'Add / update day'}));fireEvent.change(screen.getByLabelText('Monthly summary'),{target:{value:'My achievements and next plan'}});fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Save draft'}));await waitFor(()=>expect(reportWrites()).toHaveLength(1));const b=JSON.parse(String(reportWrites()[0][1]?.body));expect(b).toMatchObject({submit:false,consent:true,expected_version:0,summary:'My achievements and next plan',entries:[{day,prayers:5,literature:10,organization:30,quran:null,hadith:null}]});expect(screen.getByLabelText('Quran study (pages)')).toBeTruthy();
});
it('loads a recorded day without making it dirty or duplicating it',async()=>{
 const day=fixture('DRAFT');await open();expect((screen.getByLabelText('Prayers (prayers)') as HTMLInputElement).value).toBe('0');expect((screen.getByLabelText('Quran study (pages)') as HTMLInputElement).value).toBe('');fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Save draft'}));await waitFor(()=>expect(reportWrites()).toHaveLength(1));expect(JSON.parse(String(reportWrites()[0][1]?.body)).entries).toHaveLength(1);expect(JSON.parse(String(reportWrites()[0][1]?.body)).entries[0].day).toBe(day);
});
it('warns before changing a month and lets the user retain daily edits',async()=>{
 fixture();await open();fireEvent.change(screen.getByLabelText('Daily notes'),{target:{value:'Unsaved note'}});fireEvent.change(screen.getByLabelText('Reporting month'),{target:{value:'2020-01'}});const dialog=screen.getByRole('dialog');expect(dialog.textContent).toContain('সংরক্ষণ না করা পরিবর্তন');fireEvent.click(screen.getByRole('button',{name:'ফিরে যান'}));expect((screen.getByLabelText('Daily notes') as HTMLTextAreaElement).value).toBe('Unsaved note');expect(reportWrites()).toHaveLength(0);
});
it('requires final submission confirmation and locks a submitted book',async()=>{
 fixture('DRAFT');await open();fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Submit for review'}));expect(screen.getByRole('dialog').textContent).toContain('জমা দেওয়ার পর');expect(reportWrites()).toHaveLength(0);fireEvent.click(screen.getByRole('button',{name:'Cancel submission'}));expect(reportWrites()).toHaveLength(0);fireEvent.click(screen.getByRole('button',{name:'Submit for review'}));fireEvent.click(screen.getByRole('button',{name:'Confirm submission'}));await waitFor(()=>expect(reportWrites()).toHaveLength(1));expect(JSON.parse(String(reportWrites()[0][1]?.body)).submit).toBe(true);await waitFor(()=>expect((screen.getByLabelText('Monthly summary') as HTMLTextAreaElement).disabled).toBe(true));expect(screen.queryByRole('button',{name:'Save draft'})).toBeNull();
});
it('keeps review restrictions and downloads only saved reports',async()=>{
 fixture('SUBMITTED',false);await open();expect(screen.getByLabelText('Prayers (prayers)').matches(':disabled')).toBe(true);expect(screen.queryByRole('button',{name:'Submit for review'})).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Download PDF'}));await waitFor(()=>expect(downloadPersonalReport).toHaveBeenCalledWith('r1','pdf'));expect(reportWrites()).toHaveLength(0);
});
it('shows returned feedback and permits corrections while missing reviewers block submission',async()=>{
 fixture('RETURNED',false);await open();expect(screen.getByText('Please correct the dates')).toBeTruthy();expect((screen.getByLabelText('Monthly summary') as HTMLTextAreaElement).disabled).toBe(false);fireEvent.click(screen.getByRole('checkbox'));expect((screen.getByRole('button',{name:'Submit for review'}) as HTMLButtonElement).disabled).toBe(true);expect((screen.getByRole('button',{name:'Save draft'}) as HTMLButtonElement).disabled).toBe(false);
});

it('reopens a just-added day and preserves its other values when correcting one metric',async()=>{
 const day=fixture();await open();fireEvent.change(screen.getByLabelText('Prayers (prayers)'),{target:{value:'5'}});fireEvent.change(screen.getByLabelText('Literature (pages)'),{target:{value:'10'}});fireEvent.click(screen.getByRole('button',{name:'Add / update day'}));expect((screen.getByLabelText('Literature (pages)') as HTMLInputElement).value).toBe('');fireEvent.click(screen.getByRole('button',{name:'Edit '+day}));expect((screen.getByLabelText('Literature (pages)') as HTMLInputElement).value).toBe('10');fireEvent.change(screen.getByLabelText('Prayers (prayers)'),{target:{value:'4'}});fireEvent.click(screen.getByRole('button',{name:'Add / update day'}));fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Save draft'}));await waitFor(()=>expect(reportWrites()).toHaveLength(1));const entries=JSON.parse(String(reportWrites()[0][1]?.body)).entries;expect(entries).toHaveLength(1);expect(entries[0]).toMatchObject({prayers:4,literature:10});
});

it('blocks Salah above five while allowing zero and shows a separate monthly ceiling',async()=>{
 fixture();await open();const input=screen.getByLabelText('Prayers (prayers)') as HTMLInputElement;expect(input.max).toBe('5');fireEvent.change(input,{target:{value:'6'}});expect(input.value).toBe('');expect(screen.getByRole('alert').textContent).toContain('০ থেকে ৫');fireEvent.change(input,{target:{value:'0'}});expect(input.value).toBe('0');expect(screen.queryByRole('alert')).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Add / update day'}));const summary=screen.getByRole('region',{name:'Monthly Salah summary'});expect(summary.textContent).toContain('রিপোর্ট করা মোট: ০ ওয়াক্ত');expect(summary.textContent).toContain('মাসিক সর্বোচ্চ');
});
it('calculates full calendar ceilings for short, long and leap-year months',async()=>{
 const {salahSummary}=await import('@/lib/report-book');for(const [month,days] of [['2026-11',30],['2026-01',31],['2025-02',28],['2024-02',29]] as const){expect(salahSummary(month,[{day:month+'-01',prayers:5,quran:null,hadith:null,literature:null,organization:null,notes:''},{day:month+'-02',prayers:0,quran:null,hadith:null,literature:null,organization:null,notes:''},{day:month+'-03',prayers:null,quran:2,hadith:null,literature:null,organization:null,notes:''}])).toMatchObject({days,maximum:days*5,reportedDays:2,unreportedDays:days-2,total:5,invalid:false});}
});
