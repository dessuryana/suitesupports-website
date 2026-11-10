// SuiteSupports billing — one Edge Function, three routes:
//   GET/POST /billing/pay      public: show an invoice/subscription by its secret link token, start a Xendit checkout
//   POST     /billing/admin    staff only (x-admin-key): clients, invoices, subscriptions, payments
//   POST     /billing/webhook  Xendit callbacks (x-callback-token)
// Card details are only ever entered on Xendit's hosted page; nothing card-related touches this code.
//
// Secrets (Supabase → Edge Functions → Secrets):
//   XENDIT_SECRET_KEY      Xendit secret API key (test key first, live key at go-live)
//   XENDIT_WEBHOOK_TOKEN   Xendit "Webhook verification token"
//   ADMIN_KEY              passphrase for billing-admin.html
//   SITE_URL               optional, default https://suitesupports.pro
//   ALLOWED_ORIGINS        optional, comma separated
//   XENDIT_CHANNELS        optional, default CARDS
import { createClient } from "jsr:@supabase/supabase-js@2";

const SITE = (Deno.env.get("SITE_URL") ?? "https://suitesupports.pro").replace(/\/$/, "");
const ORIGINS = (Deno.env.get("ALLOWED_ORIGINS") ??
  "https://suitesupports.pro,https://www.suitesupports.pro,http://127.0.0.1:8099,http://localhost:8099")
  .split(",").map((s) => s.trim()).filter(Boolean);
const CHANNELS = (Deno.env.get("XENDIT_CHANNELS") ?? "CARDS").split(",").map((s) => s.trim()).filter(Boolean);

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});

class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

function corsHeaders(req: Request): Record<string, string> {
  const o = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "Access-Control-Allow-Headers": "content-type, x-admin-key",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Vary": "Origin",
  };
}

function reply(req: Request, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(req), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function safeEqual(a: string, b: string) {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

function must<T>(res: { data: T; error: { message: string } | null }): T {
  if (res.error) throw new HttpError(500, res.error.message);
  return res.data;
}

const rand = () => crypto.getRandomValues(new Uint32Array(1))[0].toString(36);

async function xendit(path: string, body?: unknown, method = "POST") {
  const key = Deno.env.get("XENDIT_SECRET_KEY");
  if (!key) throw new HttpError(503, "Card payments are not switched on yet. Please contact SuiteSupports.");
  const res = await fetch("https://api.xendit.co" + path, {
    method,
    headers: { Authorization: "Basic " + btoa(key + ":"), "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let data: Record<string, unknown> = {};
  try { data = JSON.parse(text); } catch { /* non-JSON */ }
  if (!res.ok) {
    console.error("Xendit error", res.status, path, text.slice(0, 2000));
    throw new HttpError(502, `Payment provider error: ${data.message ?? data.error_code ?? res.status}`);
  }
  return data;
}

// ---------- shared lookups ----------
async function issuer() {
  const r = must(await db.from("settings").select("value").eq("key", "issuer").maybeSingle());
  return (r?.value ?? {}) as Record<string, string>;
}

async function findByToken(t: string) {
  if (!/^[0-9a-f]{36}$/.test(t)) throw new HttpError(404, "This payment link is not valid.");
  const inv = must(await db.from("invoices").select("*, client:clients(*)").eq("pay_token", t).maybeSingle());
  if (inv) return { kind: "invoice" as const, row: inv };
  const sub = must(await db.from("subscriptions").select("*, client:clients(*)").eq("pay_token", t).maybeSingle());
  if (sub) return { kind: "subscription" as const, row: sub };
  throw new HttpError(404, "This payment link is not valid.");
}

function publicView(kind: "invoice" | "subscription", r: any) {
  const base = { kind, client: r.client?.name ?? "", currency: r.currency, amount: r.amount, status: r.status };
  if (kind === "invoice") {
    return { ...base, number: r.number, description: r.description, items: r.items, subtotal: r.subtotal,
      tax_rate: Number(r.tax_rate), tax: r.tax, due_date: r.due_date, notes: r.notes, paid_at: r.paid_at,
      created_at: r.created_at };
  }
  return { ...base, plan_name: r.plan_name, start_date: r.start_date, activated_at: r.activated_at,
    last_charge_at: r.last_charge_at };
}

// Midnight in Jakarta (UTC+7) on the given date, never earlier than tomorrow.
function anchorFor(startDate: string) {
  const d = new Date(startDate + "T00:00:00+07:00");
  const tomorrow = new Date(Date.now() + 24 * 3600e3);
  if (d < tomorrow) {
    const t = new Date(tomorrow.getTime() + 7 * 3600e3); // shift to Jakarta wall clock
    return new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate()) - 7 * 3600e3).toISOString();
  }
  return d.toISOString();
}

// ---------- public: /pay ----------
async function handlePay(req: Request) {
  const url = new URL(req.url);
  if (req.method === "GET") {
    const { kind, row } = await findByToken(url.searchParams.get("t") ?? "");
    return reply(req, { ...publicView(kind, row), issuer: await issuer() });
  }
  if (req.method !== "POST") throw new HttpError(405, "Method not allowed");
  const { t } = await req.json().catch(() => ({}));
  const { kind, row } = await findByToken(String(t ?? ""));

  if (kind === "invoice" && row.status !== "open") throw new HttpError(409, row.status === "paid" ? "This invoice is already paid." : "This invoice is no longer payable.");
  if (kind === "subscription" && row.status !== "awaiting_card") {
    // Failed monthly charges are retried by Xendit, which also emails the payer a link; never start a second plan here.
    throw new HttpError(409, ["active", "pending", "past_due"].includes(row.status) ? "This subscription is already set up." : "This subscription is no longer available.");
  }

  // Reuse a checkout that is still open, so double clicks don't create duplicates.
  const col = kind === "invoice" ? "invoice_id" : "subscription_id";
  const open = must(await db.from("pay_sessions").select("url, expires_at").eq(col, row.id).eq("status", "ACTIVE")
    .gt("expires_at", new Date(Date.now() + 3 * 60e3).toISOString()).order("created_at", { ascending: false }).limit(1));
  if (open?.length) return reply(req, { url: open[0].url });

  const back = (r: string) => `${SITE}/pay.html?t=${row.pay_token}&r=${r}`;
  const body: Record<string, unknown> = {
    session_type: kind === "invoice" ? "PAY" : "SUBSCRIPTION",
    mode: "PAYMENT_LINK",
    amount: row.amount,
    currency: "IDR",
    country: "ID",
    allowed_payment_channels: CHANNELS,
    success_return_url: back("done"),
    cancel_return_url: back("cancel"),
    locale: "en",
  };
  if (kind === "invoice") {
    body.reference_id = `${row.number}-${rand()}`;
    body.capture_method = "AUTOMATIC";
    body.description = `${row.number} · ${row.description}`.slice(0, 1000);
  } else {
    body.reference_id = `SUB-${row.id.slice(0, 8)}-${rand()}`;
    body.description = `${row.plan_name} — monthly subscription`.slice(0, 1000);
    const c = row.client;
    if (c.xendit_customer_id) body.customer_id = c.xendit_customer_id;
    else {
      const customer: Record<string, unknown> = {
        reference_id: `ss-client-${c.id}`,
        type: "INDIVIDUAL",
        individual_detail: { given_names: (c.contact_name || c.name).slice(0, 50) },
      };
      if (c.email) customer.email = c.email;
      body.customer = customer;
    }
    body.subscription = {
      schedule: {
        interval: "MONTH", interval_count: 1, anchor_date: anchorFor(row.start_date),
        retry_interval: "DAY", retry_interval_count: 1, total_retry: 3, failed_attempt_notifications: [1, 2, 3],
      },
      failed_cycle_action: "RESUME",
      payment_link_for_failed_attempt: true,
    };
  }

  const s = await xendit("/sessions", body);
  const link = String(s.payment_link_url ?? "");
  if (!s.payment_session_id || !link) throw new HttpError(502, "Payment provider returned no checkout link.");
  must(await db.from("pay_sessions").insert({
    session_id: s.payment_session_id, reference_id: body.reference_id, kind, url: link,
    invoice_id: kind === "invoice" ? row.id : null, subscription_id: kind === "subscription" ? row.id : null,
    status: String(s.status ?? "ACTIVE"), expires_at: s.expires_at ?? new Date(Date.now() + 30 * 60e3).toISOString(),
  }));
  if (kind === "subscription" && s.customer_id && !row.client.xendit_customer_id) {
    must(await db.from("clients").update({ xendit_customer_id: s.customer_id }).eq("id", row.client.id));
  }
  return reply(req, { url: link });
}

// ---------- staff: /admin ----------
function int(v: unknown, name: string, min = 0) {
  const n = Number(v);
  if (!Number.isFinite(n) || Math.round(n) !== n || n < min) throw new HttpError(400, `${name} must be a whole number of at least ${min}.`);
  return n;
}
function text(v: unknown, name: string, max = 300, required = true) {
  const s = String(v ?? "").trim();
  if (required && !s) throw new HttpError(400, `${name} is required.`);
  if (s.length > max) throw new HttpError(400, `${name} is too long (max ${max} characters).`);
  return s || null;
}

async function handleAdmin(req: Request) {
  const key = Deno.env.get("ADMIN_KEY");
  if (!key) throw new HttpError(503, "ADMIN_KEY is not set on the server yet.");
  if (!safeEqual(req.headers.get("x-admin-key") ?? "", key)) {
    await new Promise((r) => setTimeout(r, 900));
    throw new HttpError(401, "Wrong admin key.");
  }
  if (req.method !== "POST") throw new HttpError(405, "Method not allowed");
  const p = await req.json().catch(() => ({}));

  switch (p.action) {
    case "status": {
      const k = Deno.env.get("XENDIT_SECRET_KEY") ?? "";
      return reply(req, {
        xendit_key: !k ? "missing" : /development|test/i.test(k) ? "test" : /production|live/i.test(k) ? "live" : "set",
        webhook_token: Boolean(Deno.env.get("XENDIT_WEBHOOK_TOKEN")),
        webhook_url: new URL(req.url).origin + "/functions/v1/billing/webhook",
        site: SITE,
      });
    }
    case "list": {
      const [clients, invoices, subscriptions, payments] = await Promise.all([
        db.from("clients").select("*").order("name"),
        db.from("invoices").select("*, client:clients(name)").order("created_at", { ascending: false }).limit(300),
        db.from("subscriptions").select("*, client:clients(name)").order("created_at", { ascending: false }).limit(300),
        db.from("payments").select("*, client:clients(name), invoice:invoices(number), subscription:subscriptions(plan_name)")
          .order("created_at", { ascending: false }).limit(300),
      ]);
      return reply(req, { site: SITE, issuer: await issuer(), clients: must(clients), invoices: must(invoices), subscriptions: must(subscriptions), payments: must(payments) });
    }
    case "save_client": {
      const row = {
        name: text(p.name, "Client name", 120),
        contact_name: text(p.contact_name, "Contact name", 50, false),
        email: text(p.email, "Email", 50, false),
        phone: text(p.phone, "Phone", 30, false),
        address: text(p.address, "Address", 300, false),
      };
      if (row.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(row.email)) throw new HttpError(400, "Email looks wrong.");
      const res = p.id ? await db.from("clients").update(row).eq("id", p.id).select().single()
        : await db.from("clients").insert(row).select().single();
      return reply(req, { client: must(res) });
    }
    case "save_issuer": {
      const value = {
        legal_name: text(p.legal_name, "Company name", 120),
        address: text(p.address, "Address", 300, false) ?? "",
        tax_id: text(p.tax_id, "NPWP", 40, false) ?? "",
        email: text(p.email, "Email", 80, false) ?? "",
        phone: text(p.phone, "Phone", 40, false) ?? "",
      };
      must(await db.from("settings").upsert({ key: "issuer", value, updated_at: new Date().toISOString() }));
      return reply(req, { issuer: value });
    }
    case "create_invoice": {
      const items = Array.isArray(p.items) ? p.items : [];
      if (!items.length || items.length > 30) throw new HttpError(400, "Add between 1 and 30 line items.");
      const clean = items.map((it: any, i: number) => ({
        name: text(it.name, `Item ${i + 1} name`, 200),
        qty: int(it.qty, `Item ${i + 1} quantity`, 1),
        unit_price: int(it.unit_price, `Item ${i + 1} price`, 0),
      }));
      const subtotal = clean.reduce((s: number, it: any) => s + it.qty * it.unit_price, 0);
      const taxRate = Number(p.tax_rate ?? 0);
      if (!(taxRate >= 0 && taxRate <= 100)) throw new HttpError(400, "Tax rate must be between 0 and 100.");
      const tax = Math.round((subtotal * taxRate) / 100);
      const amount = subtotal + tax;
      if (amount < 10000) throw new HttpError(400, "Invoice total must be at least Rp 10.000.");
      if (p.due_date && !/^\d{4}-\d{2}-\d{2}$/.test(p.due_date)) throw new HttpError(400, "Due date looks wrong.");
      const number = must(await db.rpc("next_invoice_number")) as string;
      const inv = must(await db.from("invoices").insert({
        number, client_id: text(p.client_id, "Client"), description: text(p.description, "Description", 300),
        items: clean, subtotal, tax_rate: taxRate, tax, amount, due_date: p.due_date || null,
        notes: text(p.notes, "Notes", 1000, false),
      }).select().single());
      return reply(req, { invoice: inv, link: `${SITE}/pay.html?t=${inv.pay_token}` });
    }
    case "void_invoice": {
      const r = must(await db.from("invoices").update({ status: "void" }).eq("id", p.id).eq("status", "open").select());
      if (!r?.length) throw new HttpError(409, "Only unpaid invoices can be voided.");
      return reply(req, { ok: true });
    }
    case "create_subscription": {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(p.start_date ?? "")) throw new HttpError(400, "Start date is required.");
      if (Number(p.start_date.slice(8, 10)) > 28) throw new HttpError(400, "Pick a start day between 1 and 28, so every month has that date.");
      const amount = int(p.amount, "Monthly amount", 10000);
      const sub = must(await db.from("subscriptions").insert({
        client_id: text(p.client_id, "Client"), plan_name: text(p.plan_name, "Plan name", 120), amount, start_date: p.start_date,
      }).select().single());
      return reply(req, { subscription: sub, link: `${SITE}/pay.html?t=${sub.pay_token}` });
    }
    case "cancel_subscription": {
      const sub = must(await db.from("subscriptions").select("*").eq("id", p.id).single());
      if (sub.status === "cancelled") return reply(req, { ok: true });
      if (sub.recurring_plan_id) await xendit(`/recurring/plans/${encodeURIComponent(sub.recurring_plan_id)}/deactivate`);
      must(await db.from("subscriptions").update({ status: "cancelled" }).eq("id", sub.id));
      return reply(req, { ok: true });
    }
    default:
      throw new HttpError(400, "Unknown action.");
  }
}

// ---------- Xendit: /webhook ----------
async function sha256(s: string) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(h), (b) => b.toString(16).padStart(2, "0")).join("");
}

async function handleWebhook(req: Request) {
  const expected = Deno.env.get("XENDIT_WEBHOOK_TOKEN");
  if (!expected || !safeEqual(req.headers.get("x-callback-token") ?? "", expected)) {
    return new Response("unauthorized", { status: 401 });
  }
  const raw = await req.text();
  let payload: any;
  try { payload = JSON.parse(raw); } catch { return new Response("bad json", { status: 400 }); }
  const event = String(payload.event ?? "");
  const ins = await db.from("webhook_events").insert({ body_hash: await sha256(raw), event, payload })
    .select("id").maybeSingle();
  if (ins.error) {
    if (ins.error.code === "23505") return new Response("duplicate", { status: 200 }); // Xendit retry we already have
    throw new HttpError(500, ins.error.message);
  }
  const id = ins.data!.id;
  try {
    await applyEvent(event, payload.data ?? {});
    await db.from("webhook_events").update({ handled: true }).eq("id", id);
  } catch (e) {
    await db.from("webhook_events").update({ error: String((e as Error).message ?? e) }).eq("id", id);
    throw e; // non-2xx → Xendit retries
  }
  return new Response("ok", { status: 200 });
}

async function applyEvent(event: string, d: any) {
  const now = new Date().toISOString();
  if (event === "payment_session.completed" || event === "payment_session.expired") {
    const s = must(await db.from("pay_sessions").select("*").eq("session_id", d.payment_session_id).maybeSingle());
    if (!s) return; // a session not created by us (e.g. made in the Xendit dashboard)
    must(await db.from("pay_sessions").update({ status: d.status ?? (event.endsWith("completed") ? "COMPLETED" : "EXPIRED") }).eq("session_id", s.session_id));
    if (event.endsWith("expired")) return;
    if (s.kind === "invoice") {
      const inv = must(await db.from("invoices").update({ status: "paid", paid_at: now }).eq("id", s.invoice_id).eq("status", "open").select());
      const row = inv?.[0] ?? must(await db.from("invoices").select("*").eq("id", s.invoice_id).single());
      must(await db.from("payments").insert({
        client_id: row.client_id, invoice_id: row.id, source_event: event,
        xendit_ref: d.payment_id ?? d.payment_request_id ?? s.session_id,
        amount: d.amount ?? row.amount, currency: d.currency ?? "IDR", status: "SUCCEEDED",
      }));
    } else {
      const sub = must(await db.from("subscriptions").select("*").eq("id", s.subscription_id).single());
      must(await db.from("subscriptions").update({
        status: sub.status === "active" ? "active" : "pending",
        recurring_plan_id: d.recurring_plan_id ?? sub.recurring_plan_id,
      }).eq("id", sub.id));
      if (d.customer_id) {
        await db.from("clients").update({ xendit_customer_id: d.customer_id }).eq("id", sub.client_id).is("xendit_customer_id", null);
      }
    }
    return;
  }
  if (event.startsWith("recurring.")) {
    const planId = d.plan_id ?? d.recurring_plan_id ?? (event.startsWith("recurring.plan.") ? d.id : null);
    if (!planId) return;
    const sub = must(await db.from("subscriptions").select("*").eq("recurring_plan_id", planId).maybeSingle());
    if (!sub) return;
    if (event === "recurring.plan.activated") {
      must(await db.from("subscriptions").update({ status: "active", activated_at: sub.activated_at ?? now }).eq("id", sub.id));
    } else if (event === "recurring.plan.inactivated") {
      must(await db.from("subscriptions").update({ status: sub.status === "cancelled" ? "cancelled" : "inactive" }).eq("id", sub.id));
    } else if (event === "recurring.cycle.succeeded" || event === "recurring.cycle.failed") {
      const ok = event.endsWith("succeeded");
      must(await db.from("payments").insert({
        client_id: sub.client_id, subscription_id: sub.id, source_event: event, xendit_ref: d.id ?? null,
        amount: d.amount ?? sub.amount, currency: d.currency ?? "IDR", status: ok ? "SUCCEEDED" : "FAILED",
      }));
      must(await db.from("subscriptions").update(ok ? { status: "active", last_charge_at: now } : { status: "past_due" }).eq("id", sub.id));
    }
  }
}

// ---------- router ----------
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(req) });
  const path = new URL(req.url).pathname.replace(/\/+$/, "");
  try {
    if (path.endsWith("/pay")) return await handlePay(req);
    if (path.endsWith("/admin")) return await handleAdmin(req);
    if (path.endsWith("/webhook")) return await handleWebhook(req);
    throw new HttpError(404, "Not found");
  } catch (e) {
    const status = e instanceof HttpError ? e.status : 500;
    if (status >= 500) console.error(e);
    const message = e instanceof HttpError ? e.message : "Something went wrong. Please try again.";
    return path.endsWith("/webhook") ? new Response(message, { status }) : reply(req, { error: message }, status);
  }
});
