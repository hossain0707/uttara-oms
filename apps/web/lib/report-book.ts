export const reportMetrics = [
 {key:'prayers',label:'Prayers',unit:'prayers',bn:'সালাত',bnUnit:'ওয়াক্ত',max:5},
 {key:'quran',label:'Quran study',unit:'pages',bn:'কুরআন অধ্যয়ন',bnUnit:'পৃষ্ঠা',max:100000},
 {key:'hadith',label:'Hadith study',unit:'items',bn:'হাদিস অধ্যয়ন',bnUnit:'টি',max:100000},
 {key:'literature',label:'Literature',unit:'pages',bn:'সাহিত্য অধ্যয়ন',bnUnit:'পৃষ্ঠা',max:100000},
 {key:'organization',label:'Organizational work',unit:'minutes',bn:'সাংগঠনিক কাজ',bnUnit:'মিনিট',max:1440},
] as const;
export type ReportMetric=typeof reportMetrics[number]['key'];
export type ReportEntry={day:string;notes:string}&Record<ReportMetric,number|null>&Partial<Record<typeof extraReportMetrics[number]["key"],number|null>>&Partial<Record<typeof checkReportMetrics[number]["key"],boolean|null>>;
export type ReportGoal={metric:string;target:number};
export type PersonalReport={id:string;month:string;version:number;status:string;entries:ReportEntry[];summary:string;totals:Record<string,number>;review_note:string|null;entered_days:number;goals?:ReportGoal[];achievements?:string;incomplete_work?:string;next_plan?:string};
export const reportToday=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Dhaka',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
export const bnNumber=(value:number)=>new Intl.NumberFormat('bn-BD').format(value);
export const reportDate=(value:string,month=false)=>new Intl.DateTimeFormat('bn-BD',{timeZone:'UTC',...(month?{month:'long' as const,year:'numeric' as const}:{day:'numeric' as const,month:'long' as const,year:'numeric' as const})}).format(new Date(value+'T12:00:00Z'));
export function entryTotals(entries:ReportEntry[]){return Object.fromEntries(reportMetrics.map(m=>[m.key,entries.reduce((sum,e)=>sum+(e[m.key]??0),0)])) as Record<ReportMetric,number>;}

export const extraReportMetrics=[
 {key:'congregational_prayers',label:'Congregational prayers',unit:'prayers',bn:'জামাতে সালাত',bnUnit:'ওয়াক্ত',max:5},
 {key:'dawah_meetings',label:'Dawah meetings',unit:'times',bn:'দাওয়াতি সাক্ষাৎ',bnUnit:'বার',max:100000},
 {key:'worker_meetings',label:'Worker meetings',unit:'times',bn:'কর্মী সাক্ষাৎ',bnUnit:'বার',max:100000},
 {key:'member_meetings',label:'Member meetings',unit:'times',bn:'সদস্য সাক্ষাৎ',bnUnit:'বার',max:100000},
 {key:'worker_contacts',label:'Worker contacts',unit:'times',bn:'কর্মী যোগাযোগ',bnUnit:'বার',max:100000},
 {key:'books_distributed',label:'Books distributed',unit:'books',bn:'বই বিতরণ',bnUnit:'টি',max:100000},
 {key:'donated_hours',label:'Time donated',unit:'hours',bn:'সময় দান',bnUnit:'ঘণ্টা',max:24},
 {key:'visits',label:'Visits',unit:'times',bn:'সফর',bnUnit:'বার',max:100000},
] as const;
export const checkReportMetrics=[
 {key:'quran_studied',label:'Quran studied',bn:'কুরআন অধ্যয়ন'},
 {key:'family_meeting',label:'Family meeting',bn:'পারিবারিক বৈঠক'},
 {key:'social_work',label:'Social work',bn:'সামাজিক কাজ'},
 {key:'report_kept',label:'Report kept',bn:'রিপোর্ট রাখা'},
 {key:'self_evaluation',label:'Self evaluation',bn:'আত্মসমালোচনা'},
] as const;
export const numericReportFields=[...reportMetrics,...extraReportMetrics].map(m=>({...m,kind:'number' as const,step:m.key==='donated_hours'?0.01:1}));
const checks=checkReportMetrics.map(m=>({...m,kind:'check' as const,bnUnit:'দিন',unit:'days'}));
export const dailyReportFields=[checks[0],...numericReportFields.filter(m=>['hadith','literature','prayers','congregational_prayers','dawah_meetings','worker_meetings','member_meetings','worker_contacts','books_distributed'].includes(m.key)),checks[1],checks[2],...numericReportFields.filter(m=>['donated_hours','visits'].includes(m.key)),checks[3],checks[4],...numericReportFields.filter(m=>['quran','organization'].includes(m.key))];
export type DailyField=typeof dailyReportFields[number];
export type Reflections={achievements:string;incomplete_work:string;next_plan:string};
export const reflectionFields=[{key:'achievements',label:'Achievements',bn:'মাসের অর্জন'},{key:'incomplete_work',label:'Incomplete work',bn:'অসম্পূর্ণ কাজ'},{key:'next_plan',label:'Next month plan',bn:'আগামী মাসের পরিকল্পনা'}] as const;
export function activityTotals(entries:ReportEntry[]){return Object.fromEntries(dailyReportFields.map(m=>[m.key,Math.round(entries.reduce((sum,e)=>sum+(m.kind==='check'?(e[m.key]===true?1:0):Number(e[m.key]??0)),0)*100)/100]));}
export const activityReportedDays=(entries:ReportEntry[],key:DailyField['key'])=>entries.filter(e=>e[key]!==null&&e[key]!==undefined).length;
