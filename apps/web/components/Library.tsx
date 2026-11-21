"use client";
import { useMemo, useState } from "react";
import { BookOpen, Search, Headphones, LibraryBig, Check, Plus } from "lucide-react";
import "./Library.css";
import library from "@/data/library.json";
import catalogs from "@/data/catalogs.json";

export type ReadingBook = { title: string; total_pages: number; completed_pages: number };
const normalize = (s: string) => s.normalize("NFKC").toLowerCase().replace(/[।.,’'\s-]+/g, " ").trim();
const sectionNames: Record<string,string> = {
  "আল কুরআন":"Quran", "আল-কুরআন":"Quran", "আল – কুরআন":"Quran",
  "আল হাদিস":"Hadith", "আল-হাদিস":"Hadith", "আল – হাদীস":"Hadith",
  "আল ফিকাহ":"Fiqh", "আল ফিক্‌হ":"Fiqh", "আল-ফিকহ":"Fiqh", "আল ফিকহ":"Fiqh",
  "দাওয়াত ও তাবলিগ":"Dawah", "আন্দোলন ও সংগঠন":"Organization", "ইসলামী আন্দোলন ও সংগঠন":"Organization",
  "ইসলাম ও ইবাদাত":"Worship", "সিরাত ও ইতিহাস":"Seerah & history", "সিরাতে রাসূল (রা.)":"Seerah",
  "পারিবারিক ও সামাজিক জীবন":"Family & society", "পারিবারিক জীবন ও সামাজিক সম্পর্ক":"Family & society",
  "ঈমান ও আক্বীদাহ":"Faith", "ঈমান-আক্বীদাহ":"Faith", "আমল-আখলাক ও মুয়ামালাত":"Character & conduct",
  "আমল-আখলাক ও মু‘আমালাত":"Character & conduct", "সিরাতে সাহাবা":"Companions", "রাজনীতি":"Politics",
  "অর্থনীতি":"Economics", "পারিবারিক জীবন":"Family", "সামাজিক জীবন":"Society", "নারী":"Women", "বিবিধ":"General study",
};
const aliases: Record<string,string> = {"196":"namaz roza prayer fasting", "1846":"asan fiqh fekah", "157":"sotter sakkhya testimony", "130":"islam porichiti", "500":"islam porichoy", "235":"hedayat guidance", "117":"choritro gothon character", "70":"iman faith", "94":"quran bujha sohoj"};
export function matchingBook(books: ReadingBook[], title: string) { return books.find(b=>normalize(b.title)===normalize(title)); }
export default function Library({books, onAdd, onManage, canAdd=true}:{books:ReadingBook[]; onAdd:(book:ReadingBook)=>void; onManage:()=>void; canAdd?:boolean}) {
  const [trackId,setTrackId]=useState("worker"), [section,setSection]=useState(""), [query,setQuery]=useState(""), [failed,setFailed]=useState<Record<string,boolean>>({}), [status,setStatus]=useState("");
  const track=library.tracks.find(t=>t.id===trackId)!;
  const sections=[...new Set(track.entries.map(e=>sectionNames[e.section]||e.section))];
  const entries=useMemo(()=>track.entries.filter(e=>{
    const topic=sectionNames[e.section]||e.section;
    const id=e.url.split('/').pop()!;
    const related=catalogs.books.filter(b=>normalize(b.bn||'')===normalize(e.title)).map(b=>[b.name,...b.aliases].join(' ')).join(' ');
    const haystack=normalize([e.label,topic,aliases[id]||'',related].join(' '));
    return (!section||topic===section)&&normalize(query).split(' ').every(word=>haystack.includes(word));
  }),[track,section,query]);
  const started=books.filter(b=>b.completed_pages>0).length, complete=books.filter(b=>b.total_pages>0&&b.completed_pages>=b.total_pages).length;
  return <div className="library-workspace">
    <div className="library-hero"><div><span className="library-kicker"><LibraryBig size={17}/> YOUR READING SPACE</span><h2>Learn. Reflect. Grow.</h2><p>Explore your syllabus, open a book and keep your reading in one place.</p><a href={track.url} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">View full syllabus on BJILibrary</a></div><BookOpen className="library-hero-icon" aria-hidden="true" size={110}/></div>
    <div className="library-layout"><div className="library-main">
      <div className="library-controls"><label>Syllabus<select value={trackId} onChange={e=>{setTrackId(e.target.value);setSection('');setStatus('');}}>{library.tracks.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label><label className="library-search"><span><Search size={17}/> Find a book</span><input value={query} placeholder="e.g. Namaz" onChange={e=>setQuery(e.target.value)}/></label></div>
      <div className="library-subjects" aria-label="Book subjects"><button type="button" aria-pressed={!section} onClick={()=>setSection('')}>All subjects</button>{sections.map(s=><button key={s} type="button" aria-pressed={section===s} onClick={()=>setSection(s)}>{s}</button>)}</div>
      <div className="library-results"><h3>{track.name}</h3><span>{entries.length} book links</span></div>
      <p className="library-source-note">Browse this track freely. It does not change your assigned targets or category. Check the full syllabus for memorization, chapters, volumes and alternative reading options.</p>
      {status&&<p className="success-msg" role="status">{status}</p>}
      <div className="library-grid">{entries.map((e,i)=>{const book=matchingBook(books,e.title);const topic=sectionNames[e.section]||e.section;return <article className="library-book" key={e.url}>
        <a className={'library-cover tone-'+i%4} href={e.url} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer" aria-label={'Read '+e.title+' on BJILibrary'}>{e.cover&&!failed[e.url]?<img src={e.cover} alt={e.title} loading="lazy" referrerPolicy="no-referrer" onError={()=>setFailed(f=>({...f,[e.url]:true}))}/>:<div className="library-title-cover"><BookOpen size={27}/><strong lang="bn">{e.title}</strong><span>{topic}</span></div>}</a>
        <div className="library-book-body"><span className="library-topic">{topic}</span><h4 lang="bn">{e.title}</h4>{(e.alternative||e.scope)&&<p className="library-requirement">{e.alternative?'Section includes reading alternatives. ':'Limited chapters may apply. '}See full syllabus.</p>}
        {book&&<p className="library-progress-label">{book.total_pages>0?`${book.completed_pages} / ${book.total_pages} pages`:(book.completed_pages>0?`${book.completed_pages} pages read`:'In your reading list')}</p>}
        <a className="library-read" href={e.url} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">Read on BJILibrary</a><button type="button" disabled={!canAdd||!!book||books.length>=100} onClick={()=>{onAdd({title:e.title,total_pages:0,completed_pages:0});setStatus('Added to your reading form. Open My reading list and save reading progress to keep it.');}}>{book?<Check size={15}/>:<Plus size={15}/>} {book?'In my reading list':'Add to my reading'}</button></div>
      </article>})}</div>
      {!entries.length&&<div className="library-empty"><BookOpen size={32}/><h3>No matching books</h3><p>Try a different title or subject.</p><button type="button" onClick={()=>{setQuery('');setSection('');}}>Clear filters</button></div>}
    </div><aside className="library-aside"><section><span className="library-kicker">MY READING</span><h3>A little every day</h3><p>Your own reading list, across all syllabuses.</p><div className="library-stats"><div><strong>{books.length}</strong><span>Added</span></div><div><strong>{started}</strong><span>Started</span></div><div><strong>{complete}</strong><span>Finished</span></div></div><button type="button" className="primary-btn wide" onClick={onManage}>My reading list</button><p className="library-source-note">Counts include unsaved form changes. Save reading progress to keep them.</p></section><section><Headphones size={24}/><h3>Listen and explore</h3><p>Find audio books and other study resources at the original library.</p><a href="https://bjilibrary.com/audio-books" target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">Browse audio books</a><a href="https://bjilibrary.com/report" target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">Report resources</a></section><p className="library-source-note">Source: BJILibrary · Checked {library.checked_on}. Covers are linked from the original library; unavailable covers show the title. Your private reports stay in OMS.</p>{!canAdd&&<p>Save your profile and consent in My profile before adding reading entries.</p>}</aside></div>
  </div>;
}
