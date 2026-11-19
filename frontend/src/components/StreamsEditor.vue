<script setup lang="ts">
import {
  NAlert,
  NAutoComplete,
  NButton,
  NDataTable,
  NSpace,
  NTag,
  NText,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { formatApiError } from '../utils/errors'

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
  stream_schema: string
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
  (state.value?.streams || [])
    .filter((s) => s.dirty)
    .map((s) => s.keitaro_stream_id),
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

function offerOptions(streamId: number) {
  return (suggestions.value[streamId] || []).map((offer) => ({
    label: `${offer.id} — ${offer.name}`,
    value: String(offer.id),
  }))
}

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null)
  return formatApiError(body) || `HTTP ${res.status}`
}

function visibleOffers(stream: StreamRow): OfferRow[] {
  if (showAll.value) return stream.offers
  return stream.offers.filter((o) => !o.removed)
}

function columnsFor(stream: StreamRow): DataTableColumns<OfferRow> {
  return [
    {
      title: 'Offer',
      key: 'offer_name',
      render(row) {
        return h(
          'div',
          { class: row.removed ? 'removed' : undefined },
          [
            row.offer_name,
            row.removed
              ? h(NText, { depth: 3 }, { default: () => ' (removed)' })
              : null,
          ],
        )
      },
    },
    {
      title: 'Share',
      key: 'share',
      width: 120,
      render(row) {
        return h(
          NButton,
          {
            text: true,
            type: 'primary',
            disabled: row.removed || busy.value,
            onClick: () => togglePin(stream.keitaro_stream_id, row),
          },
          {
            default: () =>
              `${row.share}%${row.pinned ? ' · pinned' : ''}`,
          },
        )
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 140,
      render(row) {
        if (row.removed) {
          return h(
            NButton,
            {
              size: 'small',
              disabled: busy.value,
              onClick: () => bringBack(stream.keitaro_stream_id, row.offer_id),
            },
            { default: () => 'Bring back' },
          )
        }
        return h(
          NButton,
          {
            size: 'small',
            secondary: true,
            type: 'error',
            disabled: busy.value,
            onClick: () => removeOffer(stream.keitaro_stream_id, row.offer_id),
          },
          { default: () => 'Remove' },
        )
      },
    },
  ]
}
</script>

<template>
  <section class="editor panel">
    <header class="bar">
      <div>
        <NButton text type="primary" @click="emit('close')">← Кампании</NButton>
        <h2>
          {{ state?.campaign_name || '…' }}
          <span class="muted">/ Keitaro Streams</span>
        </h2>
      </div>
      <NSpace>
        <NButton :disabled="busy" :loading="busy" @click="fetchFromKt">
          Fetch from KT
        </NButton>
        <NButton
          v-if="state?.keitaro_admin_url"
          tag="a"
          :href="state.keitaro_admin_url"
          target="_blank"
          rel="noreferrer"
          secondary
        >
          View in KT
        </NButton>
        <NButton secondary @click="showAll = !showAll">
          {{ showAll ? 'Hide removed' : 'Show all offers' }}
        </NButton>
      </NSpace>
    </header>

    <NAlert v-if="error" type="error" :bordered="false">{{ error }}</NAlert>
    <NText v-if="!state?.streams.length" depth="3">
      Потоки ещё не загружены — нажми “Fetch from KT”.
    </NText>

    <article
      v-for="stream in state?.streams || []"
      :key="stream.keitaro_stream_id"
      class="stream"
    >
      <div class="stream-head">
        <div>
          <NSpace align="center" :size="8">
            <strong>
              {{ stream.name }}
            </strong>
            <NTag size="small" :bordered="false">
              #{{ stream.position || stream.keitaro_stream_id }}
            </NTag>
            <NTag v-if="stream.dirty" size="small" type="warning" :bordered="false">
              unsaved
            </NTag>
          </NSpace>
          <NText depth="3" class="meta">
            filter {{ stream.filter_summary }} · stream_id {{ stream.keitaro_stream_id }}
          </NText>
        </div>
        <NSpace v-if="stream.editable && stream.dirty">
          <NButton
            type="primary"
            :disabled="busy"
            :loading="busy"
            @click="pushStream(stream.keitaro_stream_id)"
          >
            Push to KT
          </NButton>
          <NButton :disabled="busy" @click="cancelStream(stream.keitaro_stream_id)">
            Cancel
          </NButton>
        </NSpace>
      </div>

      <template v-if="stream.editable">
        <NDataTable
          :columns="columnsFor(stream)"
          :data="visibleOffers(stream)"
          :bordered="false"
          :single-line="false"
          size="small"
        />

        <div class="add">
          <NAutoComplete
            :value="offerQuery[stream.keitaro_stream_id] || ''"
            :options="offerOptions(stream.keitaro_stream_id)"
            placeholder="Добавить оффер…"
            clearable
            @update:value="(v: string) => onOfferInput(stream.keitaro_stream_id, v)"
            @select="(v: string) => addOffer(stream.keitaro_stream_id, Number(v))"
          />
        </div>
      </template>

      <NText v-else depth="3">
        Read-only stream ({{ stream.stream_schema || stream.stream_type }}).
      </NText>
    </article>

    <NText v-if="dirtyStreamIds.length" depth="3">
      Несохранённые потоки: {{ dirtyStreamIds.join(', ') }}
    </NText>
  </section>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.25rem 1.35rem 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 40px rgba(28, 25, 23, 0.05);
}

.editor {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.bar,
.stream-head {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-start;
  justify-content: space-between;
}

.bar h2 {
  margin: 0.2rem 0 0;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
}

.muted {
  color: var(--muted);
  font-weight: 500;
}

.stream {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem;
  background: rgba(255, 255, 255, 0.65);
}

.meta {
  display: block;
  margin-top: 0.25rem;
}

.add {
  margin-top: 0.85rem;
  max-width: 28rem;
}

.removed {
  color: var(--muted);
  text-decoration: line-through;
}
</style>
