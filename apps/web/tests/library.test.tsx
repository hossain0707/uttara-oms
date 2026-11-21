import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, render, screen, fireEvent} from '@testing-library/react';
import Library from '@/components/Library';
import library from '@/data/library.json';
afterEach(cleanup);
it('searches by English keywords, filters subjects and links directly to the source',()=>{
 render(<Library books={[]} onAdd={vi.fn()} onManage={vi.fn()}/>);
 fireEvent.change(screen.getByLabelText('Find a book'),{target:{value:'namaz'}});
 expect(screen.getByRole('link',{name:'Read on BJILibrary'}).getAttribute('href')).toBe('https://bjilibrary.com/196');
 expect(screen.getByRole('link',{name:'Read on BJILibrary'}).getAttribute('rel')).toContain('noreferrer');
 fireEvent.change(screen.getByLabelText('Syllabus'),{target:{value:'rukon-b'}});
 expect(screen.getByRole('link',{name:'View full syllabus on BJILibrary'}).getAttribute('href')).toBe('https://bjilibrary.com/member-syllabus/educated-member-syllabus');
 fireEvent.change(screen.getByLabelText('Find a book'),{target:{value:'not a real title'}});
 expect(screen.getByRole('heading',{name:'No matching books'})).toBeTruthy();
});
it('stages a book without changing progress and prevents a duplicate reading entry',()=>{
 const add=vi.fn(); const book=library.tracks[0].entries[0];
 const view=render(<Library books={[]} onAdd={add} onManage={vi.fn()}/>);
 fireEvent.click(screen.getAllByRole('button',{name:'Add to my reading'})[0]);
 expect(add).toHaveBeenCalledWith({title:book.title,total_pages:0,completed_pages:0});
 view.rerender(<Library books={[{title:book.title,total_pages:100,completed_pages:25}]} onAdd={add} onManage={vi.fn()}/>);
 expect((screen.getByRole('button',{name:'In my reading list'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByText('25 / 100 pages')).toBeTruthy();
});
it('keeps catalog links and cover URLs confined to the verified library origin',()=>{
 for(const track of library.tracks){expect(new Set(track.entries.map(e=>e.url)).size).toBe(track.entries.length);for(const e of track.entries){expect(new URL(e.url).origin).toBe('https://bjilibrary.com');if(e.cover)expect(new URL(e.cover).origin).toBe('https://bjilibrary.com');expect(e.title.length).toBeLessThanOrEqual(250);}}
});
