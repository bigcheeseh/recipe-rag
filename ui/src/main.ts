// One page, no framework: read the question, POST /ask, render the contract.
// Types mirror SPEC.md sections 1 and 2; the assignment's minimum contract fields are
// the only ones the page needs, the rest is shown as extra detail.

type Citation = { title: string; url: string };
type Refusal = { reason: string; message: string };
type Usage = { model: string; retriever: string; cost_usd: number; latency_ms: { total: number } };
type Answer = {
  answer: string | null;
  refused: boolean;
  refusal_reason: "out_of_corpus" | "out_of_domain" | "safety" | null;
  refusal: Refusal | null;
  citations: Citation[];
  conflicts: string[];
  usage: Usage;
};
type Option = { id: string; note: string };
type Config = { models: Option[]; retrievers: Option[]; defaults: { model: string; retriever: string } };

const REFUSAL_LABEL: Record<string, string> = {
  out_of_domain: "Not a recipe question",
  out_of_corpus: "The recipes here cannot answer this",
  safety: "Safety question: reported, not judged",
};

function el<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) throw new Error(`missing #${id}`);
  return node as T;
}

const form = el<HTMLFormElement>("ask");
const question = el<HTMLInputElement>("question");
const submit = el<HTMLButtonElement>("submit");
const switches = el<HTMLDivElement>("switches");
const modelSelect = el<HTMLSelectElement>("model");
const modelNote = el<HTMLElement>("model-note");
const retrieverSelect = el<HTMLSelectElement>("retriever");
const retrieverNote = el<HTMLElement>("retriever-note");
const result = el<HTMLElement>("result");
const refusal = el<HTMLParagraphElement>("refusal");
const answer = el<HTMLParagraphElement>("answer");
const conflicts = el<HTMLUListElement>("conflicts");
const citations = el<HTMLUListElement>("citations");
const meta = el<HTMLParagraphElement>("meta");
const error = el<HTMLParagraphElement>("error");

function fill(list: HTMLUListElement, items: string[]): void {
  list.replaceChildren(...items.map((t) => Object.assign(document.createElement("li"), { textContent: t })));
}

// A selector whose options carry the server's note as a tooltip, on the option and
// on the "?" next to it, so the trade-off is one hover away.
function bindSelect(select: HTMLSelectElement, note: HTMLElement, options: Option[], chosen: string): void {
  select.replaceChildren(
    ...options.map((o) => Object.assign(document.createElement("option"), { value: o.id, textContent: o.id, title: o.note })),
  );
  select.value = chosen;
  const sync = (): void => {
    const current = options.find((o) => o.id === select.value);
    note.title = current?.note ?? "";
    select.title = note.title;
  };
  select.addEventListener("change", sync);
  sync();
}

async function loadConfig(): Promise<void> {
  try {
    const r = await fetch("/config");
    if (!r.ok) return; // switches stay hidden; the server defaults apply
    const c = (await r.json()) as Config;
    bindSelect(modelSelect, modelNote, c.models, c.defaults.model);
    bindSelect(retrieverSelect, retrieverNote, c.retrievers, c.defaults.retriever);
    switches.hidden = false;
  } catch {
    // no config, no switches
  }
}

function render(a: Answer, traceId: string | null): void {
  refusal.hidden = !a.refused;
  if (a.refused) {
    const label = REFUSAL_LABEL[a.refusal_reason ?? ""] ?? "Refused";
    refusal.textContent = `${label}. ${a.refusal?.message ?? ""}`;
  }
  answer.textContent = a.answer ?? "";
  fill(conflicts, a.conflicts.map((c) => `Recipes disagree: ${c}`));
  citations.replaceChildren(
    ...a.citations.map((c) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = c.url;
      link.textContent = c.title;
      link.target = "_blank";
      link.rel = "noopener";
      li.append(link);
      return li;
    }),
  );
  if (a.citations.length === 0) fill(citations, ["none"]);
  meta.textContent =
    `${a.usage.model} + ${a.usage.retriever}, ${a.usage.latency_ms.total} ms, USD ${a.usage.cost_usd.toFixed(4)}` +
    (traceId ? `, trace ${traceId}` : "");
  result.hidden = false;
}

async function ask(q: string): Promise<void> {
  submit.disabled = true;
  error.hidden = true;
  result.hidden = true;
  const body: Record<string, string> = { question: q };
  if (!switches.hidden) {
    body.model = modelSelect.value;
    body.retriever = retrieverSelect.value;
  }
  try {
    const r = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const traceId = r.headers.get("X-Trace-Id");
    if (!r.ok) {
      const detail = (await r.json().catch(() => ({}))) as { detail?: unknown };
      const text = typeof detail.detail === "string" ? detail.detail : JSON.stringify(detail.detail ?? r.statusText);
      throw new Error(`${r.status}: ${text}${traceId ? ` (trace ${traceId})` : ""}`);
    }
    render((await r.json()) as Answer, traceId);
  } catch (e) {
    error.textContent = e instanceof Error ? e.message : String(e);
    error.hidden = false;
  } finally {
    submit.disabled = false;
  }
}

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  void ask(question.value);
});

void loadConfig();
