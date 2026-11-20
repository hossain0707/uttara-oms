import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent} from '@testing-library/react';
import {useState} from 'react';
import SearchSelect,{matchesChoice,type Choice} from '@/components/SearchSelect';
import AddressFields from '@/components/AddressFields';
import catalogs from '@/data/catalogs.json';
import geo from '@/data/bangladesh.json';
afterEach(cleanup);
it('matches Bengali prefixes, English keywords and spelling aliases',()=>{
 const x:Choice={id:'uttara',name:'Uttara Model Thana',bn:'উত্তরা মডেল থানা',aliases:['Uttora'],group:'Dhaka'};
 for(const q of ['উত্ত','UTT','uttora','model dhaka']) expect(matchesChoice(x,q)).toBe(true);
 expect(matchesChoice(x,'Chattogram')).toBe(false);
 expect(catalogs.books.filter(b=>matchesChoice(b,'namaz'))).toHaveLength(1);
});
it('supports keyboard selection and preserves a custom unlisted value',()=>{
 const select=vi.fn(),change=vi.fn();
 render(<SearchSelect label="Profession" value="eng" onChange={change} onSelect={select} items={catalogs.occupations}/>);
 const input=screen.getByRole('combobox');fireEvent.focus(input);fireEvent.keyDown(input,{key:'ArrowDown'});fireEvent.keyDown(input,{key:'Enter'});
 expect(select).toHaveBeenCalledWith(expect.objectContaining({name:'Engineer'}));
 expect(change).toHaveBeenCalledWith('প্রকৌশলী');
 fireEvent.change(input,{target:{value:'My custom profession'}});expect(change).toHaveBeenLastCalledWith('My custom profession');
});
it('finds Uttara by keyword, fills its parents, applies only on request and clears dependent selection',()=>{
 function Form(){const [value,setValue]=useState('Existing private road');return <AddressFields label="Current address" value={value} onChange={setValue}/>}
 render(<Form/>);
 const find=screen.getByLabelText('Current address — Find any location / স্থান খুঁজুন');
 fireEvent.focus(find);fireEvent.change(find,{target:{value:'uttara model'}});
 fireEvent.click(screen.getByRole('option',{name:/উত্তরা মডেল থানা/}));
 expect((screen.getByLabelText('Current address') as HTMLTextAreaElement).value).toBe('Existing private road');
 fireEvent.click(screen.getByRole('button',{name:'Use selected current address'}));
 expect((screen.getByLabelText('Current address') as HTMLTextAreaElement).value).toContain('Uttara Model Thana');
 expect((screen.getByLabelText('Current address') as HTMLTextAreaElement).value).toContain('Dhaka');
 const division=screen.getByLabelText('Current address — 1. Division / বিভাগ');
 fireEvent.focus(division);fireEvent.change(division,{target:{value:'raj'}});fireEvent.click(screen.getByRole('option',{name:/রাজশাহী/}));
 expect((screen.getByLabelText('Current address — 2. District / জেলা') as HTMLInputElement).value).toBe('');
 expect((screen.getByLabelText('Current address — 3. Upazila / thana / উপজেলা / থানা') as HTMLInputElement).disabled).toBe(true);
});
it('bundles complete snapshot parent links and bounded catalog values without defining permission grants',()=>{
 expect(geo.divisions).toHaveLength(8);expect(geo.districts).toHaveLength(64);
 const div=new Set(geo.divisions.map(x=>x.id)),district=new Set(geo.districts.map(x=>x.id)),up=new Set(geo.upazilas.map(x=>x.id));
 expect(geo.districts.every(x=>div.has(x.parent))).toBe(true);
 expect(geo.upazilas.every(x=>district.has(x.parent))).toBe(true);
 expect(geo.unions.every(x=>up.has(x.parent))).toBe(true);
 expect(catalogs.books.every(x=>x.bn.length<=250)).toBe(true);
 expect(new Set(catalogs.books.map(x=>x.bn)).size).toBe(catalogs.books.length);
 expect(catalogs.positions.every(x=>!('role' in x))).toBe(true);
});
