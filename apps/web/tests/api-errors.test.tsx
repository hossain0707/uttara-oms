import {afterEach, expect, it, vi} from 'vitest';
vi.mock('@/lib/supabase', () => ({authClient: () => ({auth:{getSession:async()=>({data:{session:{access_token:'synthetic-token'}}})}})}));
import {api} from '@/lib/api';
afterEach(()=>vi.unstubAllGlobals());
it('turns nested validation details into readable field errors without echoing submitted data', async()=>{
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok:false,status:422,json:async()=>({detail:[{loc:['body','details','books',0,'title'],msg:'String should have at least 1 character',input:'private synthetic input'}]})}));
  await expect(api('/self/profile')).rejects.toThrow('books → #1 → title: String should have at least 1 character');
});
