import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import AuthScreen from '@/components/AuthScreen';
import {authClient} from '@/lib/supabase';
vi.mock('@/lib/supabase',()=>({authClient:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
function auth(overrides:Record<string,unknown>={}){const a={mfa:{getAuthenticatorAssuranceLevel:vi.fn().mockResolvedValue({data:{currentLevel:"aal1",nextLevel:"aal1"},error:null})},signInWithPassword:vi.fn().mockResolvedValue({error:null}),signUp:vi.fn().mockResolvedValue({data:{session:null},error:null}),verifyOtp:vi.fn().mockResolvedValue({error:null}),resetPasswordForEmail:vi.fn().mockResolvedValue({error:null}),updateUser:vi.fn().mockResolvedValue({error:null}),signOut:vi.fn().mockResolvedValue({error:null}),getSession:vi.fn().mockResolvedValue({data:{session:null},error:null}),onAuthStateChange:vi.fn().mockReturnValue({data:{subscription:{unsubscribe:vi.fn()}}}),...overrides};vi.mocked(authClient).mockReturnValue({auth:a} as never);return a;}
it('logs in with an email and unchanged password, with accessible visibility and account links',async()=>{
 const a=auth(),done=vi.fn();render(<AuthScreen onAuthenticated={done}/>);
 fireEvent.change(screen.getByLabelText('Email'),{target:{value:'owner@example.invalid'}});fireEvent.change(screen.getByLabelText('Password'),{target:{value:' password with spaces '}});
 fireEvent.click(screen.getByRole('button',{name:'Show password'}));expect((screen.getByLabelText('Password') as HTMLInputElement).type).toBe('text');
 expect(screen.getByRole('link',{name:'Forgot Password?'}).getAttribute('href')?.replace(/\/$/,'')).toBe('/forgot-password');expect(screen.getByRole('link',{name:'Create an Account'}).getAttribute('href')?.replace(/\/$/,'')).toBe('/signup');
 fireEvent.click(screen.getByRole('button',{name:'LOGIN'}));await waitFor(()=>expect(a.signInWithPassword).toHaveBeenCalledWith({email:'owner@example.invalid',password:' password with spaces '}));expect(done).toHaveBeenCalledOnce();
});
it('keeps a failed password login on the form without claiming success',async()=>{
 const a=auth({signInWithPassword:vi.fn().mockResolvedValue({error:new Error('Invalid login credentials')})}),done=vi.fn();render(<AuthScreen onAuthenticated={done}/>);
 fireEvent.change(screen.getByLabelText('Email'),{target:{value:'owner@example.invalid'}});fireEvent.change(screen.getByLabelText('Password'),{target:{value:'incorrect'}});fireEvent.click(screen.getByRole('button',{name:'LOGIN'}));await screen.findByRole('alert');expect(done).not.toHaveBeenCalled();expect(a.signInWithPassword).toHaveBeenCalledOnce();
});
it('checks password confirmation, then requires email confirmation before completing signup',async()=>{
 const a=auth(),done=vi.fn();render(<AuthScreen mode="signup" onAuthenticated={done}/>);
 fireEvent.change(screen.getByLabelText('Email'),{target:{value:'new@example.invalid'}});fireEvent.change(screen.getByLabelText('Password'),{target:{value:'synthetic-password'}});fireEvent.change(screen.getByLabelText('Confirm password'),{target:{value:'different-password'}});fireEvent.click(screen.getByRole('button',{name:'CREATE ACCOUNT'}));await screen.findByText('The passwords don’t match. Please check them.');expect(a.signUp).not.toHaveBeenCalled();
 fireEvent.change(screen.getByLabelText('Confirm password'),{target:{value:'synthetic-password'}});fireEvent.click(screen.getByRole('button',{name:'CREATE ACCOUNT'}));await screen.findByLabelText('Email verification code');expect(done).not.toHaveBeenCalled();
 fireEvent.change(screen.getByLabelText('Email verification code'),{target:{value:'123456'}});fireEvent.click(screen.getByRole('button',{name:'Verify email'}));await waitFor(()=>expect(a.verifyOtp).toHaveBeenCalledWith({email:'new@example.invalid',token:'123456',type:'signup'}));expect(done).toHaveBeenCalledOnce();
});
it('requests recovery for the dedicated route without revealing account existence',async()=>{
 const a=auth();render(<AuthScreen mode="forgot"/>);fireEvent.change(screen.getByLabelText('Email'),{target:{value:'owner@example.invalid'}});fireEvent.click(screen.getByRole('button',{name:'Send reset link'}));await screen.findByText(/If this address can receive a reset email/);expect(a.resetPasswordForEmail).toHaveBeenCalledWith('owner@example.invalid',{redirectTo:window.location.origin+'/reset-password/'});expect((screen.getByRole('button',{name:'Resend in 60s'}) as HTMLButtonElement).disabled).toBe(true);
});
it('rejects a reset page without a session and never updates a password',async()=>{
 const a=auth();render(<AuthScreen mode="reset"/>);await screen.findByRole('link',{name:'Request a new reset link'});expect(screen.queryByLabelText('New password')).toBeNull();expect(a.updateUser).not.toHaveBeenCalled();
});
it('updates a valid recovery session, signs out, and returns to login only after success',async()=>{
 const a=auth({getSession:vi.fn().mockResolvedValue({data:{session:{access_token:'synthetic'}},error:null})});render(<AuthScreen mode="reset"/>);await screen.findByLabelText('New password');fireEvent.change(screen.getByLabelText('New password'),{target:{value:'new-synthetic-password'}});fireEvent.change(screen.getByLabelText('Confirm password'),{target:{value:'new-synthetic-password'}});fireEvent.click(screen.getByRole('button',{name:'Save new password'}));await screen.findByRole('link',{name:'Back to sign in'});expect(a.updateUser).toHaveBeenCalledWith({password:'new-synthetic-password'});expect(a.signOut).toHaveBeenCalledOnce();
});
it('does not claim a password was changed or sign out when the provider rejects the update',async()=>{
 const a=auth({getSession:vi.fn().mockResolvedValue({data:{session:{access_token:'synthetic'}},error:null}),updateUser:vi.fn().mockResolvedValue({error:new Error('Recovery session expired')})});render(<AuthScreen mode="reset"/>);await screen.findByLabelText('New password');fireEvent.change(screen.getByLabelText('New password'),{target:{value:'new-synthetic-password'}});fireEvent.change(screen.getByLabelText('Confirm password'),{target:{value:'new-synthetic-password'}});fireEvent.click(screen.getByRole('button',{name:'Save new password'}));await screen.findByText('Recovery session expired');expect(a.signOut).not.toHaveBeenCalled();expect(screen.queryByText(/Your password has been updated/)).toBeNull();
});
it('requires the enrolled authenticator before changing a recovered leader password',async()=>{
 const a=auth({getSession:vi.fn().mockResolvedValue({data:{session:{access_token:'synthetic'}},error:null}),mfa:{getAuthenticatorAssuranceLevel:vi.fn().mockResolvedValue({data:{currentLevel:'aal1',nextLevel:'aal2'},error:null}),listFactors:vi.fn().mockResolvedValue({data:{all:[{id:'synthetic-factor',factor_type:'totp',status:'verified'}]},error:null})}});render(<AuthScreen mode="reset"/>);await screen.findByLabelText('Authenticator code');expect(screen.queryByLabelText('New password')).toBeNull();expect(a.updateUser).not.toHaveBeenCalled();
});
