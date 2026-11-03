import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "https://ynpvbxtrfbcwficiwphg.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "";

if (!supabaseAnonKey && typeof window !== "undefined") {
  console.warn("SmartAttend: NEXT_PUBLIC_SUPABASE_ANON_KEY is not defined in environment variables.");
}

/**
 * Singleton Supabase Browser Client.
 * Uses public publishable/anon key with secure localStorage session persistence.
 * Service role keys are strictly excluded.
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storageKey: "smartattend_supabase_auth_token",
  },
});
