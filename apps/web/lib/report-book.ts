export const reportMetrics = [
 {key:'prayers',label:'Prayers',unit:'prayers',bn:'সালাত',bnUnit:'ওয়াক্ত',max:5},
 {key:'quran',label:'Quran study',unit:'pages',bn:'কুরআন অধ্যয়ন',bnUnit:'পৃষ্ঠা',max:100000},
 {key:'hadith',label:'Hadith study',unit:'items',bn:'হাদিস অধ্যয়ন',bnUnit:'টি',max:100000},
 {key:'literature',label:'Literature',unit:'pages',bn:'সাহিত্য অধ্যয়ন',bnUnit:'পৃষ্ঠা',max:100000},
 {key:'organization',label:'Organizational work',unit:'minutes',bn:'সাংগঠনিক কাজ',bnUnit:'মিনিট',max:1440},
] as const;
export type ReportMetric=typeof reportMetrics[number]['key'];
export type ReportEntry={day:string;notes:string}&Record<ReportMetric,number|null>;
export type ReportGoal={metric:string;target:number};
export type PersonalReport={id:string;month:string;version:number;status:string;entries:ReportEntry[];summary:string;totals:Record<string,number>;review_note:string|null;entered_days:number;goals?:ReportGoal[]};
export const reportToday=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Dhaka',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
export const bnNumber=(value:number)=>new Intl.NumberFormat('bn-BD').format(value);
export const reportDate=(value:string,month=false)=>new Intl.DateTimeFormat('bn-BD',{timeZone:'UTC',...(month?{month:'long' as const,year:'numeric' as const}:{day:'numeric' as const,month:'long' as const,year:'numeric' as const})}).format(new Date(value+'T12:00:00Z'));
export function entryTotals(entries:ReportEntry[]){return Object.fromEntries(reportMetrics.map(m=>[m.key,entries.reduce((sum,e)=>sum+(e[m.key]??0),0)])) as Record<ReportMetric,number>;}

export function salahSummary(month:string,entries:ReportEntry[]){
 const days=new Date(Number(month.slice(0,4)),Number(month.slice(5,7)),0).getDate();
 const reported=entries.filter(e=>e.prayers!==null&&e.prayers!==undefined);
 return {days,maximum:days*5,reportedDays:reported.length,unreportedDays:days-reported.length,total:reported.reduce((sum,e)=>sum+(e.prayers??0),0),invalid:reported.some(e=>!Number.isInteger(e.prayers)||e.prayers!<0||e.prayers!>5)};
}
