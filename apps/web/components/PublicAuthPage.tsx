"use client";
import {useEffect} from "react";
import AuthScreen, {type AuthMode} from "./AuthScreen";
import {authClient} from "@/lib/supabase";
export default function PublicAuthPage({mode}:{mode:AuthMode}){
  useEffect(()=>{
    if(mode==="reset")return;
    const {data}=authClient().auth.onAuthStateChange((event)=>{
      if(event==="PASSWORD_RECOVERY")window.location.replace("/reset-password/");
      else if(event==="SIGNED_IN"||event==="MFA_CHALLENGE_VERIFIED")window.location.replace("/my/");
    });
    return()=>data.subscription.unsubscribe();
  },[mode]);
  return <AuthScreen mode={mode}/>;
}
