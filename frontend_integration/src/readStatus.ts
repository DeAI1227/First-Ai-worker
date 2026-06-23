import { supabase } from "./supabaseClient";

export async function markEventRead(userId: string, eventId: string) {
  return supabase.from("user_read_status").upsert({
    user_id: userId,
    item_type: "event",
    item_id: eventId,
    is_read: true,
    read_at: new Date().toISOString(),
  });
}

export async function markReportRead(userId: string, reportId: string) {
  return supabase.from("user_read_status").upsert({
    user_id: userId,
    item_type: "report",
    item_id: reportId,
    is_read: true,
    read_at: new Date().toISOString(),
  });
}

