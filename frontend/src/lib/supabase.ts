import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

export function getSupabaseConfigError(): string | null {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    return "Missing Supabase environment variables. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.";
  }

  return null;
}

export function getSupabaseClient(): SupabaseClient {
  if (client) {
    return client;
  }

  const configError = getSupabaseConfigError();
  if (configError) {
    throw new Error(configError);
  }

  const url = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  client = createClient(url, anonKey);
  return client;
}
