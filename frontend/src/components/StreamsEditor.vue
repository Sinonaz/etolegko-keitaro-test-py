<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

type OfferRow = {
  offer_id: number
  offer_name: string
  share: number
  pinned: boolean
  removed: boolean
}

type StreamRow = {
  keitaro_stream_id: number
  name: string
  stream_type: string
  position: number
  schema: string
  filter_summary: string
  editable: boolean
  dirty: boolean
  offers: OfferRow[]
}

type EditorState = {
  campaign_id: string
  campaign_name: string
  keitaro_campaign_id: number
  keitaro_admin_url: string | null
  streams: StreamRow[]
}

type OfferSuggestion = { id: number; name: string }

const props = defineProps<{ campaignId: string }>()
const emit = defineEmits<{ close: [] }>()

const state = ref<EditorState | null>(null)
const error = ref<string | null>(null)
const busy = ref(false)
const showAll = ref(true)

const offerQuery = ref<Record<number, string>>({})
const suggestions = ref<Record<number, OfferSuggestion[]>>({})
const searchTimers: Record<number, ReturnType<typeof setTimeout> | undefined> = {}

const dirtyStreamIds = computed(() =>
  (state.value?.streams || []).filter((s) => s.dirty).map((s) => s.keitaro_stream_id),
)

onMounted(() => {
  void load()
})

watch(
  () => props.campaignId,
  () => void load(),
)

async function load() {
  error.value = null
  try {
    const res = await fetch(`/api/campaigns/${props.campaignId}/streams`)
    if (!res.ok) throw new Error(await readError(res))
    state.value = (await res.json()) as EditorState
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function run(path: string, init?: RequestInit) {
  busy.value = true
  error.value = null
  try {
    const res = await fetch(`/api/campaigns/${props.campaignId}/streams${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    })
    if (!res.ok) throw new Error(await readError(res))
    state.value = (await res.json()) as EditorState
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

function fetchFromKt() {
  return run('/fetch', { method: 'POST' })
}

function pushStream(streamId: number) {
  return run(`/${streamId}/push`, { method: 'POST' })
}

function cancelStream(streamId: number) {
  return run(`/${streamId}/cancel`, { method: 'POST' })
}

function removeOffer(streamId: number, offerId: number) {
  return run(`/${streamId}/offers/${offerId}/remove`, { method: 'POST' })
}

function bringBack(streamId: number, offerId: number) {
  return run(`/${streamId}/offers/${offerId}/bring-back`, { method: 'POST' })
}

function togglePin(streamId: number, offer: OfferRow) {
  const action = offer.pinned ? 'unpin' : 'pin'
  return run(`/${streamId}/offers/${offer.offer_id}/${action}`, { method: 'POST' })
}

function onOfferInput(streamId: number, value: string) {
  offerQuery.value[streamId] = value
  if (searchTimers[streamId]) clearTimeout(searchTimers[streamId])
  const q = value.trim()
  if (q.length < 1) {
    suggestions.value[streamId] = []
    return
  }
  searchTimers[streamId] = setTimeout(() => void searchOffers(streamId, q), 250)
}

async function searchOffers(streamId: number, q: string) {
  try {
    const res = await fetch(`/api/offers/search?q=${encodeURIComponent(q)}`)
    if (!res.ok) return
    suggestions.value[streamId] = (await res.json()) as OfferSuggestion[]
  } catch {
    suggestions.value[streamId] = []
  }
}

async function addOffer(streamId: number, offerId: number) {
  await run(`/${streamId}/offers`, {
    method: 'POST',
    body: JSON.stringify({ offer_id: offerId }),
  })
  offerQuery.value[streamId] = ''
  suggestions.value[streamId] = []
}

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null)
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message: unknown }).message)
    }
  }
  return `HTTP ${res.status}`
}

function visibleOffers(stream: StreamRow): OfferRow[] {
  if (showAll.value) return stream.offers
  return stream.offers.filter((o) => !o.removed)
}
</script>

<template>
  <section class="editor">
    <header class="bar">
      <div>
        <button type="button" class="link" @click="emit('close')">← Campaigns</button>
        <h2>
          {{ state?.campaign_name || '…' }}
          <span class="muted">/ Keitaro Streams</span>
        </h2>
      </div>
      <div class="actions">
        <button type="button" :disabled="busy" @click="fetchFromKt">
          Fetch streams from KT
        </button>
        <a
          v-if="state?.keitaro_admin_url"
          class="buttonish"
          :href="state.keitaro_admin_url"
          target="_blank"
          rel="noreferrer"
        >
          View in KT
        </a>
        <button type="button" @click="showAll = !showAll">
          {{ showAll ? 'Hide removed' : 'Show all offers' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="!state?.streams.length" class="muted">
      No streams loaded yet — press “Fetch streams from KT”.
    </p>

    <article
      v-for="stream in state?.streams || []"
      :key="stream.keitaro_stream_id"
      class="stream"
    >
      <div class="stream-head">
        <div>
          <strong>
            Stream: {{ stream.name }} (#{{ stream.position || stream.keitaro_stream_id }})
          </strong>
          <span class="muted">
            filter by {{ stream.filter_summary }}, stream_id
            {{ stream.keitaro_stream_id }}
          </span>
        </div>
        <div v-if="stream.editable && stream.dirty" class="actions">
          <button type="button" class="primary" :disabled="busy" @click="pushStream(stream.keitaro_stream_id)">
            Push to KT
          </button>
          <button type="button" :disabled="busy" @click="cancelStream(stream.keitaro_stream_id)">
            Cancel
          </button>
        </div>
      </div>

      <table v-if="stream.editable">
        <thead>
          <tr>
            <th>Offer</th>
            <th>Share</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="offer in visibleOffers(stream)"
            :key="offer.offer_id"
            :class="{ removed: offer.removed }"
          >
            <td>
              {{ offer.offer_name }}
              <span v-if="offer.removed" class="muted">(removed)</span>
            </td>
            <td>
              <button
                type="button"
                class="share"
                :disabled="offer.removed || busy"
                :title="offer.pinned ? 'Unpin' : 'Pin share'"
                @click="togglePin(stream.keitaro_stream_id, offer)"
              >
                {{ offer.share }}%{{ offer.pinned ? ' (pinned)' : '' }}
              </button>
            </td>
            <td>
              <button
                v-if="!offer.removed"
                type="button"
                :disabled="busy"
                @click="removeOffer(stream.keitaro_stream_id, offer.offer_id)"
              >
                Remove
              </button>
              <button
                v-else
                type="button"
                :disabled="busy"
                @click="bringBack(stream.keitaro_stream_id, offer.offer_id)"
              >
                Bring back
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="stream.editable" class="add">
        <input
          :value="offerQuery[stream.keitaro_stream_id] || ''"
          type="text"
          placeholder="Search offer to add"
          @input="onOfferInput(stream.keitaro_stream_id, ($event.target as HTMLInputElement).value)"
        />
        <ul v-if="(suggestions[stream.keitaro_stream_id] || []).length" class="suggest">
          <li
            v-for="s in suggestions[stream.keitaro_stream_id]"
            :key="s.id"
          >
            <button type="button" :disabled="busy" @click="addOffer(stream.keitaro_stream_id, s.id)">
              {{ s.id }} — {{ s.name }}
            </button>
          </li>
        </ul>
      </div>

      <p v-else class="muted">Read-only stream ({{ stream.schema || stream.stream_type }}).</p>
    </article>

    <p v-if="dirtyStreamIds.length" class="muted">
      Unsaved streams: {{ dirtyStreamIds.join(', ') }}
    </p>
  </section>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.bar,
.stream-head,
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: space-between;
}

.bar h2 {
  margin: 0.25rem 0 0;
  font-size: 1.15rem;
}

.stream {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.75rem;
  background: #fafafa;
}

.stream-head {
  margin-bottom: 0.75rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

th,
td {
  border-bottom: 1px solid #eee;
  text-align: left;
  padding: 0.45rem 0.35rem;
  vertical-align: top;
}

tr.removed td {
  color: #888;
  text-decoration: line-through;
}

tr.removed td:last-child {
  text-decoration: none;
}

button,
.buttonish {
  border: 1px solid #ccc;
  background: #fff;
  border-radius: 4px;
  padding: 0.35rem 0.65rem;
  font: inherit;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

button.primary {
  background: #2f6fed;
  border-color: #2f6fed;
  color: #fff;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

button.link {
  border: 0;
  background: transparent;
  padding: 0;
  color: #2f6fed;
}

.share {
  border: 0;
  background: transparent;
  color: #2f6fed;
  font-weight: 700;
  padding: 0;
}

.add {
  margin-top: 0.75rem;
}

.add input {
  width: 100%;
  max-width: 24rem;
  padding: 0.45rem 0.55rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font: inherit;
}

.suggest {
  list-style: none;
  margin: 0.35rem 0 0;
  padding: 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-width: 24rem;
  background: #fff;
}

.suggest button {
  width: 100%;
  text-align: left;
  border: 0;
  border-radius: 0;
}

.muted {
  color: #666;
  font-size: 0.9rem;
}

.err {
  color: #b00020;
}
</style>
