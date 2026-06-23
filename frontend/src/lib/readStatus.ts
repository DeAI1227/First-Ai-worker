import { getSupabaseClient } from "./supabase";

export async function markEventRead(userId: string, eventId: string): Promise<void> {
  const supabase = getSupabaseClient();
  const { error } = await supabase.from("user_read_status").upsert({
    user_id: userId,
    item_type: "event",
    item_id: eventId,
    is_read: true,
    read_at: new Date().toISOString(),
  });

  if (error) {
    throw error;
  }
}

export async function markReportRead(userId: string, reportId: string): Promise<void> {
  const supabase = getSupabaseClient();
  const { error } = await supabase.from("user_read_status").upsert({
    user_id: userId,
    item_type: "report",
    item_id: reportId,
    is_read: true,
    read_at: new Date().toISOString(),
  });

  if (error) {
    throw error;
  }
}
