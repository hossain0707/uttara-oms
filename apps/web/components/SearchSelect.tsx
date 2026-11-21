"use client";
import {useId, useState} from 'react';
export type Choice = {id:string; name:string; bn?:string; aliases?:string[]; group?:string};
export const searchText = (value:string) => value.normalize('NFKC').toLocaleLowerCase().replace(/[\u200c\u200d]/g,'').replace(/\s+/g,' ').trim();
export function matchesChoice(item:Choice, query:string) {
  const text=searchText([item.name,item.bn,...(item.aliases||[]),item.group].filter(Boolean).join(' '));
  return searchText(query).split(' ').every(word=>text.includes(word));
}
export default function SearchSelect({label,value,onChange,onSelect,items,disabled=false,placeholder='',maxLength=250}:{label:string;value:string;onChange:(value:string)=>void;onSelect?:(item:Choice)=>void;items:Choice[];disabled?:boolean;placeholder?:string;maxLength?:number}) {
  const id=useId(), [open,setOpen]=useState(false),[active,setActive]=useState(-1);
  const results=items.filter(x=>matchesChoice(x,value)).slice(0,30);
  const pick=(item:Choice)=>{onChange(item.bn||item.name);onSelect?.(item);setOpen(false);setActive(-1)};
  return <div className="form-field suggestion-field"><label htmlFor={id}>{label}</label><input id={id} className="input" role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={id+'-list'} aria-activedescendant={active>=0&&results[active]?id+'-'+active:undefined} autoComplete="off" maxLength={maxLength} disabled={disabled} placeholder={placeholder} value={value} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onChange={e=>{onChange(e.target.value);setOpen(true);setActive(-1)}} onKeyDown={e=>{if(e.nativeEvent.isComposing)return;if(e.key==='Escape')setOpen(false);if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setOpen(true);setActive(i=>e.key==='ArrowDown'?Math.min(i+1,results.length-1):Math.max(i-1,0));}if(e.key==='Enter'&&open){e.preventDefault();if(active>=0&&results[active])pick(results[active]);else if(results.length===1)pick(results[0]);}}}/>{open&&<div className="suggestion-menu"><ul role="listbox" id={id+'-list'} aria-label={label+' suggestions'}>{results.map((x,i)=><li role="option" id={id+'-'+i} aria-selected={i===active} key={x.id} onMouseDown={e=>e.preventDefault()} onClick={()=>pick(x)}><strong>{x.bn||x.name}</strong>{x.bn&&<span>{x.name}</span>}{x.group&&<small>{x.group.split(' / ')[0]}</small>}</li>)}</ul><p>{results.length ? 'Showing up to 30 matches. Type more to narrow the list.' : 'No listed match. You can keep your own wording.'}</p></div>}</div>;
}
